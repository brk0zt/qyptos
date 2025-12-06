# memory/compression_engine.py (Geliþtirilmiþ Versiyon)
import numpy as np
from sklearn.decomposition import PCA
import logging
import pickle
import os
import zlib # Yapýsal veri sýkýþtýrmasý için
import json
from .ai_services import AIService


logger = logging.getLogger(__name__)

# Sabitler
PCA_MODEL_PATH = 'data/pca_compression_model.pkl'
TARGET_DIMENSION = 64 # Örn: 384 boyutlu vektörü 64 boyuta düþürmek

class SemanticCompressionEngine:
    """
    Vektor embedding'lerini (PCA) ve yapisal verileri (zlib) sikistirmaktan sorumlu motor.
    """
    def __init__(self):
        self._pca_model = None
        self.is_trained = False
        self._load_or_init_pca()

    def _load_or_init_pca(self):
        """Kayitli PCA modelini yukler veya bos bir model baslatir."""
        os.makedirs(os.path.dirname(PCA_MODEL_PATH), exist_ok=True)
        
        if os.path.exists(PCA_MODEL_PATH):
            try:
                with open(PCA_MODEL_PATH, 'rb') as f:
                    self._pca_model = pickle.load(f)
                    self.is_trained = True
                    logger.info("Kayitli PCA modeli basariyla yuklendi.")
            except Exception as e:
                logger.error(f"PCA modeli yuklenirken hata olustu: {e}")
                self._pca_model = PCA(n_components=TARGET_DIMENSION)
        else:
            self._pca_model = PCA(n_components=TARGET_DIMENSION)
            logger.info(f"Yeni PCA modeli baslatildi. Egitim bekleniyor.")

    def semantic_compress_image(self, image_path: str, ai_service: AIService) -> dict | None:
        """
        Goruntuyu alir, GNN modelini kullanarak semantik grafige donusturur ve sikistirir.
        
        Dondurulen dict, MemoryItem modeline kaydetmek icin hazir alanlari icerir.
        """
        logger.info(f"Semantik sikistirma baslatiliyor: {image_path}")
        
        # 1. Grafik Veri Hazýrlýðý
        graph_data, sp_map = ai_service.image_to_graph_data(image_path)

        if graph_data is None:
            logger.warning("Grafik veri hazirlanamadi.")
            return None
            
        # 2. Sýkýþtýrma (Embedding Çýkarýmý)
        compressed_features = ai_service.compress_graph_features(graph_data)
            
        # 3. Verileri saklama için hazýrlama (bytes ve zlib)
        
        # Sýkýþtýrýlmýþ özellikler (Tensor -> Numpy -> Bytes)
        semantic_features_bytes = compressed_features.cpu().numpy().astype(np.float32).tobytes()
        
        # Grafik Topolojisi (Edge Index) - Zlib ile sýkýþtýrýlmýþ
        edge_index_bytes = zlib.compress(graph_data.edge_index.cpu().numpy().astype(np.int32).tobytes())
        
        # Süperpiksel Haritasý (sp_map) - Zlib ile sýkýþtýrýlmýþ
        superpixel_map_bytes = zlib.compress(sp_map.astype(np.int32).tobytes())
        
        # Meta veriler
        metadata = {
            'num_nodes': compressed_features.shape[0],
            'feature_dim': compressed_features.shape[1],
            'image_shape': sp_map.shape,
            'original_edge_count': graph_data.edge_index.size(1),
            'pruned_edge_count': graph_data.edge_index.size(1)
        }
        
        logger.info(f"Sikistirma tamamlandi. Dugum: {metadata['num_nodes']}, Ozellik Boyutu: {metadata['feature_dim']}")
        
        return {
            'semantic_features': semantic_features_bytes,
            'graph_topology': edge_index_bytes,
            'superpixel_map': superpixel_map_bytes,
            'graph_metadata': metadata,
            'is_semantically_compressed': True
        }

    # --- YENÝ SEMANTÝK GRAFÝK GERÝ OLUÞTURMA (Decompress) Metodu ---
    def semantic_decompress_image(self, memory_item, ai_service: AIService) -> np.ndarray | None:
        """
        MemoryItem'dan sikistirilmis veriyi geri alip, Decoder ile goruntuyu tahmin eder.
        """
        if not memory_item.is_semantically_compressed:
             logger.warning(f"Item {memory_item.id} semantik olarak sikistirilmamis.")
             return None
             
        try:
            # 1. Veriyi Geri Çözme (Bytes -> Numpy/Tensor)
            features_np = np.frombuffer(memory_item.semantic_features, dtype=np.float32)
            metadata = memory_item.graph_metadata
            num_nodes = metadata['num_nodes']
            feature_dim = metadata['feature_dim']
            
            # Geri oluþturma için Tensor'a dönüþtür
            compressed_features = torch.tensor(features_np.reshape(num_nodes, feature_dim), dtype=torch.float)

            # 2. Geri Oluþturma (Decoder)
            reconstructed_colors = ai_service.decompress_graph_features(compressed_features)
            
            # 3. Süperpiksel Haritasýný Geri Çözme
            sp_map_np = np.frombuffer(zlib.decompress(memory_item.superpixel_map), dtype=np.int32)
            image_shape = metadata['image_shape']
            sp_map = sp_map_np.reshape(image_shape)
            
            # 4. Görüntüyü Tekrar Oluþturma
            reconstructed_image = np.zeros(image_shape, dtype=np.float32)
            
            # Her pikseli, ait olduðu süperpikselin tahmin edilen ortalama rengiyle doldur
            # .cpu().numpy() çaðrýsý performansý etkileyebilir, ancak tam doðruluk için gereklidir.
            for i in range(image_shape[0]):
                for j in range(image_shape[1]):
                    sp_label = sp_map[i, j]
                    reconstructed_image[i, j] = reconstructed_colors[sp_label].cpu().numpy()
                    
            # 0-1 aralýðýndaki görüntüyü döndür (PIL/Skimage ile gösterilmeye hazýr)
            return reconstructed_image
            
        except Exception as e:
            logger.error(f"Semantik geri olusturma hatasi: {e}")
            return None

    # --- 1. Vektör Embedding Sýkýþtýrma ---
    def fit_and_save_pca(self, data_samples: list[np.ndarray]):
        """PCA modelini veririlen vektor ornekleriyle egitir ve diske kaydeder."""
        if not data_samples:
            return
            
        # Eðer zaten eðitimli ise, yeniden eðitmemek için kontrol
        if self.is_trained:
            logger.info("PCA zaten egitilmis, yeniden eigtim atlandi.")
            return

        data_matrix = np.array(data_samples)
        
        try:
            self._pca_model.fit(data_matrix)
            self.is_trained = True
            
            # Eðitilen modeli kaydet
            with open(PCA_MODEL_PATH, 'wb') as f:
                pickle.dump(self._pca_model, f)
            logger.info(f"PCA modeli {len(data_samples)} ornekle egitildi ve kaydedildi.")
            
        except Exception as e:
            logger.error(f"PCA egitimi sirasinda hata olustu: {e}")

    def compress_embedding(self, original_embedding: bytes) -> bytes | None:
        """Egitilmis PCA modelini kullanarak vektoru sikistirir."""
        if not self.is_trained or original_embedding is None:
            logger.warning("PCA egitilmedi veya girdi bos. Sikistirma yapilamadi.")
            return None
            
        try:
            # Girdi bytes ise numpy array'e dönüþtür
            vector = np.frombuffer(original_embedding, dtype=np.float32).reshape(1, -1)
            
            # Dönüþtür
            compressed_vector = self._pca_model.transform(vector)
            
            # Sonucu bytes olarak döndür
            return compressed_vector.astype(np.float32).tobytes()
        except Exception as e:
            logger.error(f"Vektor sikistirma hatasi: {e}")
            return None

    # --- 2. Yapýsal Veri Sýkýþtýrma ---
    def compress_structural_data(self, data: str) -> bytes:
        """JSON veya metin formatindaki yapisal veriyi zlib ile sikistirir."""
        # UTF-8 olarak encode et ve zlib ile sýkýþtýr
        return zlib.compress(data.encode('utf-8'))

    def decompress_structural_data(self, compressed_data: bytes) -> str:
        """Sikistirilmis veriyi cozer ve metin olarak dondurur."""
        # zlib ile çöz ve UTF-8 olarak decode et
        return zlib.decompress(compressed_data).decode('utf-8')