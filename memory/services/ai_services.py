# memory/services/ai_services.py (Düzeltilmiş)
from transformers import pipeline
import numpy as np
import logging
import math
import time
import os
import whisper
import warnings
warnings.filterwarnings("ignore")

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import face_recognition
import cv2
import matplotlib.pyplot as plt

from transformers import CLIPProcessor, CLIPModel
from sentence_transformers import SentenceTransformer
from PIL import Image
from torch_geometric.data import Data
from torch_geometric.nn import GCNConv
from skimage.segmentation import slic
from skimage import io
from skimage.segmentation import mark_boundaries

# Quantum Safe Library (Opsiyonel)
try:
    import oqs
except ImportError:
    oqs = None

logger = logging.getLogger(__name__)


# ==================== YARDIMCI FONKSİYONLAR ====================

def create_superpixels(image_path, n_segments=500, compactness=10):
    """Belirtilen görüntü yolu için SLIC algoritması ile superpiksel oluşturur."""
    try:
        image = io.imread(image_path)
        if image.dtype == np.uint8:
            image = image.astype(np.float32) / 255.0
    except FileNotFoundError:
        print(f"HATA: '{image_path}' dosya yolu bulunamadı.")
        return None, None, 0
    except Exception as e:
        print(f"Resim okuma hatası: {e}")
        return None, None, 0

    try:
        labels = slic(
            image,
            n_segments=n_segments,
            compactness=compactness,
            enforce_connectivity=True,
            sigma=0,
            start_label=0
        )
        num_superpixels = len(np.unique(labels))
        return image, labels, num_superpixels
    except Exception as e:
        logger.error(f"SLIC hatası: {e}")
        return None, None, 0


def visualize_superpixels(image, labels):
    """Superpiksel sınırlarını orijinal görüntü üzerinde görselleştirir."""
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    ax.imshow(mark_boundaries(image, labels, color=(1, 1, 1)))
    ax.set_title("Oluşturulan Superpikseller (Düğümler)")
    ax.axis('off')
    plt.show()


def extract_node_features(image_rgb, labels, num_nodes):
    """Her bir superpiksel için ortalama RGB değerlerini hesaplar."""
    height, width, channels = image_rgb.shape
    node_features_np = np.zeros((num_nodes, channels), dtype=np.float32)
    pixel_counts = np.zeros(num_nodes, dtype=np.int32)

    for i in range(height):
        for j in range(width):
            label = labels[i, j]
            if label < num_nodes:
                node_features_np[label] += image_rgb[i, j]
                pixel_counts[label] += 1

    pixel_counts_expanded = pixel_counts[:, np.newaxis]
    node_features_np = np.divide(
        node_features_np,
        pixel_counts_expanded,
        out=node_features_np,
        where=pixel_counts_expanded != 0
    )

    node_features_tensor = torch.tensor(node_features_np, dtype=torch.float)
    y_reco = node_features_tensor.clone()
    return node_features_tensor, y_reco


def create_edge_index(labels):
    """Superpiksel komşuluklarını bulur."""
    height, width = labels.shape
    adj_set = set()
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

    for r in range(height):
        for c in range(width):
            src_label = labels[r, c]
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < height and 0 <= nc < width:
                    dest_label = labels[nr, nc]
                    if src_label != dest_label:
                        adj_set.add((int(src_label), int(dest_label)))
                        adj_set.add((int(dest_label), int(src_label)))

    if not adj_set:
        return torch.zeros((2, 0), dtype=torch.long)

    source_nodes = [edge[0] for edge in adj_set]
    target_nodes = [edge[1] for edge in adj_set]
    edge_index = torch.tensor([source_nodes, target_nodes], dtype=torch.long)
    return edge_index


