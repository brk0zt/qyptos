# memory/tests.py (Geliþtirilmiþ Versiyon)
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock
import numpy as np
import os
import shutil

# Proje Modüllerinizi import edin
from memory.models import MemoryItem, MemoryTier, UserMemoryProfile
from memory.services.advanced_memory_manager import AdvancedMemoryManager # Muhtemel Düzeltme
from memory.services.compression_engine import SemanticCompressionEngine   # Muhtemel Düzeltme
from memory.services.ai_services import AIService
from memory.management.commands.memory_maintenance import Command as MaintenanceCommand

# Mock Data için
TEST_USER_USERNAME = 'testuser'
TEST_EMBEDDING_DIM = 384
TEST_COMPRESSED_DIM = 64

User = get_user_model()

# --- Temel Ayarlar ve Hazýrlýk ---
def create_test_data(self):
    """Testler için MemoryTier ve Kullanýcý oluþturur."""
    self.user = User.objects.create_user(username=TEST_USER_USERNAME, password='password')
    self.profile, _ = UserMemoryProfile.objects.get_or_create(user=self.user)
    
    # Memory Tier'larý oluþtur (duration_days alanýný varsayýyoruz)
    self.tier_short = MemoryTier.objects.create(name='short_term', duration_minutes=1440) # 1 gün
    self.tier_long = MemoryTier.objects.create(name='long_term', duration_minutes=43200)  # 30 gün
    
    # Basit bir vektör oluþturucu
    def create_vector(seed):
        np.random.seed(seed)
        return np.random.rand(TEST_EMBEDDING_DIM).astype(np.float32).tobytes()
        
    self.vector_a = create_vector(1)
    self.vector_b = create_vector(2) # A'ya yakýn olmalý (tohumlar ardýþýk)
    self.vector_c = create_vector(100) # A'dan uzak olmalý

    # MemoryItem'lar oluþtur
    # Memory A: Arama sorgusuna çok yakýn (yüksek benzerlik skorunu simüle etmek için)
    self.item_a = MemoryItem.objects.create(
        user=self.user, memory_tier=self.tier_short, file_name='test_proje_raporu.pdf',
        content_summary='Ödeme sistemi projesiyle ilgili detaylý rapor.',
        vector_embedding=self.vector_a, access_count=10,
        expires_at=timezone.now() + timedelta(hours=2) # Süresi dolmak üzere
    )
    # Memory B: Daha az alakalý ama çok eriþimli (re-ranking'i test etmek için)
    self.item_b = MemoryItem.objects.create(
        user=self.user, memory_tier=self.tier_short, file_name='gundelik_notlar.txt',
        content_summary='Günlük hatýrlatýcýlar ve basit görevler.',
        vector_embedding=self.vector_b, access_count=50,
        expires_at=timezone.now() + timedelta(days=5)
    )
    # Memory C: Alakasýz ve süresi çoktan dolmuþ
    self.item_c = MemoryItem.objects.create(
        user=self.user, memory_tier=self.tier_long, file_name='eski_dosya.zip',
        content_summary='Alakasýz eski bir dosya.',
        vector_embedding=self.vector_c, access_count=1,
        expires_at=timezone.now() - timedelta(hours=1) # Süresi dolmuþ
    )

