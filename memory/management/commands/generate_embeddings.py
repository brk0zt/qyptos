# memory/management/commands/generate_embeddings.py (Sync + Generate)
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model
from memory.models import MemoryItem, MemoryTier
from memory.services.ai_services import AIService
import os
import mimetypes

User = get_user_model()

class Command(BaseCommand):
    help = 'Diskteki dosyaları tarar, eksikse hafızaya ekler ve vektörleri oluşturur.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Vektörü olsa bile yeniden oluştur.')

    def handle(self, *args, **options):
        force_update = options['force']
        ai_service = AIService()
        
        self.stdout.write("--- 1. ADIM: Disk ve Hafıza Senkronizasyonu ---")
        self.sync_files_from_disk()
        
        self.stdout.write("\n--- 2. ADIM: Embedding (Vektör) Oluşturma ---")
        
        if force_update:
            items = MemoryItem.objects.all()
            self.stdout.write(self.style.WARNING("Mod: FORCE (Tüm dosyalar yeniden işlenecek)"))
        else:
            items = MemoryItem.objects.filter(vector_embedding__isnull=True)
            self.stdout.write("Mod: Sadece eksik vektörler")

        total_count = items.count()
        self.stdout.write(f"İşlenecek dosya sayısı: {total_count}")

        for item in items:
            self.stdout.write(f" > [{item.id}] {item.file_name} işleniyor...", ending='')
            
            try:
                if not item.file_path or not os.path.exists(item.file_path):
                    self.stdout.write(self.style.ERROR(" DOSYA BULUNAMADI (Atlanıyor)"))
                    continue

                embedding = None
                
                # Resim mi?
                if item.file_type == 'image' or item.file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    embedding = ai_service.get_image_embedding(item.file_path)
                    
                # Metin/Kod mu?
                elif item.file_type in ['text', 'pdf', 'code', 'document']:
                    embedding = ai_service.get_text_embedding(item.file_name) # Şimdilik isminden

                elif item.file_type == 'video' or item.file_name.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                    
                    # Önce videonun genel bir vektörü var mı diye bak (thumbnail'den vb.)
                    # Yoksa ilk kareyi kapak resmi yapabiliriz ama asıl olay VideoFrame tablosunda.
                    
                    frames = ai_service.analyze_video_content(item.file_path, interval_seconds=10) # 10 saniyede bir kare al
                    
                    if frames:
                        # Ana memory item'a ilk karenin vektörünü koy (Genel arama için)
                        item.vector_embedding = frames[0]['embedding'].tobytes()
                        item.save()
                        
                        # Alt kareleri VideoFrame tablosuna kaydet
                        from memory.models import VideoFrame # Import etmeyi unutma
                        
                        # Eskileri temizle (duplicate olmasın)
                        VideoFrame.objects.filter(memory_item=item).delete()
                        
                        for frame in frames:
                            VideoFrame.objects.create(
                                memory_item=item,
                                timestamp=frame['timestamp'],
                                vector_embedding=frame['embedding'].tobytes()
                            )
                        
                        self.stdout.write(self.style.SUCCESS(f" OK (Video: {len(frames)} kare)"))
                    else:
                        self.stdout.write(self.style.WARNING(" Video işlendi ama kare alınamadı."))

                if embedding is not None:
                    item.vector_embedding = embedding.tobytes()
                    item.save()
                    dims = embedding.shape[0]
                    self.stdout.write(self.style.SUCCESS(f" OK (Vektör: {dims})"))
                else:
                    self.stdout.write(self.style.ERROR(" BAŞARISIZ (Model None döndü)"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f" HATA: {e}"))

        self.stdout.write(self.style.SUCCESS('\n✅ İşlem Tamamlandı.'))

    def sync_files_from_disk(self):
        """Diskteki dosyaları tarayıp MemoryItem tablosuna ekler."""
        uploads_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
        
        if not os.path.exists(uploads_dir):
            self.stdout.write(self.style.WARNING(f"Upload klasörü bulunamadı: {uploads_dir}"))
            return

        # Bellek katmanını al
        default_tier, _ = MemoryTier.objects.get_or_create(name="short_term")

        # Klasörleri gez (uploads/USER_ID/DOSYA)
        for user_id in os.listdir(uploads_dir):
            user_path = os.path.join(uploads_dir, user_id)
            
            # Bu klasör ismi bir User ID mi?
            if os.path.isdir(user_path) and user_id.isdigit():
                try:
                    user = User.objects.get(id=int(user_id))
                except User.DoesNotExist:
                    continue

                for filename in os.listdir(user_path):
                    file_path = os.path.join(user_path, filename)
                    
                    if os.path.isfile(file_path):
                        # Veritabanında var mı kontrol et
                        exists = MemoryItem.objects.filter(file_name=filename, user=user).exists()
                        
                        if not exists:
                            # Dosya türünü tahmin et
                            mime_type, _ = mimetypes.guess_type(file_path)
                            file_type = 'unknown'
                            if mime_type:
                                if mime_type.startswith('image'): file_type = 'image'
                                elif mime_type.startswith('text'): file_type = 'text'
                                elif mime_type.startswith('video'): file_type = 'video'
                            
                            # --- DÜZELTME BURADA ---
                            # Dosya boyutunu alıp 'original_size' olarak kaydediyoruz
                            file_size_bytes = os.path.getsize(file_path)

                            MemoryItem.objects.create(
                                user=user,
                                file_name=filename,
                                file_path=file_path,
                                file_type=file_type,
                                original_size=file_size_bytes, # <-- Zorunlu alan eklendi
                                memory_tier=default_tier
                            )
                            self.stdout.write(self.style.SUCCESS(f"  + Yeni dosya eklendi: {filename}"))