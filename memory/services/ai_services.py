# memory/ai_services.py (Geliştirilmiş Versiyon)
import numpy as np
import logging
from transformers import CLIPProcessor, CLIPModel
from sentence_transformers import SentenceTransformer
from PIL import Image
import os
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.data import Data
from torch_geometric.nn import GCNConv
from skimage.segmentation import slic

logger = logging.getLogger(__name__)

# --- GÜNCELLEME 1: Düğüm Özellikleri (x) 0-1 Aralığına Normalize Ediliyor ---
def create_superpixels(image_path, n_segments=500, compactness=10):
    """
    Belirtilen goruntu yolu icin SLIC algoritmasi ile superpiksel olusturur.
    ...
    """
    try:
        image = io.imread(image_path)
        # Görüntünün float türüne dönüştürülmesi (0-255 -> 0.0-1.0 aralığı için gereklidir)
        if image.dtype == np.uint8:
             image = image.astype(np.float32) / 255.0

    except FileNotFoundError:
        print(f"HATA: '{image_path}' dosya yolu bulunamadi.")
        return None, None, 0
    
    # SLIC, Lab renk uzayında daha iyi çalışır. 
    # SLIC'e Lab görüntüsünü vermek yerine, genellikle RGB görüntüsü üzerinde çalışırız.
    # Ancak burada RGB görüntü, float olarak (0-1) aralığına getirildi.
    labels = slic(
        image, 
        n_segments=n_segments, 
        compactness=compactness, 
        enforce_connectivity=True,
        sigma=0
    )

    num_superpixels = len(np.unique(labels))
    
    print(f"Basarili: {num_superpixels} adet superpiksel (dugum) olusturuldu.")

    # Orijinal Görüntüyü (0-1 aralığında) döndürüyoruz
    return image, labels, num_superpixels


def visualize_superpixels(image, labels):
    """Superpiksel sinirlarini orijinal goruntu uzerinde gorsellestirir."""
    from skimage.segmentation import mark_boundaries
    
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    # mark_boundaries için girdi görüntüsü 0-1 aralığında olmalıdır.
    ax.imshow(mark_boundaries(image, labels, color=(1, 1, 1))) 
    ax.set_title("Olusturulan Superpikseller (Dugumler)")
    ax.axis('off')
    plt.show()

# --- GÜNCELLEME 2: Geri Oluşturma Hedefi (y_reco) için Kullanılacak Özellik Çıkarımı ---
def extract_node_features(image_rgb, labels, num_nodes):
    """
    Her bir superpiksel icin ortalama RGB degerlerini hesaplar.
    
    Args:
        image_rgb (numpy.ndarray): Orijinal RGB goruntu matrisi (0-1 araliginda).
        ...
        
    Returns:
        torch.Tensor: Her dugum icin ozellik vektorlerini iceren matris (PyG'deki 'x').
        torch.Tensor: Geri olusturma hedefi olarak kullanilacak ortalama renkler (y_reco).
    """
    # Görüntü boyutları: (Yükseklik, Genişlik, Kanal=3)
    height, width, channels = image_rgb.shape
    
    node_features_np = np.zeros((num_nodes, channels), dtype=np.float32)
    pixel_counts = np.zeros(num_nodes, dtype=np.int32)

    # 1. Pikselleri Süperpiksel Etiketine Göre Gruplama
    for i in range(height):
        for j in range(width):
            label = labels[i, j]
            node_features_np[label] += image_rgb[i, j]
            pixel_counts[label] += 1

    # 2. Ortalama Hesaplama (Toplam/Sayı)
    pixel_counts_expanded = pixel_counts[:, np.newaxis] 
    
    node_features_np = np.divide(
        node_features_np, 
        pixel_counts_expanded, 
        out=node_features_np, 
        where=pixel_counts_expanded != 0 
    )
    
    print(f"Basarili: Dugum ozellik matrisi boyutu: {node_features_np.shape}")

    # PyTorch Geometric için Tensor'a dönüştürme.
    # Bu, hem modelin girdisi (`x`) hem de geri oluşturma hedefi (`y_reco`) olacaktır.
    node_features_tensor = torch.tensor(node_features_np, dtype=torch.float)
    
    # y_reco: Süperpikselin orijinal ortalama rengini tutar (Geri oluşturma hedefi)
    y_reco = node_features_tensor.clone()

    return node_features_tensor, y_reco # İki çıktı döndürülüyor