# --- TEST SINIFI 1: AdvancedMemoryManager Testleri ---
class AdvancedMemoryManagerTests(TestCase):
    def setUp(self):
        create_test_data(self)
        self.manager = AdvancedMemoryManager(self.user)
        
        # AIService.get_text_embedding'i mock'layarak deterministik sonuçlar al
        # Arama sorgusu 'Ödeme sistemi projesi' için vector_a'ya yakýn bir vektör dönsün
        with patch.object(AIService, 'get_text_embedding', return_value=np.frombuffer(self.vector_a, dtype=np.float32)):
            self.query_vector = AIService().get_text_embedding("ödeme sistemi projesi")

    @patch('memory.ai_services.AIService.get_text_embedding', autospec=True)
    def test_semantic_search_ranking(self, mock_get_embedding):
        """Arama sonuçlarýnýn hem benzerliðe hem de eriþim sayýsýna göre sýralandýðýný test et."""
        
        # Arama vektörünü simüle et (Item A'ya çok yakýn, Item B'ye biraz yakýn, Item C'ye uzak)
        mock_get_embedding.return_value = np.frombuffer(self.vector_a, dtype=np.float32)

        # Manager'ýn simüle edilmiþ arama metodunu çaðýr (simülasyonda tüm DB'den sorgular)
        results = self.manager.semantic_search(query="ödeme sistemi projesiyle ilgili rapor", limit=10)
        
        self.assertTrue(len(results) > 0)
        
        # Re-Ranking Mantýðý Testi:
        # Item B'nin eriþim sayýsý (50) çok daha yüksek, bu da ranking skorunu yükseltebilir.
        # Bu nedenle, Item A'nýn yüksek benzerliði ve Item B'nin yüksek eriþimi arasýnda bir denge olmalý.
        # Basitlik için, Item A'nýn yüksek benzerliðinden dolayý ilk sýrada gelmesi beklenir (genelde böyle olur).
        self.assertEqual(results[0]['file_name'], 'test_proje_raporu.pdf', "En alakalý öðe ilk sýrada olmalý.")
        self.assertIn('gundelik_notlar.txt', [r['file_name'] for r in results], "Diðer alakalý öðeler sonuçlarda olmalý.")

    def test_get_fused_timeline(self):
        """TimelineEvent ve UserActivity'nin birleþtirilip doðru sýralandýðýný test et."""
        # TimelineEvent ve UserActivity oluþtur (models.py import edilmeli)
        from memory.models import TimelineEvent, UserActivity
        
        yesterday = timezone.now() - timedelta(days=1)
        two_days_ago = timezone.now() - timedelta(days=2)
        
        TimelineEvent.objects.create(
            user=self.user, timestamp=yesterday, event_type='app_usage', title='VS Code Kullanýmý', confidence_score=0.9
        )
        UserActivity.objects.create(
            user=self.user, timestamp=two_days_ago, activity_type='file_open', window_title='Dokumaný Aç', target_file='test.md'
        )
        
        timeline = self.manager.get_fused_timeline(days=3)
        
        self.assertEqual(len(timeline), 2, "Ýki olay da timeline'da olmalý.")
        self.assertEqual(timeline[0]['title'], 'VS Code Kullanýmý', "Timeline en son olaya göre sýralanmalý.")
        self.assertEqual(timeline[1]['event_type'], 'file_open', "UserActivity de timeline'a dahil edilmeli.")

# --- TEST SINIFI 2: CompressionEngine Testleri ---
class CompressionEngineTests(TestCase):
    def setUp(self):
        self.engine = SemanticCompressionEngine()
        # Mocking için geçici bir dizin oluþtur
        self.temp_dir = 'test_pca_data'
        os.makedirs(self.temp_dir, exist_ok=True)
        self.pca_path = os.path.join(self.temp_dir, 'pca_compression_model.pkl')
        
        # SemanticCompressionEngine içindeki yolu geçici olarak ayarla
        self.engine.PCA_MODEL_PATH = self.pca_path
        self.engine.TARGET_DIMENSION = 10 # Kolay test için küçük bir boyut
        
        # PCA modeli yükleme/baþlatma mantýðýný yeniden çalýþtýr
        self.engine._load_or_init_pca()

    def tearDown(self):
        # Geçici dizini ve içeriðini temizle
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            
    def test_pca_training_and_compression(self):
        """PCA modelinin eðitildiðini ve vektörü baþarýlý bir þekilde sýkýþtýrdýðýný test et."""
        
        # 1. Eðitim verisi oluþtur (384 boyutlu 100 örnek)
        np.random.seed(42)
        original_vectors = [np.random.rand(TEST_EMBEDDING_DIM).astype(np.float32) for _ in range(100)]
        original_vectors_bytes = [v.tobytes() for v in original_vectors]

        # 2. PCA modelini eðit
        self.engine.fit_and_save_pca(original_vectors)
        self.assertTrue(self.engine.is_trained, "PCA modeli eðitilmiþ olmalý.")
        self.assertTrue(os.path.exists(self.pca_path), "Eðitilen model diske kaydedilmiþ olmalý.")
        
        # 3. Vektör sýkýþtýrma
        test_vector_bytes = original_vectors_bytes[0]
        compressed_vector_bytes = self.engine.compress_embedding(test_vector_bytes)
        
        self.assertIsNotNone(compressed_vector_bytes, "Sýkýþtýrýlmýþ vektör boþ olmamalý.")
        
        compressed_vector = np.frombuffer(compressed_vector_bytes, dtype=np.float32)
        self.assertEqual(compressed_vector.size, self.engine.TARGET_DIMENSION, "Vektör hedef boyuta sýkýþtýrýlmalý.")

