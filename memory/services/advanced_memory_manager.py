# memory/services/advanced_memory_manager.py
from django.utils import timezone
from datetime import timedelta
import numpy as np
import logging
from django.db.models import Q, F
from django.db import models
# Modellerini doğru yerden import ettiğine emin ol
from ..models import MemoryItem, UserActivity, TimelineEvent, UserMemoryProfile, MemoryTier
from .ai_services import AIService 
from .compression_engine import SemanticCompressionEngine
from django.db import models
from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)

class AdvancedMemoryManager:
    """
    Hafıza yönetiminin çekirdeği.
    """
    def __init__(self, user):
        self.user = user
        self.ai_service = AIService()
        self.compression_engine = SemanticCompressionEngine()
        # Profil yoksa oluştur
        self.user_profile, _ = UserMemoryProfile.objects.get_or_create(user=user)
        self.translator = GoogleTranslator(source='auto', target='en')

    def semantic_search(self, query: str, file_type: str = None, limit: int = 10) -> list:
        print(f"\n🔎 AKILLI ARAMA BAŞLADI: '{query}' (Kullanıcı ID: {self.user.id})")
        
        if not query:
            return []

        results_dict = {}

        try:

            try:
                translated_query = self.translator.translate(query)
                print(f"   🌍 Dil Algılandı ve Çevrildi: '{query}' -> '{translated_query}'")
            except Exception as e:
                print(f"   ⚠️ Çeviri servisi ulaşılamadı, orijinal dil kullanılıyor. Hata: {e}")
                translated_query = query

            # --- 1. PROMPT ENGINEERING (Sorgu Zenginleştirme) ---
            # Model "kedi" yerine "A photo of kedi" cümlesini daha iyi anlar.
            # Bu, vektör skorlarını (cosine similarity) yukarı çeker.
            clean_query = translated_query.lower()
            
            if "photo of" in clean_query or "picture of" in clean_query:
                visual_prompt = translated_query # Kullanıcının yazdığını olduğu gibi kullan
            else:
                visual_prompt = f"A photo of {translated_query}" # Biz ekleyelim
            
            print(f"   ℹ️  AI Prompt: '{visual_prompt}'")

            # Embeddingleri Hazırla
            # Metin araması için orijinal sorguyu, görsel araması için prompt'u kullanıyoruz
            query_vector_text = self.ai_service.get_text_embedding(translated_query) 
            query_vector_clip = self.ai_service.get_clip_text_embedding(visual_prompt)

            # --- 2. ADAY HAVUZUNU OLUŞTURMA ---
            # Sadece vektörü olanları al (Vektörsüz dosya "kör" dosyadır)
            # İsim eşleşmesini burada filtrelemiyoruz, onu puanlarken kullanacağız.
            filters = Q(user=self.user) & Q(vector_embedding__isnull=False)
            if file_type:
                filters &= Q(file_type=file_type)

            candidates = MemoryItem.objects.filter(filters)
            print(f"   -> Taranacak aday sayısı: {candidates.count()}")

            # --- 3. PUANLAMA DÖNGÜSÜ ---
            for item in candidates:
                item_vector = np.frombuffer(item.vector_embedding, dtype=np.float32)
                
                current_query_vector = None
                if item_vector.shape[0] == 384: current_query_vector = query_vector_text
                elif item_vector.shape[0] == 512: current_query_vector = query_vector_clip
                
                if current_query_vector is None or item_vector.shape != current_query_vector.shape:
                    continue

                # A. TEMEL SKOR (Cosine Similarity)
                raw_score = np.dot(item_vector, current_query_vector) / (
                    np.linalg.norm(item_vector) * np.linalg.norm(current_query_vector)
                )
                raw_score = float(raw_score)

                # B. EŞİK KONTROLÜ (Gürültü Filtresi)
                # 0.21 altı genellikle alakasızdır.
                if raw_score < 0.21:
                    continue

                # C. ÜSTEL PUANLAMA (Exponential Scoring)
                # Makası açmak için 4. kuvvetini alıyoruz.
                # Örnek: Webcam(0.24)^4 = 0.0033 vs Bebek(0.28)^4 = 0.0061 (2 kat fark!)
                display_score = pow(raw_score, 4) * 150

                # D. KELİME BONUSU (Sadece %5)
                # Orijinal Türkçe isimde geçiyorsa küçük bir jest yap.
                keyword_bonus = 0.0
                if query.lower() in item.file_name.lower():
                    keyword_bonus = 0.05
                    display_score += keyword_bonus

                # Tavan puan %99
                display_score = min(display_score, 0.99)

                # --- URL DÜZELTME ---
                if "uploads" not in item.file_name:
                    safe_url = f"/media/uploads/{item.user.id}/{item.file_name}"
                else:
                    safe_url = f"/media/{item.file_name}"

                # Sadece yüksek skorlu adayları loga bas (Kirlilik olmasın)
                if display_score > 0.50:
                    print(f"      + Güçlü Aday: {item.file_name[:20]}... | Ham: {raw_score:.3f} | Sonuç: %{display_score*100:.1f}")

                results_dict[item.id] = {
                    'id': item.id,
                    'file_name': item.file_name,
                    'file_type': item.file_type,
                    'file_path': item.file_path,
                    'similarity_score': display_score,
                    'ranking_score': display_score,
                    'summary': item.content_summary,
                    'thumbnail': safe_url
                }

            final_results = list(results_dict.values())
            final_results.sort(key=lambda x: x['ranking_score'], reverse=True)
            
            print(f"✅ TOPLAM SONUÇ: {len(final_results)} dosya bulundu.\n")
            return final_results[:limit]

        except Exception as e:
            logger.error(f"Semantic search hatası: {e}")
            print(f"❌ ARAMA HATASI: {e}")
            return []
    
    def get_fused_timeline(self, days: int = 7, limit: int = 100) -> list:
        """
        TimelineEvent ve kritik UserActivity'leri birleştirip zamana ve öneme göre sıralar.
        """
        time_threshold = timezone.now() - timedelta(days=days)

        # 1. TimelineEvent'leri al (Doğrudan Recall olayları)
        events = TimelineEvent.objects.filter(
            user=self.user,
            timestamp__gte=time_threshold
        ).values('timestamp', 'event_type', 'title', 'description', 'confidence_score')
        
        timeline = []

        # 2. Kritik UserActivity'leri al (örneğin dosya açma/kaydetme)
        critical_activities = UserActivity.objects.filter(
            user=self.user,
            timestamp__gte=time_threshold
        ).filter(
            activity_type__in=['file_open', 'file_save', 'app_switch']
        ).values('timestamp', 'activity_type', 'window_title', 'context')
        
        # 3. Her iki listeyi tek bir listede birleştir
        for event in events:
            event['source'] = 'TimelineEvent'
            event['sort_key'] = event['timestamp']
            timeline.append(event)
            
        for activity in critical_activities:
            activity['source'] = 'UserActivity'
            activity['event_type'] = activity.pop('activity_type')
            activity['title'] = f"Aktivite: {activity['window_title']}"
            activity['sort_key'] = activity['timestamp']
            timeline.append(activity)

        # 4. Birleştirilmiş listeyi zamana göre sırala (en yeniden en eskiye) ve limit uygula
        timeline_sorted = sorted(timeline, key=lambda x: x['sort_key'], reverse=True)
        
        return timeline_sorted[:limit]

    # --- 3. Hafıza İstatistikleri ---
    def get_user_stats(self) -> dict:
        """
        Kullanıcının hafıza kullanımını ve katman dağılımını hesaplar.
        """
        total_items = MemoryItem.objects.filter(user=self.user).count()
        tier_distribution = MemoryItem.objects.filter(user=self.user).values('memory_tier__name').annotate(count=models.Count('memory_tier'))
        
        # quota bilgisini profilden al
        quota_mb = self.user_profile.memory_quota_mb
        used_mb = self.user_profile.total_memory_used_mb
        
        return {
            'total_items': total_items,
            'memory_quota_mb': quota_mb,
            'memory_used_mb': used_mb,
            'memory_remaining_mb': quota_mb - used_mb,
            'tier_distribution': list(tier_distribution),
        }

    # --- 4. Periyodik İşlem: Katman Geçişi ---
    def check_and_promote_memories(self):
        """
        Süresi dolmak üzere olan 'short_term' öğeleri 'long_term' katmanına taşır ve sıkıştırır.
        Bu metod memory_maintenance.py tarafından çağrılacaktır.
        """
        one_day_ago = timezone.now() - timedelta(days=1)
        
        # Süresi dolan veya dolmak üzere olan kısa süreli öğeleri bul
        items_to_promote = MemoryItem.objects.filter(
            user=self.user,
            memory_tier__name='short_term',
            expires_at__lte=timezone.now() + timedelta(hours=6) # Son 6 saat içinde dolacaklar
        )
        
        for item in items_to_promote:
            # 1. Sıkıştırma (Yalnızca uzun süreliye geçmeden önce)
            # BinaryField olduğu için sıkıştırma sonucunu tekrar BinaryField olarak almalıyız
            if not item.compressed_embedding:
                try:
                    # Sıkıştırma motorunu kullanarak vektörün boyutunu azalt
                    compressed_data = self.compression_engine.compress_embedding(item.vector_embedding)
                    item.compressed_embedding = compressed_data
                except Exception as e:
                    logger.error(f"Sıkıştırma hatası ({item.id}): {e}")
            
            # 2. Katmanı 'long_term' olarak güncelle ve expires_at'i sıfırla
            long_term_tier = MemoryTier.objects.get(name='long_term')
            item.memory_tier = long_term_tier
            item.expires_at = None # save() metodu yeniden hesaplayacak
            item.save()
            
            logger.info(f"MemoryItem {item.id} uzun süreli belleğe taşındı ve sıkıştırıldı.")

    def calculate_similarity(self, query, memory_item):
        """Basit benzerlik hesaplama"""
        query_terms = query.lower().split()
        
        score = 0
        text_to_check = [
            memory_item.file_name.lower(),
            ' '.join(memory_item.semantic_tags or []),
            memory_item.content_summary or ""
        ]
        
        full_text = ' '.join(text_to_check).lower()
        
        for term in query_terms:
            if term in full_text:
                score += 0.1
        
        # Erişim sıklığı ve yakınlığı ile artır
        recency_bonus = self.calculate_recency_bonus(memory_item.last_accessed)
        frequency_bonus = min(memory_item.access_count * 0.01, 0.3)
        
        return min(score + recency_bonus + frequency_bonus, 1.0)
    
    def calculate_recency_bonus(self, last_accessed):
        """Son erisime gore bonus puan"""
        hours_ago = (timezone.now() - last_accessed).total_seconds() / 3600
        if hours_ago < 1: return 0.5
        if hours_ago < 24: return 0.3
        if hours_ago < 168: return 0.1
        return 0
    
    def promote_to_long_term(self, memory_item):
        """Kisa sureli bellekten uzun sureli bellege tasi"""
        try:
            from ..models import MemoryTier
            long_term_tier = MemoryTier.objects.get(name='long_term')
            
            # Semantik sıkıştırma uygula
            if memory_item.vector_embedding and self.compression_engine.should_compress(memory_item):
                # Vektör sıkıştırma
                original_vector = np.frombuffer(memory_item.vector_embedding, dtype=np.float32)
                compressed_vector = self.compression_engine.compress_embedding(original_vector)
                memory_item.compressed_embedding = compressed_vector.tobytes()
                
                # Yapısal veri sıkıştırma
                compressed_structural = self.compression_engine.compress_structural_data(
                    memory_item.structural_data
                )
                memory_item.structural_data = compressed_structural
            
            memory_item.memory_tier = long_term_tier
            memory_item.save()
            
        except Exception as e:
            logger.error(f"Promote to long term hatasi: {e}")
    
    def get_timeline_events(self, days=7, limit=50):
        """Timeline events getir"""
        start_date = timezone.now() - timedelta(days=days)
        
        from ..models import MemoryItem, UserActivity
        
        events = []
        
        # Memory item'ları
        memories = MemoryItem.objects.filter(
            user=self.user,
            created_at__gte=start_date
        ).select_related('memory_tier')[:limit//2]
        
        for memory in memories:
            events.append({
                'type': 'memory',
                'timestamp': memory.created_at,
                'title': f"{memory.file_name}",
                'description': f"{memory.file_type} - {memory.memory_tier.name}",
                'thumbnail': memory.thumbnail_path,
                'metadata': {
                    'file_path': memory.file_path,
                    'memory_tier': memory.memory_tier.name,
                    'access_count': memory.access_count
                }
            })
        
        # User activities
        activities = UserActivity.objects.filter(
            user=self.user,
            timestamp__gte=start_date
        )[:limit//2]
        
        for activity in activities:
            events.append({
                'type': 'activity',
                'timestamp': activity.timestamp,
                'title': f"{activity.activity_type}",
                'description': activity.target_file or activity.application,
                'metadata': {
                    'activity_type': activity.activity_type,
                    'application': activity.application,
                    'window_title': activity.window_title
                }
            })
        
        events.sort(key=lambda x: x['timestamp'], reverse=True)
        return events[:limit]