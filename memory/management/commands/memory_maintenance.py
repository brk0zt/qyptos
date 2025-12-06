# memory/management/commands/memory_maintenance.py (Geliştirilmiş Versiyon)
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Count
from datetime import timedelta
import os
import numpy as np
import logging
from memory.models import MemoryItem, MemoryTier
from memory.services.advanced_memory_manager import AdvancedMemoryManager # Muhtemel Düzeltme
from memory.services.compression_engine import SemanticCompressionEngine   # Muhtemel Düzeltme
from memory.services.ai_services import AIService

logger = logging.getLogger(__name__)
User = get_user_model()
PCA_TRAIN_SAMPLE_SIZE = 10000 # PCA için toplanacak maksimum vektör sayısı

class Command(BaseCommand):
    help = 'Bellek bakım işlemlerini gerçekleştirir: Temizlik, Sıkıştırma ve PCA Eğitimi.'
    
    def add_arguments(self, parser):
        # Mevcut argümanlar
        parser.add_argument('--compress', action='store_true', help='Kısa süreli bellekten uzun süreliye taşı ve sıkıştır.')
        parser.add_argument('--cleanup', action='store_true', help='Süresi dolmuş memory itemlarını temizle (Veritabanı ve Disk).')
        
        # Yeni argüman
        parser.add_argument('--train_pca', action='store_true', help='Sıkıştırma motoru için PCA modelini eğitir.')
    
    def handle(self, *args, **options):
        # Hangi işlevlerin çalışacağını belirle
        should_compress = options['compress']
        should_cleanup = options['cleanup']
        should_train_pca = options['train_pca']

        if not any([should_compress, should_cleanup, should_train_pca]):
            self.stdout.write(self.style.WARNING("Hiçbir işlem belirtilmedi. --compress, --cleanup veya --train_pca kullanın."))
            return

        # Tek bir geçişte tüm işlemleri verimli bir şekilde yap
        if should_cleanup:
            self.cleanup_expired()
            
        if should_compress:
            self.compress_memories()
            
        if should_train_pca:
            self.train_pca_model()
            
        self.stdout.write(self.style.SUCCESS('Bellek bakımı tamamlandı.'))

    # --- İşlem 1: Memory Item Sıkıştırma ve Yükseltme ---
    def compress_memories(self):
        self.stdout.write(">> Kısa süreli belleği sıkıştırma ve yükseltme başlatılıyor...")
        try:
            # Sıkıştırma için uygun katmanı al (models.py'den varsayılan adı alıyoruz)
            short_term_tier = MemoryTier.objects.get(name='short_term')
        except MemoryTier.DoesNotExist:
            self.stdout.write(self.style.ERROR("short_term MemoryTier bulunamadı. Atlanıyor."))
            return

        # Sıkıştırma eşiği: Şu andan itibaren 6 saat içinde süresi dolacaklar
        expiration_threshold = timezone.now() + timedelta(hours=6)
        
        # Sıkıştırılması gereken öğeleri bul (yalnızca vector_embedding'i olanları)
        memories_to_process = MemoryItem.objects.filter(
            memory_tier=short_term_tier,
            expires_at__lte=expiration_threshold,
            vector_embedding__isnull=False,
            compressed_embedding__isnull=True # Daha önce sıkıştırılmamış olanlar
        ).select_related('user') # Kullanıcı verisini tek sorguda al

        users = set(m.user for m in memories_to_process)
        
        for user in users:
            manager = AdvancedMemoryManager(user)
            user_memories = [m for m in memories_to_process if m.user == user]
            self.stdout.write(f"  -> {user.username} için {len(user_memories)} öğe işleniyor.")
            
            for memory in user_memories:
                # AdvancedMemoryManager'daki check_and_promote_memories metodunun mantığını çağır
                manager.check_and_promote_memories_for_item(memory) # Yeni eklenen yardımcı metod
                self.stdout.write(self.style.NOTICE(f"    [Sıkıştırıldı]: {memory.file_name[:40]}..."))

    # --- İşlem 2: Süresi Dolmuş Öğeleri Temizleme (Veritabanı ve Disk) ---
    def cleanup_expired(self):
        self.stdout.write(">> Süresi dolmuş memory itemlarını temizleme başlatılıyor...")
        
        expired_memories = MemoryItem.objects.filter(expires_at__lte=timezone.now())
        total_count = expired_memories.count()
        deleted_file_count = 0

        self.stdout.write(f"Toplam {total_count} süresi dolmuş öğe bulundu.")
        
        for memory in expired_memories:
            # 1. Disk üzerindeki dosyaları sil (Ekran Görüntüsü veya İlgili Dosya)
            paths_to_check = [memory.screenshot_path, memory.file_path]
            for path in paths_to_check:
                if path and os.path.exists(path):
                    try:
                        os.remove(path)
                        deleted_file_count += 1
                    except OSError as e:
                        logger.error(f"Dosya silinirken hata oluştu ({path}): {e}")
            
            # 2. Veritabanı kaydını sil
            memory.delete()
            
        self.stdout.write(self.style.SUCCESS(f"✅ {total_count} kayıt veritabanından, {deleted_file_count} dosya diskten silindi."))

    # --- İşlem 3: PCA Modelini Eğitme ---
    def train_pca_model(self):
        self.stdout.write(f">> PCA modelini eğitme başlatılıyor ({PCA_TRAIN_SAMPLE_SIZE} örnekle)...")
        
        engine = SemanticCompressionEngine()
        
        # Son eklenen (ve sıkıştırılmamış) vektörleri al
        recent_uncompressed_items = MemoryItem.objects.filter(
            vector_embedding__isnull=False,
            compressed_embedding__isnull=True
        ).order_by('-created_at')[:PCA_TRAIN_SAMPLE_SIZE]

        if not recent_uncompressed_items:
            self.stdout.write(self.style.WARNING("Eğitim için yeterli yeni vektör (MemoryItem) bulunamadı."))
            return

        # Vektörleri topla
        data_samples = []
        for item in recent_uncompressed_items:
            # BinaryField'dan numpy array'e dönüştür
            vector = np.frombuffer(item.vector_embedding, dtype=np.float32)
            if vector.size > 0:
                data_samples.append(vector)
                
        if data_samples:
            # Toplu eğitimi yap
            engine.fit_and_save_pca(data_samples)
            self.stdout.write(self.style.SUCCESS(f"✅ PCA modeli {len(data_samples)} örnekle başarıyla eğitildi ve kaydedildi."))
        else:
             self.stdout.write(self.style.WARNING("Toplanan örneklerde geçerli vektör bulunamadı."))