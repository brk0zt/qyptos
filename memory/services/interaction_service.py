# memory/services/interaction_service.py
import logging
import json
from django.utils import timezone
from .ai_services import AIService
from .advanced_memory_manager import AdvancedMemoryManager
from ..models import UserActivity

logger = logging.getLogger(__name__)

class InteractionService:
    def __init__(self, user):
        self.user = user
        self.memory_manager = AdvancedMemoryManager(user)

    def process_message(self, message: str, context: dict = None):
        """
        Kullanıcı mesajını işler, veriyi JSON uyumlu hale getirir ve yanıt döner.
        """
        print(f"🤖 AI İşleniyor: '{message}'")
        
        response_data = {
            "reply": "İşlem başlatılamadı.",
            "relevant_memories": [],
            "action_performed": "search"
        }

        try:
            # 1. Hafızada Ara
            search_results = self.memory_manager.semantic_search(query=message, limit=5)
            
            # 2. Veri Temizliği (Serialization) - KRİTİK ADIM
            # Numpy verilerini (float32 vb.) standart Python tiplerine çevirmezsek JSON patlar.
            clean_results = []
            for item in search_results:
                clean_item = {
                    'id': item.get('id'),
                    'file_name': str(item.get('file_name', '')),
                    'file_type': str(item.get('file_type', 'unknown')),
                    'file_path': str(item.get('file_path', '')),
                    'similarity_score': float(item.get('similarity_score', 0.0)), # float'a zorla
                    'ranking_score': float(item.get('ranking_score', 0.0)),       # float'a zorla
                    'summary': str(item.get('summary') or "Özet yok."),
                    'thumbnail': str(item.get('thumbnail', ''))
                }
                clean_results.append(clean_item)

            # 3. Aktivite Kaydet
            UserActivity.objects.create(
                user=self.user,
                activity_type='ai_interaction',
                application='Qyptos Chat',
                window_title=f"Sorgu: {message}",
                timestamp=timezone.now(),
                context={'query': message, 'results': len(clean_results)}
            )

            # 4. Yanıt Oluştur
            if not clean_results:
                response_data["reply"] = f"Üzgünüm, hafızamda '{message}' ile ilgili bir şey bulamadım."
                response_data["relevant_memories"] = []
            else:
                count = len(clean_results)
                top_file = clean_results[0]['file_name']
                response_data["reply"] = f"Buldum! '{message}' ile ilgili {count} dosya var. En yakını: **{top_file}**"
                response_data["relevant_memories"] = clean_results

            # DEBUG: Terminale ne gönderdiğimizi basalım
            print(f"📤 FRONTEND'E GİDEN VERİ: {json.dumps(response_data, ensure_ascii=False)[:200]}...")
            
            return response_data

        except Exception as e:
            logger.error(f"Interaction error: {e}")
            import traceback
            traceback.print_exc() # Hatanın tam yerini göster
            return {
                "reply": f"Bir hata oluştu: {str(e)}",
                "relevant_memories": [],
                "error": str(e)
            }