def create_edge_index(labels):
    """
    Superpiksel etiketlerine dayanarak birbirine temas eden superpiksel ciftlerini (kenarlari) bulur.
    ...
    """
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
                        edge1 = (int(src_label), int(dest_label))
                        edge2 = (int(dest_label), int(src_label))
                        
                        adj_set.add(edge1)
                        adj_set.add(edge2)

    source_nodes = [edge[0] for edge in adj_set]
    target_nodes = [edge[1] for edge in adj_set]
    
    edge_index = torch.tensor([source_nodes, target_nodes], dtype=torch.long)
    
    print(f"Basarili: Toplam {len(adj_set)} adet simetrik kenar olusturuldu.")
    print(f"PyG 'edge_index' boyutu: {edge_index.shape}")
    
    return edge_index


def calculate_edge_weights(x, edge_index):
    """
    Kenar agirliklarini, bagli oldugu dugumlerin (superpiksellerin) ozellik vektorleri 
    (ortalama RGB) arasindaki Oklid Mesafesi (L2 norm) olarak hesaplar.
    ...
    """
    source_nodes = edge_index[0]
    target_nodes = edge_index[1]

    source_features = x[source_nodes]
    target_features = x[target_nodes]

    diff_features = source_features - target_features

    edge_weights = torch.norm(diff_features, p=2, dim=1)
    
    print(f"Basarili: Kenar agirlik vektoru boyutu: {edge_weights.shape}")

    return edge_weights

def intelligent_prune_edges(x, edge_index, edge_weights, compression_ratio=0.7):
    """
    Kenar agirliklarina (onem puanlarina) gore iliskileri akillica kirpar (seyreklestirir).
    ...
    """
    scores = edge_weights.cpu().numpy()
    
    # compression_ratio = 0.7 ise, en düşük %30'luk puanı threshold olarak belirle.
    threshold = np.percentile(scores, (compression_ratio * 100))
    
    # Sadece threshold değerinden büyük veya eşit olan kenarları koru (En önemli/farklı ilişkiler)
    mask = edge_weights >= threshold

    pruned_edge_index = edge_index[:, mask]
    pruned_edge_weights = edge_weights[mask]
    
    original_edges = edge_index.size(1)
    pruned_edges = pruned_edge_index.size(1)
    pruning_percentage = 1 - (pruned_edges / original_edges)
    
    print(f"\n--- Akilli Kirpma Sonucu ---")
    print(f"Orijinal Kenar Sayisi: {original_edges}")
    print(f"Kirpilmis Kenar Sayisi: {pruned_edges}")
    print(f"Seyreklestirme Orani (Kirpilan): %{pruning_percentage * 100:.2f}")
    
    return pruned_edge_index, pruned_edge_weights

def calculate_node_centrality(labels, num_nodes):
    """
    Her dugum icin goruntu merkezine olan yakinliga dayali bir onem puani hesaplar.
    ...
    """
    height, width = labels.shape
    center_y, center_x = height / 2, width / 2
    
    y_coords_sum = np.zeros(num_nodes)
    x_coords_sum = np.zeros(num_nodes)
    pixel_counts = np.zeros(num_nodes)

    for r in range(height):
        for c in range(width):
            label = labels[r, c]
            y_coords_sum[label] += r
            x_coords_sum[label] += c
            pixel_counts[label] += 1

    pixel_counts[pixel_counts == 0] = 1 
    
    sp_centers_y = y_coords_sum / pixel_counts
    sp_centers_x = x_coords_sum / pixel_counts
    
    distances = np.sqrt((sp_centers_y - center_y)**2 + (sp_centers_x - center_x)**2)
    
    max_distance = np.sqrt(center_y**2 + center_x**2)
    
    centrality_score_np = 1 - (distances / max_distance)
    
    print(f"Basarili: Dugum merkezilik puanlari hesaplandi.")
    
    return torch.tensor(centrality_score_np, dtype=torch.float)

