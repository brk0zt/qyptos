# memory/management/commands/generate_embeddings.py (Sync + Generate)
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model
from memory.models import MemoryItem, MemoryTier
from memory.services.ai_services import AIService
import os
import mimetypes
import numpy as np

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

                    try:
                        import face_recognition
                        from memory.models import Person, FaceEncoding
                    except ImportError:
                        self.stdout.write(self.style.WARNING("Face recognition modülü eksik."))
                        continue

                    faces = ai_service.detect_and_encode_faces(item.file_path)
                    
                    if faces:
                        self.stdout.write(f" -> {len(faces)} yüz bulundu. ", ending='')
                        
                        # Mevcut kayıtlı kişilerin yüz imzalarını (encoding) belleğe al
                        # (Gerçek prodüksiyonda bu sorgu optimize edilmeli, şimdilik döngü içinde yapıyoruz)
                        known_encodings = []
                        known_people_ids = []
                        
                        # Veritabanındaki her kişiden 1 örnek yüz al
                        for person in Person.objects.all():
                            # O kişinin ilk yüz kaydını referans al
                            sample_face = person.faces.first()
                            if sample_face:
                                # Binary veriyi numpy array'e çevir (float64 önemli!)
                                known_encodings.append(
                                    np.frombuffer(sample_face.encoding, dtype=np.float64)
                                )
                                known_people_ids.append(person.id)

                        # Bulunan her yeni yüz için:
                        for face in faces:
                            current_encoding = face['encoding'] # Zaten numpy array geliyor
                            found_person = None

                            # Eğer veritabanında kayıtlı kimse varsa karşılaştır
                            if known_encodings:
                                # face_recognition kütüphanesi ile karşılaştırma yap
                                # tolerance=0.6 standarttır. Daha düşük (0.5) daha katı, daha yüksek (0.7) daha gevşek.
                                matches = face_recognition.compare_faces(known_encodings, current_encoding, tolerance=0.6)
                                
                                if True in matches:
                                    # İlk eşleşen kişiyi al
                                    first_match_index = matches.index(True)
                                    person_id = known_people_ids[first_match_index]
                                    found_person = Person.objects.get(id=person_id)
                                    # print(f"   [Tanındı]: {found_person.name}")

                            # Eşleşme yoksa YENİ KİŞİ oluştur
                            if found_person is None:
                                found_person = Person.objects.create(
                                    user=item.user,
                                    name=f"Kişi #{Person.objects.count() + 1}", # Geçici İsim
                                    cover_photo=item.file_path # Bu fotoğrafı kapak yap
                                )
                                # Yeni kişiyi hafızadaki listeye de ekle ki aynı fotodaki diğer yüzlerle karışmasın
                                known_encodings.append(current_encoding)
                                known_people_ids.append(found_person.id)
                                # print(f"   [Yeni]: {found_person.name}")

                            # Yüzü veritabanına kaydet ve kişiyle ilişkilendir
                            FaceEncoding.objects.create(
                                person=found_person,
                                memory_item=item,
                                encoding=current_encoding.tobytes(), # Binary olarak kaydet
                                location_top=face['location'][0],
                                location_right=face['location'][1],
                                location_bottom=face['location'][2],
                                location_left=face['location'][3]
                            )

                        self.stdout.write(self.style.SUCCESS("İşlendi (Gruplandı)."))
                    
                # Metin/Kod mu?
                elif item.file_type in ['text', 'pdf', 'code', 'document'] or \
                     item.file_name.lower().endswith(('.txt', '.md', '.py', '.js', '.pdf', '.docx')):
                    
                    self.stdout.write(f" Metin Okunuyor: {item.file_name} ", ending='')
                    
                    # 1. İçeriği Çıkar
                    content = ai_service.extract_text_from_file(item.file_path)
                    
                    if content and len(content.strip()) > 10:
                        # 2. İçeriği Özetle/Kaydet (İleride RAG için kullanacağız)
                        item.content_summary = content[:500] + "..." # Veritabanında özet olarak sakla
                        
                        # 3. Vektör Oluştur (Dosya Adı + İçerik Kombinasyonu)
                        # Hem ismini hem içeriğini temsil eden hibrit bir vektör
                        combined_text = f"{item.file_name} : {content[:1000]}"
                        embedding = ai_service.get_text_embedding(combined_text)
                        
                        self.stdout.write(f"-> {len(content)} karakter okundu. ", ending='')
                    else:
                        # İçerik okunamadıysa veya boşsa sadece isminden üret
                        self.stdout.write("(İçerik boş, isimden üretiliyor) ", ending='')
                        embedding = ai_service.get_text_embedding(item.file_name)

                    if embedding is not None:
                        item.vector_embedding = embedding.tobytes()
                        item.save()
                        self.stdout.write(self.style.SUCCESS("OK"))
                    else:
                        self.stdout.write(self.style.ERROR("Vektör Hatası"))

                elif item.file_type == 'video' or item.file_name.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):

                    self.stdout.write(f" Video Analizi: {item.file_name} ", ending='')

                    # Önce videonun genel bir vektörü var mı diye bak (thumbnail'den vb.)
                    # Yoksa ilk kareyi kapak resmi yapabiliriz ama asıl olay VideoFrame tablosunda.
                    
                    frames = ai_service.analyze_video_content(item.file_path, interval_seconds=5) # 5 saniyede bir kare al

                    # 2. Ses Analizi (YENİ) - Whisper Devreye Giriyor
                    transcript = ai_service.transcribe_audio(item.file_path)
                    
                    # Transkripti kaydet
                    if transcript:
                        item.content_summary = f"[VIDEO TRANSCRIPT]: {transcript[:1000]}"
                        self.stdout.write(f" + Ses Okundu ", ending='')

                    if frames:
                        # Ana memory item'a ilk karenin vektörünü koy (Genel arama için)
                        embedding = frames[0]['embedding']
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

                elif item.file_name.lower().endswith(('.mp3', '.wav', '.m4a', '.ogg')):
                    self.stdout.write(f" Ses Analizi: {item.file_name} ", ending='')
                    
                    transcript = ai_service.transcribe_audio(item.file_path)
                    
                    if transcript:
                        item.content_summary = transcript[:1000]
                        # Metin embeddingi oluştur (İsminden değil, konuşmadan)
                        combined = f"{item.file_name} : {transcript[:500]}"
                        embedding = ai_service.get_text_embedding(combined)
                        self.stdout.write(self.style.SUCCESS(" OK (Speech-to-Text)"))
                    else:
                        embedding = ai_service.get_text_embedding(item.file_name)
                        self.stdout.write(" (Sessiz)")

                if embedding is not None:
                    # Numpy array ise bytes'a çevir
                    if isinstance(embedding, np.ndarray):
                        item.vector_embedding = embedding.tobytes()
                    else:
                        item.vector_embedding = embedding # Zaten bytes ise
                        
                    item.save()
                    self.stdout.write(self.style.SUCCESS(" OK"))
                else:
                    self.stdout.write(self.style.ERROR(" BAŞARISIZ (Vektör yok)"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f" HATA: {e}"))
                import traceback
                traceback.print_exc()

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