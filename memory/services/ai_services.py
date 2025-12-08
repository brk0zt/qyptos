# memory/services/ai_services.py (Final Fix)
import numpy as np
import logging
import math
import time
import os
os.environ["HF_HUB_OFFLINE"] = "1" 
os.environ["TRANSFORMERS_OFFLINE"] = "1"
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
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

# Quantum Safe Library (Opsiyonel - Yüklü değilse simülasyon çalışır)
try:
    import oqs
except ImportError:
    oqs = None

logger = logging.getLogger(__name__)

# --- YARDIMCI FONKSİYONLAR (Class Dışında) ---

def create_superpixels(image_path, n_segments=500, compactness=10):
    """Belirtilen goruntu yolu icin SLIC algoritmasi ile superpiksel olusturur."""
    try:
        image = io.imread(image_path)
        # Görüntünün float türüne dönüştürülmesi (0-255 -> 0.0-1.0 aralığı için gereklidir)
        if image.dtype == np.uint8:
             image = image.astype(np.float32) / 255.0
    except FileNotFoundError:
        print(f"HATA: '{image_path}' dosya yolu bulunamadi.")
        return None, None, 0
    except Exception as e:
        print(f"Resim okuma hatasi: {e}")
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
        # print(f"Basarili: {num_superpixels} adet superpiksel (dugum) olusturuldu.")
        return image, labels, num_superpixels
    except Exception as e:
        logger.error(f"SLIC hatasi: {e}")
        return None, None, 0

def visualize_superpixels(image, labels):
    """Superpiksel sinirlarini orijinal goruntu uzerinde gorsellestirir."""
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    ax.imshow(mark_boundaries(image, labels, color=(1, 1, 1))) 
    ax.set_title("Olusturulan Superpikseller (Dugumler)")
    ax.axis('off')
    plt.show()

def extract_node_features(image_rgb, labels, num_nodes):
    """Her bir superpiksel icin ortalama RGB degerlerini hesaplar."""
    height, width, channels = image_rgb.shape
    
    node_features_np = np.zeros((num_nodes, channels), dtype=np.float32)
    pixel_counts = np.zeros(num_nodes, dtype=np.int32)

    for i in range(height):
        for j in range(width):
            label = labels[i, j]
            # Label sınırlar dışındaysa atla (güvenlik için)
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
    """Superpiksel komsuluklarini bulur."""
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
    """Kenar agirliklarini hesaplar."""
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
    """Kenarlari kirpar."""
    if edge_weights.numel() == 0:
        return edge_index, edge_weights

    scores = edge_weights.cpu().numpy()
    threshold = np.percentile(scores, (compression_ratio * 100))
    mask = edge_weights >= threshold

    # Tensör maskeleme işlemi için PyTorch tensörüne çeviriyoruz (gerekirse)
    # Burada edge_weights zaten tensör.
    mask_tensor = torch.from_numpy(mask).bool() if isinstance(mask, np.ndarray) else mask
    
    pruned_edge_index = edge_index[:, mask_tensor]
    pruned_edge_weights = edge_weights[mask_tensor]
    
    return pruned_edge_index, pruned_edge_weights

def add_gaussian_noise(g, clip_norm, epsilon, delta):
    """Gradyanlara gurultu ekler."""
    sigma = (clip_norm * math.sqrt(2 * math.log(1 / delta))) / epsilon
    noise = torch.randn_like(g) * sigma
    return g + noise

# --- MODELLER VE SINIFLAR ---

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
        # OQS yüklü ise kullan, değilse simülasyon
        if oqs:
            try:
                self.kem = oqs.KeyEncapsulation("Kyber512")
                self.public_key = self.kem.generate_keypair()
                self.simulation_mode = False
            except Exception as e:
                logger.warning(f"OQS baslatilamadi: {e}. Simulasyon moduna geciliyor.")
                self.simulation_mode = True
        else:
            logger.warning("OQS kutuphanesi yok. Simulasyon moduna geciliyor.")
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
        print("🚨 GÜVENLİK: WiFi dogrulama basarisiz - self-destruct!")

class SelfDestructProtocol:
    def __init__(self, max_duration=3600):
        self.creation_time = time.time()
        self.max_duration = max_duration
    
    def check_and_destroy(self):
        if time.time() - self.creation_time > self.max_duration:
            self.secure_erase()
    
    def secure_erase(self):
        # 10-pass overwrite ile güvenli silme simülasyonu
        print("Secure erase initiated...")