# --- Hafifletilmiş Transformer Encoder Tanımı (Değişmedi) ---
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

# --- GÜNCELLEME 3: Semantic Decoder Tanımı (Ayrı Bir Modül Olarak Korundu) ---
class SemanticDecoder(nn.Module):
    def __init__(self, in_features, out_channels=3):
        super().__init__()
        # in_features: hidden_channels (GNN çıktısı boyutu)
        # out_channels: 3 (RGB geri oluşturma)
        self.fc1 = nn.Linear(in_features, in_features * 2) 
        self.fc2 = nn.Linear(in_features * 2, out_channels) 
    
    def forward(self, x):
        # x: (num_nodes, in_features)
        x = F.relu(self.fc1(x))
        # Sigmoid, çıktının 0 ile 1 arasında olmasını sağlar (normalize edilmiş renkler için).
        return torch.sigmoid(self.fc2(x))

class DifferentialPrivacy:
    def __init__(self, epsilon=1.0, delta=1e-5):
        self.epsilon = epsilon
        self.delta = delta
    
    def add_noise(self, tensor):
        sigma = math.sqrt(2 * math.log(1.25 / self.delta)) / self.epsilon
        noise = torch.randn_like(tensor) * sigma
        return tensor + noise

# --- GÜNCELLEME 4: HybridGNNTransformer Sınıfına Decoder Entegrasyonu ---
class HybridGNNTransformer(nn.Module):
    def __init__(self, in_channels, hidden_channels, num_classes, num_heads=4):
        # out_channels -> num_classes olarak yeniden adlandırıldı, karışıklığı önlemek için
        super().__init__()
        
        # GNN Bileşeni (Yerel/Temas Eden İlişki Özellikleri)
        self.gcn1 = GCNConv(in_channels, hidden_channels)
        self.gcn2 = GCNConv(hidden_channels, hidden_channels) 
        
        # Transformer Bileşeni (Global/Uzun Menzilli İlişki Modelleme)
        self.transformer = LightweightTransformerEncoder(
            embed_dim=hidden_channels, 
            num_heads=num_heads
        )
        
        # Nihai Sınıflandırıcı (Semantic Segmentasyon için, isteğe bağlı)
        self.classifier = nn.Linear(hidden_channels, num_classes)
        
        # !!! SEMANTİK SIKIŞTIRMA İÇİN YENİ EKLEME !!!
        # Geri oluşturma (Decoder) modülü. hidden_channels'tan 3 kanallı (RGB) çıktıya gider.
        self.decoder = SemanticDecoder(hidden_channels, out_channels=3)

    def forward(self, data):
        x, edge_index, edge_attr = data.x, data.edge_index, data.edge_attr
        
        # --- GNN Aşaması (Yerel Bilgi İşleme) ---
        x_local = F.relu(self.gcn1(x, edge_index, edge_attr))
        x_local = F.dropout(x_local, p=0.5, training=self.training)
        x_local = self.gcn2(x_local, edge_index, edge_attr) # (num_nodes, hidden_channels)

        # --- Transformer Aşaması (Global Bilgi İşleme) ---
        x_global = self.transformer(x_local)

        # --- Birleştirme (Sıkıştırılmış Özellik Vektörü) ---
        # Bu, sıkıştırılmış (compressed) anlamsal özellik vektörüdür.
        x_final = x_local + x_global 
        
        # --- Çıktılar ---
        # 1. Sınıflandırma Çıktısı (Segmentasyon)
        out_cls = F.log_softmax(self.classifier(x_final), dim=1)
        
        # 2. Geri Oluşturma Çıktısı (Sıkıştırma)
        # Sıkıştırılmış anlamsal özellikler, decoder'a gönderilir.
        out_reco = self.decoder(x_final) 
        
        # Hem sınıflandırma hem de geri oluşturma çıktılarını döndür
        return out_cls, out_reco


def add_gaussian_noise(g, clip_norm, epsilon, delta):
    """ Gradyanlara gizlilik butcesine göre Gaussian gurultusu ekler. (Degismedi)"""
    sigma = (clip_norm * math.sqrt(2 * math.log(1 / delta))) / epsilon
    noise = torch.randn_like(g) * sigma
    return g + noise