def calculate_edge_weights(x, edge_index):
    """Kenar ağırlıklarını hesaplar."""
    if edge_index.size(1) == 0:
        return torch.tensor([], dtype=torch.float)

    source_nodes = edge_index[0]
    target_nodes = edge_index[1]
    source_features = x[source_nodes]
    target_features = x[target_nodes]
    diff_features = source_features - target_features
    edge_weights = torch.norm(diff_features, p=2, dim=1)
    return edge_weights


def intelligent_prune_edges(x, edge_index, edge_weights, compression_ratio=0.7):
    """Kenarları kırpar."""
    if edge_weights.numel() == 0:
        return edge_index, edge_weights

    scores = edge_weights.cpu().numpy()
    threshold = np.percentile(scores, (compression_ratio * 100))
    mask = edge_weights >= threshold
    mask_tensor = torch.from_numpy(mask).bool() if isinstance(mask, np.ndarray) else mask
    pruned_edge_index = edge_index[:, mask_tensor]
    pruned_edge_weights = edge_weights[mask_tensor]
    return pruned_edge_index, pruned_edge_weights


def add_gaussian_noise(g, clip_norm, epsilon, delta):
    """Gradyanlara gürültü ekler."""
    sigma = (clip_norm * math.sqrt(2 * math.log(1 / delta))) / epsilon
    noise = torch.randn_like(g) * sigma
    return g + noise


# ==================== MODELLER ====================

class LightweightTransformerEncoder(nn.Module):
    def __init__(self, embed_dim, num_heads, dropout=0.1):
        super().__init__()
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim,
            nhead=num_heads,
            dim_feedforward=embed_dim * 4,
            dropout=dropout,
            batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=1)

    def forward(self, x):
        x = x.unsqueeze(0)
        x_global = self.transformer_encoder(x)
        x_global = x_global.squeeze(0)
        return x_global


class SemanticDecoder(nn.Module):
    def __init__(self, in_features, out_channels=3):
        super().__init__()
        self.fc1 = nn.Linear(in_features, in_features * 2)
        self.fc2 = nn.Linear(in_features * 2, out_channels)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        return torch.sigmoid(self.fc2(x))


class HybridGNNTransformer(nn.Module):
    def __init__(self, in_channels, hidden_channels, num_classes, num_heads=4):
        super().__init__()
        self.gcn1 = GCNConv(in_channels, hidden_channels)
        self.gcn2 = GCNConv(hidden_channels, hidden_channels)
        self.transformer = LightweightTransformerEncoder(embed_dim=hidden_channels, num_heads=num_heads)
        self.classifier = nn.Linear(hidden_channels, num_classes)
        self.decoder = SemanticDecoder(hidden_channels, out_channels=3)

    def forward(self, data):
        x, edge_index, edge_attr = data.x, data.edge_index, data.edge_attr
        x_local = F.relu(self.gcn1(x, edge_index, edge_attr))
        x_local = F.dropout(x_local, p=0.5, training=self.training)
        x_local = self.gcn2(x_local, edge_index, edge_attr)
        x_global = self.transformer(x_local)
        x_final = x_local + x_global
        out_cls = F.log_softmax(self.classifier(x_final), dim=1)
        out_reco = self.decoder(x_final)
        return out_cls, out_reco


# ==================== GÜVENLİK SINIFLAR ====================

class DifferentialPrivacy:
    def __init__(self, epsilon=1.0, delta=1e-5):
        self.epsilon = epsilon
        self.delta = delta

    def add_noise(self, tensor):
        sigma = math.sqrt(2 * math.log(1.25 / self.delta)) / self.epsilon
        noise = torch.randn_like(tensor) * sigma
        return tensor + noise


class LatticeCrypto:
    def __init__(self, dimension=512):
        self.dimension = dimension
        if oqs:
            try:
                self.kem = oqs.KeyEncapsulation("Kyber512")
                self.public_key = self.kem.generate_keypair()
                self.simulation_mode = False
            except Exception as e:
                logger.warning(f"OQS başlatılamadı: {e}. Simülasyon moduna geçiliyor.")
                self.simulation_mode = True
        else:
            logger.warning("OQS kütüphanesi yok. Simülasyon moduna geçiliyor.")
            self.simulation_mode = True

    def encrypt(self, data):
        if self.simulation_mode:
            return {"simulated": True, "data": data}
        ciphertext, shared_secret = self.kem.encap_secret(self.public_key)
        return {"ciphertext": ciphertext, "public_key": self.public_key}