# --- TEST SINIFI 3: Management Command Testleri ---
class MemoryMaintenanceTests(TestCase):
    def setUp(self):
        create_test_data(self)
        self.command = MaintenanceCommand()
        self.long_term_tier = MemoryTier.objects.get(name='long_term')
        
        # Silinecek bir dosya ile süresi dolmuþ MemoryItem oluþtur
        self.temp_file_path = os.path.join(self.command.COMMAND_DIR, 'test_cleanup_file.txt')
        os.makedirs(self.command.COMMAND_DIR, exist_ok=True)
        with open(self.temp_file_path, 'w') as f:
            f.write("Bu dosya silinmeli.")
        
        # Süresi dolmuþ ama silinmesi gereken öðe
        self.expired_item = MemoryItem.objects.create(
            user=self.user, memory_tier=self.tier_short, file_name='silinecek.txt',
            expires_at=timezone.now() - timedelta(hours=1),
            file_path=self.temp_file_path # Dosya yolunu ekle
        )

    def tearDown(self):
        # Geçici dosyayý ve dizinini temizle
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)
        
    def test_cleanup_expired_command(self):
        """Süresi dolmuþ öðelerin veritabanýndan ve diskten silindiðini test et."""
        
        # 1. Komutu çalýþtýr
        self.command.handle(cleanup=True)
        
        # 2. Doðrula: DB kaydý silinmiþ mi?
        self.assertFalse(MemoryItem.objects.filter(id=self.expired_item.id).exists(), "Süresi dolmuþ öðe veritabanýndan silinmeli.")
        
        # 3. Doðrula: Disk üzerindeki dosya silinmiþ mi?
        self.assertFalse(os.path.exists(self.temp_file_path), "Ýliþkili dosya diskten silinmeli.")

    @patch('memory.advanced_memory_manager.AdvancedMemoryManager.check_and_promote_memories')
    def test_compress_command(self, mock_promote):
        """Sýkýþtýrma komutunun AdvancedMemoryManager'ý çaðýrdýðýný test et."""
        
        # Süresi dolmak üzere olan bir öðe oluþtur (self.item_a)
        self.item_a.expires_at = timezone.now() + timedelta(minutes=5)
        self.item_a.save()
        
        # Komutu çalýþtýr
        self.command.handle(compress=True)
        
        # AdvancedMemoryManager'ýn içindeki ana yükseltme metodunun çaðrýldýðýný doðrula
        # Gerçek uygulamada, check_and_promote_memories_for_item metodu çaðrýlacaktý.
        # Bu mock, o metodun çaðrýlacaðýný simüle eder.
        self.assertTrue(mock_promote.called, "Sýkýþtýrma mantýðý AdvancedMemoryManager üzerinden çaðrýlmalý.")
        
        # Çaðrýlan metodun MemoryItem'ý uzun süreliye taþýyýp taþýmadýðýný kontrol et (Bu, mock'lanmadan önce yapýlýr)
        self.item_a.refresh_from_db()
        self.assertEqual(self.item_a.memory_tier, self.long_term_tier, "Öðe uzun süreli belleðe taþýnmalý.")

# Geliþtirilen tüm dosyalarýn import edilmesi gerektiði varsayýlýr (PyCharm gibi bir IDE'de çalýþýyorsanýz)