class AdvancedSecurityModule:
    def __init__(self):
        self.quantum_crypto = LatticeCrypto()
        self.differential_privacy = DifferentialPrivacy()
        self.self_destruct = SelfDestructProtocol()
        self.wifi_validator = WiFiDependentSecurity()
    
    def secure_processing_pipeline(self, image_data):
        # Örnek pipeline
        return image_data

# --- EĞİTİM FONKSİYONU (Global Scope) ---
def train_gcn_with_dp(model, data, optimizer, num_epochs, dp_enabled=False, clip_norm=1.0, epsilon=1.0, delta=1e-5, lambda_reco=0.5):
    """
    Differential Privacy (DP) ile guclendirilmis egitim dongusu.
    """
    classification_criterion = F.nll_loss
    reconstruction_criterion = nn.MSELoss()
    
    model.train()
    for epoch in range(num_epochs):
        optimizer.zero_grad()
        out_cls, out_reco = model(data)
        
        # Etiket (y) yoksa sadece reconstruction loss kullan
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

# --- ANA AI SERVICE SINIFI ---

class AIService:
    """
    Tüm ML/AI modellerini yöneten servis.
    Modelleri Lazy Loading ile yükler.
    """
    SENTENCE_MODEL_NAME = 'all-MiniLM-L6-v2' 
    CLIP_MODEL_NAME = 'openai/clip-vit-base-patch32'

    def __init__(self):
        self._text_model = None
        self._clip_processor = None
        self._clip_model = None
        self._semantic_model = None
        self.embedding_dimension = 384
        self.clip_dimension = 512
        self.use_fallback = False

    def _load_text_model(self):
        if self._text_model is None:
            try:
                self._text_model = SentenceTransformer(self.SENTENCE_MODEL_NAME)
            except Exception as e:
                logger.error(f"TEXT MODEL ERROR: {e}")
                self._text_model = None
                self.use_fallback = True
    
    def _load_clip_model(self):
        if self._clip_model is None:
            try:
                self._clip_processor = CLIPProcessor.from_pretrained(self.CLIP_MODEL_NAME)
                self._clip_model = CLIPModel.from_pretrained(self.CLIP_MODEL_NAME)
            except Exception as e:
                logger.error(f"CLIP MODEL ERROR: {e}")
                self._clip_model = None

    def _load_semantic_model(self):
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
            except Exception as e:
                logger.error(f"Semantic Model Init Error: {e}")
                self._semantic_model = None

    # --- 1. Metin Embedding ---
    def get_text_embedding(self, text: str) -> np.ndarray | None:
        if not text: return None
        self._load_text_model()

        if self._text_model:
            try:
                embedding = self._text_model.encode(text)
                return embedding.astype(np.float32) 
            except Exception as e:
                logger.error(f"Embed error: {e}")
        return self._fallback_text_embedding(text)

    def _fallback_text_embedding(self, text: str) -> np.ndarray | None:
        if self.use_fallback:
             np.random.seed(len(text.split())) 
             return np.random.rand(self.embedding_dimension).astype(np.float32)
        return None

    # --- 2. Görüntü Embedding (CLIP IMAGE) ---
    def get_image_embedding(self, image_path: str) -> np.ndarray | None:
        if not os.path.exists(image_path):
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
                logger.error(f"Image embed error: {e}")
        return None

    # --- 3. Metin Embedding (CLIP TEXT) - Resim Aramak İçin ---
    def get_clip_text_embedding(self, text: str) -> np.ndarray | None:
        """Metni CLIP modeli ile 512 boyutlu vektöre dönüştürür."""
        if not text: return None
        self._load_clip_model()
        
        if self._clip_model and self._clip_processor:
            try:
                inputs = self._clip_processor(text=[text], return_tensors="pt", padding=True)
                with torch.no_grad():
                    text_features = self._clip_model.get_text_features(**inputs)
                embedding = text_features.squeeze().cpu().numpy()
                return embedding.astype(np.float32)
            except Exception as e:
                logger.error(f"CLIP Text embed error: {e}")
                return None
        return None

    def analyze_video_content(self, video_path: str, interval_seconds: int = 5):
        """
        Videoyu kare kare tarar ve embedding'leri çıkarır.
        Dönüş: [{'timestamp': 10.5, 'embedding': vector}, ...]
        """
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
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        if not fps or fps <= 0:
            print("⚠️ Video FPS okunamadı, varsayılan 30 kabul ediliyor.")
            fps = 30.0

        frame_interval = int(fps * interval_seconds)
        current_frame = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Belirlenen aralıkta bir kare yakala
            if current_frame % frame_interval == 0:
                try:
                    # OpenCV (BGR) -> PIL (RGB) Dönüşümü
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(rgb_frame)
                    
                    # Embedding Çıkar
                    inputs = self._clip_processor(images=pil_image, return_tensors="pt", padding=True)
                    with torch.no_grad():
                        features = self._clip_model.get_image_features(**inputs)
                    
                    vector = features.squeeze().cpu().numpy().astype(np.float32)
                    timestamp = current_frame / fps
                    
                    frames_data.append({
                        'timestamp': round(timestamp, 2), # Saniye cinsinden zaman
                        'embedding': vector
                    })
                    print(f"   📸 Kare Yakalandı: {timestamp:.1f}sn")
                    
                except Exception as e:
                    logger.error(f"Kare işleme hatası: {e}")

            current_frame += 1
        
        cap.release()
        print(f"✅ Video analizi bitti. Toplam {len(frames_data)} kare hafızaya alındı.")
        return frames_data

    # --- 4. Görüntüyü Grafik Verisine Dönüştürme ---
    def image_to_graph_data(self, image_path: str):
        self._load_semantic_model()
        if not self._semantic_model:
            return None, None

        image, labels, num_nodes = create_superpixels(image_path, n_segments=300)

        if image is None: return None, None
        
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

    # --- 5. Sıkıştırma (Encoding) ---
    def compress_graph_features(self, graph_data: Data) -> torch.Tensor:
        if not self._semantic_model:
            raise Exception("Semantic model yüklenemedi.")
        
        with torch.no_grad():
            x, edge_index, edge_attr = graph_data.x, graph_data.edge_index, graph_data.edge_attr
            x_local = F.relu(self._semantic_model.gcn1(x, edge_index, edge_attr))
            x_local = self._semantic_model.gcn2(x_local, edge_index, edge_attr)
            x_global = self._semantic_model.transformer(x_local)
            x_final = x_local + x_global 
            return x_final

    # --- 6. Geri Oluşturma (Decoding) ---
    def decompress_graph_features(self, compressed_features: torch.Tensor) -> torch.Tensor:
        if not self._semantic_model:
            raise Exception("Semantic model yüklenemedi.")
            
        with torch.no_grad():
            out_reco = self._semantic_model.decoder(compressed_features)
            return out_reco
            
    # --- 7. Eğitim Metodu ---
    def train_semantic_model(self, graph_data_list, num_epochs=100, is_dp_enabled=True, epsilon=1.0):
        self._load_semantic_model()
        if not self._semantic_model:
            return

        optimizer = optim.Adam(self._semantic_model.parameters(), lr=0.001)
        
        # Basitlik için sadece ilk datayı alıyoruz (Batchleme yapılabilir)
        if not graph_data_list: return
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
    
    # Model konfigürasyonu
    SENTENCE_MODEL_NAME = 'all-MiniLM-L6-v2' # Hızlı ve verimli bir model
    CLIP_MODEL_NAME = 'openai/clip-vit-base-patch32' # Metin ve Görüntü için popüler model

    def __init__(self):
        # Lazy Loading için modelleri başlangıçta None olarak ayarla
        self._text_model = None
        self._clip_processor = None
        self._clip_model = None
        # Vektör boyutunu cache'le
        self.embedding_dimension = 384 # all-MiniLM-L6-v2 boyutu
        self.clip_dimension = 512 # CLIP boyutu
        
        # Basit yedek (fallback) yapı
        self.use_fallback = False

    def _load_text_model(self):
        """Sentence Transformer modelini yalnızca ilk çağrıda yükler."""
        if self._text_model is None:
            try:
                # Modeli yüklemeyi dene
                self._text_model = SentenceTransformer(self.SENTENCE_MODEL_NAME)
                logger.info(f"{self.SENTENCE_MODEL_NAME} başarıyla yüklendi.")
            except Exception as e:
                logger.error(f"TEXT MODEL YÜKLEME HATASI. Yedek sisteme geçiliyor: {e}")
                self._text_model = None
                self.use_fallback = True
    
    def _load_clip_model(self):
        """CLIP modelini yalnızca ilk çağrıda yükler (Görüntü/Metin Eşleştirme için)."""
        if self._clip_model is None:
            try:
                self._clip_processor = CLIPProcessor.from_pretrained(self.CLIP_MODEL_NAME)
                self._clip_model = CLIPModel.from_pretrained(self.CLIP_MODEL_NAME)
                logger.info(f"CLIP modeli başarıyla yüklendi.")
            except Exception as e:
                logger.error(f"CLIP MODEL YÜKLEME HATASI. Görüntü embedding'leri devre dışı: {e}")
                self._clip_model = None

    # --- 1. Metin Embedding'i Oluşturma ---
    def get_text_embedding(self, text: str) -> np.ndarray | None:
        """Metin verisinden vektör embedding'i oluşturur."""
        if not text:
            return None
            
        self._load_text_model()

        if self._text_model:
            try:
                # Model ile embedding oluştur
                embedding = self._text_model.encode(text)
                return embedding.astype(np.float32) # Bellek/depolama için float32 kullan
            except Exception as e:
                logger.error(f"Metin embedding oluşturma hatası: {e}")
                return self._fallback_text_embedding(text)
        else:
            return self._fallback_text_embedding(text)

    def _fallback_text_embedding(self, text: str) -> np.ndarray | None:
        """Basit bir yedek embedding (örneğin kelime sayısına dayalı)"""
        # Gerçek bir uygulamada bu, TF-IDF ile 384 boyutlu bir vektör döndürebilir.
        # Basit simülasyon: 384 boyutlu rastgele bir vektör dön
        logger.warning("Yedek (Fallback) metin embedding kullanılıyor.")
        if self.use_fallback:
             # Eğer fallback modundaysak, her seferinde aynı boyutta bir vektör dönmeliyiz.
             # Örnek: Kelime sayısına göre basit bir hashleme
             np.random.seed(len(text.split())) # Basit deterministik tohumlama
             return np.random.rand(self.embedding_dimension).astype(np.float32)
        return None

    # --- 2. Görüntü Embedding'i Oluşturma ---
    def get_image_embedding(self, image_path: str) -> np.ndarray | None:
        """Görüntü dosyasından (screenshot) vektör embedding'i oluşturur (CLIP ile)."""
        if not os.path.exists(image_path):
            logger.warning(f"Görüntü dosyası bulunamadı: {image_path}")
            return None
            
        self._load_clip_model()
        
        if self._clip_model and self._clip_processor:
            try:
                image = Image.open(image_path)
                inputs = self._clip_processor(images=image, return_tensors="pt", padding=True)
                
                # Modeli kullanarak görüntü vektörünü al
                with torch.no_grad(): # PyTorch import edilmediyse burada hata verir
                    image_features = self._clip_model.get_image_features(**inputs)
                
                # Vektörü normalize et ve numpy dizisi olarak döndür
                embedding = image_features.squeeze().cpu().numpy()
                return embedding.astype(np.float32)

            except Exception as e:
                logger.error(f"Görüntü embedding oluşturma hatası: {e}")
                return None
        return None # CLIP modeli yoksa None dön