class QuantumResistantEncoder:
    def __init__(self):
        self.lattice_crypto = LatticeCrypto(dimension=512)

    def encrypt_semantic_features(self, features):
        return self.lattice_crypto.encrypt(features)


class WiFiDependentSecurity:
    def __init__(self):
        self.trusted_networks = ["Home_WiFi", "Office_Network"]

    def verify_wifi_and_decrypt(self, encrypted_data, current_wifi):
        if current_wifi in self.trusted_networks:
            return self.decrypt(encrypted_data)
        else:
            self.self_destruct()
            return None

    def decrypt(self, encrypted_data):
        return encrypted_data.get("data") if encrypted_data.get("simulated") else None

    def self_destruct(self):
        print("🚨 GÜVENLİK: WiFi doğrulama başarısız - self-destruct!")


class SelfDestructProtocol:
    def __init__(self, max_duration=3600):
        self.creation_time = time.time()
        self.max_duration = max_duration

    def check_and_destroy(self):
        if time.time() - self.creation_time > self.max_duration:
            self.secure_erase()

    def secure_erase(self):
        print("Secure erase initiated...")


class AdvancedSecurityModule:
    def __init__(self):
        self.quantum_crypto = LatticeCrypto()
        self.differential_privacy = DifferentialPrivacy()
        self.self_destruct = SelfDestructProtocol()
        self.wifi_validator = WiFiDependentSecurity()

    def secure_processing_pipeline(self, image_data):
        return image_data


# ==================== EĞİTİM FONKSİYONU ====================

def train_gcn_with_dp(model, data, optimizer, num_epochs, dp_enabled=False, clip_norm=1.0, epsilon=1.0, delta=1e-5, lambda_reco=0.5):
    """Differential Privacy (DP) ile güçlendirilmiş eğitim döngüsü."""
    classification_criterion = F.nll_loss
    reconstruction_criterion = nn.MSELoss()

    model.train()
    for epoch in range(num_epochs):
        optimizer.zero_grad()
        out_cls, out_reco = model(data)

        if data.y is not None and data.y.max() < out_cls.size(1):
            cls_loss = classification_criterion(out_cls, data.y)
        else:
            cls_loss = 0.0

        reco_loss = reconstruction_criterion(out_reco, data.y_reco)
        total_loss = cls_loss + lambda_reco * reco_loss
        total_loss.backward()

        if dp_enabled:
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=clip_norm)
            for param in model.parameters():
                if param.grad is not None:
                    param.grad.data = add_gaussian_noise(
                        param.grad.data,
                        clip_norm=clip_norm,
                        epsilon=epsilon,
                        delta=delta
                    )

        optimizer.step()

    return model


# ==================== ANA AI SERVICE SINIFI ====================