# --- GÜNCELLEME 5: Eğitim Döngüsünde (train_gcn_with_dp) Kayıp Fonksiyonu Değişikliği ---
def train_gcn_with_dp(model, data, optimizer, num_epochs, dp_enabled=False, clip_norm=1.0, epsilon=1.0, delta=1e-5, lambda_reco=0.5):
    """
    Differential Privacy (DP) ile guclendirilmis, SEMANTIK SIKISTIRMA icin 
    Geri Olusturma Kaybi (Reconstruction Loss) iceren egitim dongusu.
    
    Args:
        ...
        lambda_reco (float): Geri olusturma kaybinin (MSE) toplam kayiba olan agirligi.
    """
    
    # Kayıp Fonksiyonları
    # NLL Loss: Sınıflandırma için
    # MSE Loss: Geri oluşturma (Reconstruction) için. Hedef (data.y_reco) ile modelin geri oluşturma çıktısı (out_reco) arasındaki farkı hesaplar.
    classification_criterion = F.nll_loss
    reconstruction_criterion = nn.MSELoss()
    
    # Model eğitimi
    model.train()
    for epoch in range(num_epochs):
        optimizer.zero_grad()
        
        # Modelden iki çıktı alınır: sınıflandırma ve geri oluşturma
        out_cls, out_reco = model(data)
        
        # 1. Sınıflandırma Kaybı (Sınıf Etiketi varsa)
        # y: Sınıf etiketlerini tutan Tensör (PyG'de `data.y`)
        cls_loss = classification_criterion(out_cls, data.y)
        
        # 2. Geri Oluşturma Kaybı
        # y_reco: Orijinal süperpiksel ortalama renkleri (PyG'de `data.y_reco` olarak kabul edilecek)
        reco_loss = reconstruction_criterion(out_reco, data.y_reco)
        
        # Toplam Kayıp = Sınıflandırma Kaybı + (lambda * Geri Oluşturma Kaybı)
        total_loss = cls_loss + lambda_reco * reco_loss
        
        total_loss.backward()

        if dp_enabled:
            # DP Adımları (Değişmedi)
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
        
        if epoch % 20 == 0:
            print(f'Epoch: {epoch:03d}, Toplam Kayip: {total_loss:.4f} (CLS: {cls_loss:.4f}, RECO: {reco_loss:.4f})')

    print(f"\nDP: {dp_enabled} - Semantik Sikistirma Egitimi Tamamlandi!")
    return model

class LatticeCrypto:
    def __init__(self, dimension=512):
        self.dimension = dimension
        try:
            self.kem = oqs.KeyEncapsulation("Kyber512")
            self.public_key = self.kem.generate_keypair()
        except:
            print("⚠️ OQS kütüphanesi yüklenemedi - simulation modu")
            self.simulation_mode = True
    
    def encrypt(self, data):
        if hasattr(self, 'simulation_mode'):
            return {"simulated": True, "data": data}
        ciphertext, shared_secret = self.kem.encap_secret(self.public_key)
        return {"ciphertext": ciphertext, "public_key": self.public_key}

class QuantumResistantEncoder:
    def __init__(self):
        # Kyber vı Dilithium implementasyonu gerekli
        self.lattice_crypto = LatticeCrypto(dimension=512)
    
    def encrypt_semantic_features(self, features):
        # Semantic özellikleri lattice tabanlı şifrele
        encrypted = self.lattice_crypto.encrypt(features)
        return encrypted

class QyptosFileHandler:
    def __init__(self):
        self.semantic_header = {
            'compression_type': 'semantic_hybrid',
            'security_level': 'quantum_resistant',
            'semantic_map': 'encrypted_relations'
        }
    
    def save_compressed(self, model_output, file_path):
        # Semantic sıkıştırılmış veriyi .qyptos formatında kaydet
        pass


