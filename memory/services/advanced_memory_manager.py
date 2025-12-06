# memory/services/advanced_memory_manager.py
from django.utils import timezone
from datetime import timedelta
import numpy as np
from .compression_engine import SemanticCompressionEngine
import logging
from .ai_services import AIService # Varsayýlan olarak AI Servisini import ediyoruz
from django.db.models import Q, F
from ..models import MemoryItem, UserActivity, TimelineEvent, UserMemoryProfile


logger = logging.getLogger(__name__)

class AdvancedMemoryManager:
    """
    Hafıza yönetiminin çekirdeği. Semantik arama, katman geçişleri ve timeline füzyonu
    gibi karmaşık işlemleri yönetir.
    """
    def __init__(self, user):
        self.user = user
        self.compression_engine = SemanticCompressionEngine()
        self.ai_service = AIService()
        self.compression_engine = SemanticCompressionEngine()
        self.user_profile, created = UserMemoryProfile.objects.get_or_create(user=user)
    
    def semantic_search(self, query, file_type=None, limit=20)-> list:
        """
        Kullanıcının sorgusunu vektöre dönüştürür ve en yakın hafıza öğelerini bulur, 
        bağlamsal verilerle yeniden puanlar.
        """
        if not query:
            return []

            try:
            # 1. Sorguyu vektöre dönüştür
                query_vector = self.ai_service.get_text_embedding(query)
            
                if query_vector is None:
                    logger.warning(f"Kullanıcı {self.user.username} için vektör oluşturulamadı.")
                    return []

                recent_items = MemoryItem.objects.filter(
                user=self.user,
                expires_at__gte=timezone.now() - timedelta(days=30) # Son 30 gün
                )
            
                results = []
            
                for item in recent_items:
                # Basit bir numpy benzerlik hesaplaması (Sadece simülasyon amaçlı)
                    item_vector = np.frombuffer(item.vector_embedding) if item.vector_embedding else None
                    if item_vector is not None:
                    # Cosine Benzerliği (Varsayım: item_vector ve query_vector aynı boyutta)
                        similarity = np.dot(item_vector, query_vector) / (np.linalg.norm(item_vector) * np.linalg.norm(query_vector))
                    
                    # 3. Yeniden Puanlama (Re-Ranking): Bağlamı dahil et
                    # Bağlamsal Skor = (Erişim Sayısı Ağırlığı * log(access_count+1)) + (Benzerlik Skoru)
                        context_score = 0.5 * np.log(item.access_count + 1) + 1.5 * similarity
                    
                        results.append({
                        'item': item,
                        'similarity_score': float(similarity),
                        'ranking_score': float(context_score),
                        })

                # 4. En yüksek puana göre sırala ve limit uygula
                    final_results = sorted(results, key=lambda x: x['ranking_score'], reverse=True)[:limit]
            
                    return [res['item'].to_dict() for res in final_results] # to_dict() metodu models.py'de varsayýlýr

            except Exception as e:
                logger.error(f"Semantic search hatası: {e}")
                return []

        from ..models import MemoryItem
        
        try:
            memories = MemoryItem.objects.filter(
                user=self.user,
                expires_at__gt=timezone.now()
            )
            
            if file_type:
                memories = memories.filter(file_type=file_type)
            
            # Basit benzerlik hesaplama
            results = []
            for memory in memories:
                score = self.calculate_similarity(query, memory)
                if score > 0.1:
                    results.append({
                        'memory_item': memory,
                        'file_path': memory.file_path,
                        'file_type': memory.file_type,
                        'similarity_score': score,
                        'last_accessed': memory.last_accessed,
                        'access_count': memory.access_count,
                        'content_summary': memory.content_summary
                    })
            
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Semantic search hatasi: {e}")
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