class AIService:
    """Tüm ML/AI modellerini yöneten servis. Modelleri Lazy Loading ile yükler."""
    
    SENTENCE_MODEL_NAME = 'all-MiniLM-L6-v2'
    CLIP_MODEL_NAME = 'openai/clip-vit-base-patch32'

    def __init__(self):
        self._text_model = None
        self._clip_processor = None
        self._clip_model = None
        self._whisper_model = None
        self._semantic_model = None
        self._qa_pipeline = None  # ← DÜZELTME: QA pipeline için değişken eklendi
        self.embedding_dimension = 384
        self.clip_dimension = 512
        self.use_fallback = False

    def _load_text_model(self):
        """Sentence Transformer modelini yalnızca ilk çağrıda yükler."""
        if self._text_model is None:
            try:
                self._text_model = SentenceTransformer(self.SENTENCE_MODEL_NAME)
                logger.info(f"{self.SENTENCE_MODEL_NAME} başarıyla yüklendi.")
            except Exception as e:
                logger.error(f"TEXT MODEL YÜKLEME HATASI: {e}")
                self._text_model = None
                self.use_fallback = True

    def _load_clip_model(self):
        """CLIP modelini yalnızca ilk çağrıda yükler."""
        if self._clip_model is None:
            try:
                self._clip_processor = CLIPProcessor.from_pretrained(self.CLIP_MODEL_NAME)
                self._clip_model = CLIPModel.from_pretrained(self.CLIP_MODEL_NAME)
                logger.info(f"CLIP modeli başarıyla yüklendi.")
            except Exception as e:
                logger.error(f"CLIP MODEL YÜKLEME HATASI: {e}")
                self._clip_model = None

    def _load_semantic_model(self):
        """Semantic GNN/Transformer modelini yükler."""
        if self._semantic_model is None:
            try:
                IN_CHANNELS = 3
                HIDDEN_CHANNELS = 128
                NUM_CLASSES = 10
                self._semantic_model = HybridGNNTransformer(
                    in_channels=IN_CHANNELS,
                    hidden_channels=HIDDEN_CHANNELS,
                    num_classes=NUM_CLASSES
                )
                self._semantic_model.eval()
                logger.info("Semantic GNN/Transformer modeli başarıyla yüklendi.")
            except Exception as e:
                logger.error(f"Semantic model init error: {e}")
                self._semantic_model = None

    def _load_qa_model(self):
        """Soru-Cevap modelini lazy-load ile yükler (offline destekli)."""
        if self._qa_pipeline is None:
            try:
                print("🧠 QA (Soru-Cevap) Modeli yükleniyor...")
            
                # ÖNCE offline modda deneyelim
                model_path = "models/xlm-roberta-base-squad2"
                local_model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), model_path)
            
                if os.path.exists(local_model_path):
                    # Yerel model dosyasını kullan
                    print(f"   ✅ Offline model bulundu: {local_model_path}")
                    self._qa_pipeline = pipeline(
                        "question-answering", 
                        model=local_model_path,
                        tokenizer=local_model_path
                    )
                else:
                    # Online modeli indir
                    print("   🌐 Online model indiriliyor... (internet bağlantısı gerekiyor)")
                    self._qa_pipeline = pipeline(
                        "question-answering", 
                        model="deepset/xlm-roberta-base-squad2", 
                        tokenizer="deepset/xlm-roberta-base-squad2"
                    )
                
                    # Modeli yerel olarak kaydet
                    os.makedirs(local_model_path, exist_ok=True)
                    self._qa_pipeline.save_pretrained(local_model_path)
                    print(f"   💾 Model kaydedildi: {local_model_path}")
                
                logger.info("QA modeli başarıyla yüklendi.")
            
            except Exception as e:
                logger.error(f"QA model hatası: {e}")
                print(f"   ⚠️ QA modeli yüklenemedi. Soru-cevap özelliği devre dışı.")
                self._qa_pipeline = None

    # ==================== EMBEDDING METODları ====================

    def get_text_embedding(self, text: str) -> np.ndarray | None:
        """Metin verisinden vektör embedding'i oluşturur."""
        if not text:
            return None

        self._load_text_model()

        if self._text_model:
            try:
                embedding = self._text_model.encode(text)
                return embedding.astype(np.float32)
            except Exception as e:
                logger.error(f"Metin embedding hatası: {e}")
                return self._fallback_text_embedding(text)
        else:
            return self._fallback_text_embedding(text)

    def _fallback_text_embedding(self, text: str) -> np.ndarray | None:
        """Basit bir yedek embedding."""
        logger.warning("Yedek (Fallback) metin embedding kullanılıyor.")
        if self.use_fallback:
            np.random.seed(len(text.split()))
            return np.random.rand(self.embedding_dimension).astype(np.float32)
        return None

    def get_image_embedding(self, image_path: str) -> np.ndarray | None:
        """Görüntü dosyasından vektör embedding'i oluşturur (CLIP ile)."""
        if not os.path.exists(image_path):
            logger.warning(f"Görüntü dosyası bulunamadı: {image_path}")
            return None

        self._load_clip_model()

        if self._clip_model and self._clip_processor:
            try:
                image = Image.open(image_path)
                inputs = self._clip_processor(images=image, return_tensors="pt", padding=True)
                with torch.no_grad():
                    image_features = self._clip_model.get_image_features(**inputs)
                embedding = image_features.squeeze().cpu().numpy()
                return embedding.astype(np.float32)
            except Exception as e:
                logger.error(f"Görüntü embedding hatası: {e}")
                return None
        return None

    def get_clip_text_embedding(self, text: str) -> np.ndarray | None:
        """Metni CLIP modeli ile vektöre dönüştürür (Resim aramak için)."""
        if not text:
            return None

        self._load_clip_model()

        if self._clip_model and self._clip_processor:
            try:
                inputs = self._clip_processor(text=[text], return_tensors="pt", padding=True)
                with torch.no_grad():
                    text_features = self._clip_model.get_text_features(**inputs)
                embedding = text_features.squeeze().cpu().numpy()
                return embedding.astype(np.float32)
            except Exception as e:
                logger.error(f"CLIP Text embedding hatası: {e}")
                return None
        return None

    # ==================== VİDEO ANALİZİ ====================

    def analyze_video_content(self, video_path: str, interval_seconds: int = 5):
        """Videoyu kare kare tarar ve embedding'leri çıkarır."""
        if not os.path.exists(video_path):
            print(f"❌ Video bulunamadı: {video_path}")
            return []

        self._load_clip_model()
        if not self._clip_model:
            print("❌ CLIP Modeli yüklenemediği için video işlenemiyor.")
            return []

        print(f"🎥 Video analizi başlıyor: {os.path.basename(video_path)} (Her {interval_seconds}sn'de bir)")

        frames_data = []
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            print(f"❌ Video açılamadı: {video_path}")
            return []

        fps = cap.get(cv2.CAP_PROP_FPS)
        if not fps or fps <= 0:
            print("⚠️ Video FPS okunamadı, varsayılan 30 kabul ediliyor.")
            fps = 30.0

        frame_interval = int(fps * interval_seconds)
        current_frame = 0
        processed_count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if current_frame % frame_interval == 0:
                try:
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(rgb_frame)
                    inputs = self._clip_processor(images=pil_image, return_tensors="pt", padding=True)
                    with torch.no_grad():
                        features = self._clip_model.get_image_features(**inputs)

                    vector = features.squeeze().cpu().numpy().astype(np.float32)
                    timestamp = current_frame / fps

                    frames_data.append({
                        'timestamp': round(timestamp, 2),
                        'embedding': vector
                    })
                    processed_count += 1
                    print(f"   📸 Kare Yakalandı: {timestamp:.1f}sn")

                except Exception as e:
                    logger.error(f"Kare işleme hatası: {e}")

            current_frame += 1

        cap.release()
        print(f"✅ Video analizi bitti. Toplam {len(frames_data)} kare hafızaya alındı.")
        return frames_data


    def _load_whisper_model(self):
        """Whisper modelini lazy-load ile yükler."""
        if not hasattr(self, '_whisper_model') or self._whisper_model is None:
            try:
                print("🎧 Whisper (Ses Modeli) yükleniyor... (Bu biraz zaman alabilir)")
                # 'base' modeli hızlıdır, 'small' veya 'medium' daha hassastır.
                # Türkçe için 'base' yeterli, cpu dostudur.
                self._whisper_model = whisper.load_model("base") 
                logger.info("Whisper modeli başarıyla yüklendi.")
            except Exception as e:
                logger.error(f"Whisper yükleme hatası: {e}")
                self._whisper_model = None

    def transcribe_audio(self, file_path: str) -> str:
        """Video veya Ses dosyasındaki konuşmaları yazıya döker."""
        if not os.path.exists(file_path): return ""
        
        self._load_whisper_model()
        if not self._whisper_model: return ""

        try:
            print(f"🎤 Ses Analizi Başlıyor: {os.path.basename(file_path)}")
            
            # AYARLAR GÜNCELLENDİ: Halüsinasyonu önlemek için parametreler eklendi
            result = self._whisper_model.transcribe(
                file_path, 
                fp16=False,
                condition_on_previous_text=False, # Tekrarı önler
                no_speech_threshold=0.6,          # Sessizliği algıla
                logprob_threshold=-1.0            # Düşük olasılıklı (saçma) metinleri at
            )
            
            text = result['text'].strip()
            
            # Temizlik: Eğer metin çok kısaysa veya sadece sembollerden oluşuyorsa yut.
            if len(text) < 5 or text in ["You", "Thank you.", "MBC News", "Music"]: 
                print("   🔇 Gürültü/Müzik filtrelendi.")
                return ""

            if text:
                print(f"   🗣️ Konuşma: \"{text[:50]}...\"")
                return text
            else:
                return ""
                
        except Exception as e:
            logger.error(f"Transkripsiyon hatası: {e}")
            return ""

    # ==================== GRAFİK DÖNÜŞÜM VE SIKLAŞTIRMA ====================

    def image_to_graph_data(self, image_path: str):
        """Görüntüyü süperpiksel tabanlı PyG Data nesnesine dönüştürür."""
        self._load_semantic_model()
        if not self._semantic_model:
            return None, None

        image, labels, num_nodes = create_superpixels(image_path, n_segments=300)
        if image is None:
            return None, None

        x, y_reco = extract_node_features(image, labels, num_nodes)
        edge_index = create_edge_index(labels)
        edge_weights = calculate_edge_weights(x, edge_index)
        pruned_edge_index, pruned_edge_weights = intelligent_prune_edges(
            x, edge_index, edge_weights, compression_ratio=0.5
        )

        graph_data = Data(
            x=x,
            edge_index=pruned_edge_index,
            edge_attr=pruned_edge_weights,
            y=torch.zeros(num_nodes, dtype=torch.long),
            y_reco=y_reco
        )
        return graph_data, labels

    def compress_graph_features(self, graph_data: Data) -> torch.Tensor:
        """Grafik verisini GNN/Transformer ile işler ve sıkıştırılmış özellikleri döndürür."""
        if not self._semantic_model:
            raise Exception("Semantic model yüklenemedi.")

        with torch.no_grad():
            x, edge_index, edge_attr = graph_data.x, graph_data.edge_index, graph_data.edge_attr
            x_local = F.relu(self._semantic_model.gcn1(x, edge_index, edge_attr))
            x_local = self._semantic_model.gcn2(x_local, edge_index, edge_attr)
            x_global = self._semantic_model.transformer(x_local)
            x_final = x_local + x_global
            return x_final

    def decompress_graph_features(self, compressed_features: torch.Tensor) -> torch.Tensor:
        """Sıkıştırılmış özellikleri alıp Decoder ile renkleri geri tahmin eder."""
        if not self._semantic_model:
            raise Exception("Semantic model yüklenemedi.")

        with torch.no_grad():
            out_reco = self._semantic_model.decoder(compressed_features)
            return out_reco

    # ==================== EĞİTİM ====================

    def train_semantic_model(self, graph_data_list, num_epochs=100, is_dp_enabled=True, epsilon=1.0):
        """Semantic modeli eğitir."""
        self._load_semantic_model()
        if not self._semantic_model:
            return

        optimizer = optim.Adam(self._semantic_model.parameters(), lr=0.001)

        if not graph_data_list:
            return
        data = graph_data_list[0]

        trained_model = train_gcn_with_dp(
            model=self._semantic_model,
            data=data,
            optimizer=optimizer,
            num_epochs=num_epochs,
            dp_enabled=is_dp_enabled,
            epsilon=epsilon
        )
        logger.info(f"Semantik model eğitildi.")
        return trained_model

    # ==================== DOSYADAN METİN ÇIKARMA ====================

    def extract_text_from_file(self, file_path: str) -> str:
        """Verilen dosya yolundan metin içeriğini okur (PDF, DOCX, TXT)."""
        if not os.path.exists(file_path):
            return ""

        ext = os.path.splitext(file_path)[1].lower()
        text_content = ""

        try:
            # Metin Dosyaları
            if ext in ['.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', '.csv', '.log']:
                encodings = ['utf-8', 'cp1254', 'latin-1', 'cp1252']
                for enc in encodings:
                    try:
                        with open(file_path, 'r', encoding=enc) as f:
                            text_content = f.read()
                        if text_content:
                            break
                    except UnicodeDecodeError:
                        continue

            # PDF Dosyaları
            elif ext == '.pdf':
                from pypdf import PdfReader
                reader = PdfReader(file_path)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text_content += extracted + "\n"

            # Word Dosyaları
            elif ext in ['.docx', '.doc']:
                import docx
                doc = docx.Document(file_path)
                for para in doc.paragraphs:
                    text_content += para.text + "\n"

        except Exception as e:
            logger.error(f"Metin okuma hatası ({file_path}): {e}")
            return ""

        if len(text_content) > 0:
            print(f"   📄 Metin Okundu ({len(text_content)} karakter): {text_content[:30]}...")
        else:
            print(f"   ⚠️ Metin Okunamadı veya Boş: {file_path}")

        return text_content[:3000]  # İlk 3000 karakter

    # ==================== SORU-CEVAP METODU ====================

    def answer_question(self, context: str, question: str) -> dict:
        """Verilen metin (context) içerisinden, sorunun (question) cevabını bulur."""
        if not context or not question: return None
        
        self._load_qa_model()
        if not self._qa_pipeline: return None

        try:
            # Modelin işleyebileceği uzunluğa kırp (Token limiti)
            # Context çok uzunsa sadece en alakalı kısımları almak gerekir ama şimdilik başını alalım.
            prepared_context = context[:2000] 
            
            result = self._qa_pipeline(question=question, context=prepared_context)
            
            # Eğer skor çok düşükse (Emin değilse) cevap verme
            if result['score'] < 0.1: 
                return None
                
            return result # {'score': 0.9, 'start': 10, 'end': 20, 'answer': 'Fenerbahçe'}
            
        except Exception as e:
            logger.error(f"Soru cevaplama hatası: {e}")
            return None


        def detect_and_encode_faces(self, image_path: str):
            """
            Resimdeki yüzleri bulur ve 128 boyutlu vektörlerini çıkarır.
            Dönüş: [{'encoding': np.array, 'location': (top, right, bottom, left)}, ...]
            """
            if not os.path.exists(image_path): return []

        try:
            # Resmi yükle
            image = face_recognition.load_image_file(image_path)
            
            # Yüzleri bul (HOG metodu hızlıdır, CNN daha iyidir ama GPU ister)
            # Büyük resimlerde işlem hızlansın diye resmi küçültebiliriz ama şimdilik tam boyut.
            face_locations = face_recognition.face_locations(image)
            
            if not face_locations:
                return []

            print(f"   👤 {len(face_locations)} Yüz Tespit Edildi.")
            
            # Yüzlerin haritasını (encoding) çıkar
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            results = []
            for face_encoding, face_location in zip(face_encodings, face_locations):
                results.append({
                    'encoding': face_encoding, # numpy array
                    'location': face_location  # (top, right, bottom, left)
                })
            
            return results

        except Exception as e:
            logger.error(f"Yüz tanıma hatası: {e}")
            return []