class WiFiDependentSecurity:
    def __init__(self):
        self.trusted_networks = ["Home_WiFi", "Office_Network"]
    
    def verify_wifi_and_decrypt(self, encrypted_data, current_wifi):
        if current_wifi in self.trusted_networks:
            return self.decrypt(encrypted_data)
        else:
            self.self_destruct()
            return None
    
    def decrypt(self, encrypted_data):  # ✅ BU METODU EKLE
        # Şifre çözme implementasyonu
        return encrypted_data.get("data") if encrypted_data.get("simulated") else None
    
    def self_destruct(self):  # ✅ BU METODU EKLE
        print("🚨 GÜVENLİK: WiFi dogrulama basarisiz - self-destruct!")

class SelfDestructProtocol:
    def __init__(self, max_duration=3600):  # 1 saat
        self.creation_time = time.time()
        self.max_duration = max_duration
    
    def check_and_destroy(self):
        if time.time() - self.creation_time > self.max_duration:
            self.secure_erase()
    
    def secure_erase(self):
        # 10-pass overwrite ile güvenli silme
        for i in range(10):
            self.overwrite_with_random()

class AdvancedSecurityModule:
    def __init__(self):
        self.quantum_crypto = LatticeCrypto()
        self.differential_privacy = DifferentialPrivacy()
        self.self_destruct = SelfDestructProtocol()
        self.wifi_validator = WiFiDependentSecurity()
    
    def secure_processing_pipeline(self, image_data):
        # 1. Semantic sıkıştırma
        compressed = self.semantic_compress(image_data)
        
        # 2. Quantum şifreleme
        encrypted = self.quantum_crypto.encrypt(compressed)
        
        # 3. .qyptos formatında paketle
        qyptos_file = self.create_qyptos_file(encrypted)
        
        return qyptos_file

class CameraSecurityMonitor:
    def __init__(self):
        def detect_lens_obstruction(self):  # ✅ BUNU EKLE
        # Kamera lens tespit algoritması
            return False

        self.camera_active = False
        self.lens_detection = False

    def self_destruct_media(self):  # ✅ BUNU EKLE  
        print("🚨 GUVENLIK: Medya imha ediliyor...")
        # Medyayı güvenli şekilde sil

    def monitor_camera_security(self):
        while self.media_active:
            if self.detect_lens_obstruction() or not self.camera_active:
                self.self_destruct_media()
                break

class AIService:
    """
    Tüm ML/AI modellerini yöneten ve verimli bir şekilde embedding'ler oluşturan servis.
    Modelleri Lazy Loading ile yükler.
    """

    def train_semantic_model(self, graph_data_list, num_epochs=100, is_dp_enabled=True, epsilon=1.0):
        """
        Jakobiyen Tabanlı DP kullanarak Semantik Modeli Eğitir.
        """
        self._load_semantic_model() # Modelin yüklü olduğundan emin ol
        if not self._semantic_model:
            logger.error("Eğitim için Semantic model yüklenemedi.")
            return

        optimizer = optim.Adam(self._semantic_model.parameters(), lr=self.user_profile.learning_rate)
        
        # Tüm grafikleri birleştirme (Batchleme veya tekil grafik eğitimi)
        # Örnek olarak, tek bir büyük grafikte eğittiğimizi varsayalım:
        combined_data = Data.from_separate_graphs(graph_data_list)
        
        # Yeni ve Gelişmiş Eğitim Fonksiyonunu Çağır
        from .a import train_gcn_with_dp # veya DP helpers'ın olduğu doğru modülü import edin.
        
        # Epsilon ve kuantil değerlerini dinamik olarak yönetebiliriz.
        trained_model = train_gcn_with_dp(
            model=self._semantic_model,
            data=combined_data,
            optimizer=optimizer,
            num_epochs=num_epochs,
            dp_enabled=is_dp_enabled,
            jacobian_clip_quantile=0.9, # %90 kuantilini kullan
            epsilon=epsilon, 
            delta=1e-5 # Standart delta değeri
        )
        
        # Eğitilmiş modeli kaydetme mantığı buraya eklenir.
        # self._save_semantic_model(trained_model)
        logger.info(f"Semantik model, Jakobiyen-Temelli DP ile başarıyla eğitildi (Epsilon: {epsilon}).")
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