def get_clip_text_embedding(self, text: str) -> np.ndarray | None:
        """
        Metni CLIP modeli ile vektöre dönüştürür (Resim aramak için kullanılır).
        Boyut: 512
        """
        if not text: return None
        
        self._load_clip_model()
        
        if self._clip_model and self._clip_processor:
            try:
                # CLIP Text Encoder kullanımı
                inputs = self._clip_processor(text=[text], return_tensors="pt", padding=True)
                
                with torch.no_grad():
                    text_features = self._clip_model.get_text_features(**inputs)
                
                # Normalize et ve numpy döndür
                embedding = text_features.squeeze().cpu().numpy()
                return embedding.astype(np.float32)
            except Exception as e:
                logger.error(f"CLIP Text embedding hatası: {e}")
                return None
        return None

def _load_semantic_model(self):
        """Semantic GNN/Transformer modelini yükler."""
        if not hasattr(self, '_semantic_model') or self._semantic_model is None:
            try:
                # Modeli başlatma (Gerçek uygulamada, bu bir eğitilmiş modeli diskten yüklemelidir.)
                IN_CHANNELS = 3  # RGB
                HIDDEN_CHANNELS = 128 
                NUM_CLASSES = 10 # Varsayılan sınıf sayısı (eğer segmentasyon da yapılıyorsa)
                
                self._semantic_model = HybridGNNTransformer(
                    in_channels=IN_CHANNELS, 
                    hidden_channels=HIDDEN_CHANNELS, 
                    num_classes=NUM_CLASSES
                )
                # self._semantic_model.load_state_dict(torch.load('path/to/trained_model.pth'))
                self._semantic_model.eval()
                logger.info("Semantic GNN/Transformer modeli başarıyla yüklendi/başlatıldı.")
            except Exception as e:
                logger.error(f"Semantic model yükleme hatası: {e}")
                self._semantic_model = None


    # --- 4. Görüntüyü Grafik Verisine Dönüştürme Metodu ---
        def image_to_graph_data(self, image_path: str):
            """
            Görüntüyü süperpiksel tabanlı PyG Data nesnesine dönüştürür.
            (a.py'deki create_superpixels, extract_node_features, create_edge_index, vb. çağırır)
            """
        self._load_semantic_model() # Modelin hazır olduğundan emin ol
        if not self._semantic_model:
            return None, None

        # 1. Süperpiksel Oluşturma
            image, labels, num_nodes = create_superpixels(image_path, n_segments=300) # num_segments düşürüldü

            if image is None: return None, None
        
        # 2. Düğüm Özellikleri ve Geri Oluşturma Hedefi Çıkarımı
            x, y_reco = extract_node_features(image, labels, num_nodes)
        
        # 3. Kenar İndeksi ve Ağırlık Oluşturma
            edge_index = create_edge_index(labels)
            edge_weights = calculate_edge_weights(x, edge_index)
        
        # 4. Akıllı Kenar Kırpma (Sıkıştırma için kritik)
            pruned_edge_index, pruned_edge_weights = intelligent_prune_edges(
                x, edge_index, edge_weights, compression_ratio=0.5
            )

        # PyG Data nesnesini oluşturma
            graph_data = Data(
                x=x, 
                edge_index=pruned_edge_index, 
                edge_attr=pruned_edge_weights, 
                y=torch.zeros(num_nodes, dtype=torch.long), # Sınıf etiketleri yoksa dummy etiket
                y_reco=y_reco # Geri oluşturma hedefi
            )
        
            return graph_data, labels

    # --- 5. Sıkıştırma (Encoding) Metodu ---
            def compress_graph_features(self, graph_data: Data) -> torch.Tensor:
                """Grafik verisini GNN/Transformer ile işler ve sıkıştırılmış özellikleri (x_final) döndürür."""
            if not self._semantic_model:
                raise Exception("Semantic model yüklenemedi.")
        
            with torch.no_grad():
                # Modelin sadece sıkıştırılmış özelliği hesaplayan bir fonksiyonu olmalı.
                # Forward metodu hem CLS hem RECO çıktığı için, burada sadece x_final'i alıyoruz.
                    x, edge_index, edge_attr = graph_data.x, graph_data.edge_index, graph_data.edge_attr

                    x_local = F.relu(self._semantic_model.gcn1(x, edge_index, edge_attr))
                    x_local = self._semantic_model.gcn2(x_local, edge_index, edge_attr)
                    x_global = self._semantic_model.transformer(x_local)
            
                    x_final = x_local + x_global # Bu sıkıştırılmış özelliktir.
            
                    return x_final

    # --- 6. Geri Oluşturma (Decoding) Metodu ---
        def decompress_graph_features(self, compressed_features: torch.Tensor) -> torch.Tensor:
            """Sıkıştırılmış özellikleri (x_final) alıp Decoder ile renkleri geri tahmin eder."""
            if not self._semantic_model:
                raise Exception("Semantic model yüklenemedi.")
            
            with torch.no_grad():
            # out_reco = self._semantic_model.decoder(compressed_features)
            # Eğer sadece x_final verilmişse, decoder'ı direkt çağırmak gerekir.
                out_reco = self._semantic_model.decoder(compressed_features)
                return out_reco

# Not: PyTorch (torch) import edilmelidir.