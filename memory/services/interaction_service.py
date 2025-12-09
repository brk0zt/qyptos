# memory/services/interaction_service.py
import logging
import json
from django.utils import timezone
from .ai_services import AIService
from .advanced_memory_manager import AdvancedMemoryManager
from ..models import UserActivity
from .homonyms_data import AMBIGUOUS_TERMS

logger = logging.getLogger(__name__)

class InteractionService:
    def __init__(self, user):
        self.user = user
        self.memory_manager = AdvancedMemoryManager(user)
        self.ambiguous_terms = AMBIGUOUS_TERMS
        # --- ŞAİBELİ KELİMELER SÖZLÜĞÜ (HOMONYM DICTIONARY) ---
        # Burayı zamanla genişletebilirsin.
        # Format: 'kelime': [{'text': 'Kullanıcıda görünecek', 'prompt': 'AI'ya gidecek net komut'}]

    def process_message(self, message: str, context: dict = None):
        """
        Kullanıcı mesajını analiz eder, şaibe varsa soru sorar, yoksa arama yapar.
        """
        print(f"🤖 AI İşleniyor: '{message}'")
        
        # 1. ŞAİBE KONTROLÜ (AMBIGUITY CHECK)
        # Mesajı küçük harfe çevir ve temizle
        clean_msg = message.lower().strip()
        
        # Eğer kelime sözlükte varsa ve kullanıcı henüz bir seçim yapmadıysa (yani prompt karmaşık değilse)
        if clean_msg in self.ambiguous_terms:
            ambiguity_data = self.ambiguous_terms[clean_msg]
            
            print(f"⚠️ Şaibe Tespit Edildi: '{clean_msg}'. Kullanıcıya soruluyor.")
            
            return {
                "reply": ambiguity_data['question'],
                "relevant_memories": [],
                "suggestions": ambiguity_data['options'], # Frontend'e butonları gönderiyoruz
                "action_performed": "ask_clarification"
            }

        # 2. NORMAL ARAMA SÜRECİ (Şaibe yoksa veya çözüldüyse)
        response_data = {
            "reply": "İşlem başlatılamadı.",
            "relevant_memories": [],
            "suggestions": [],
            "action_performed": "search"
        }

        try:
            # Hafızada Ara (AdvancedMemoryManager zaten translate yapıyor, o yüzden 'search_query' İngilizce olsa da sorun yok)
            search_results = self.memory_manager.semantic_search(query=message, limit=5)
            
            # Veri Temizliği
            clean_results = []
            for item in search_results:
                clean_item = {
                    'id': item.get('id'),
                    'file_name': str(item.get('file_name', '')),
                    'file_type': str(item.get('file_type', 'unknown')),
                    'file_path': str(item.get('file_path', '')),
                    'similarity_score': float(item.get('similarity_score', 0.0)),
                    'ranking_score': float(item.get('ranking_score', 0.0)),
                    'summary': str(item.get('summary') or "Özet yok."),
                    'thumbnail': str(item.get('thumbnail', ''))
                }
                clean_results.append(clean_item)

            # Aktivite Kaydet
            UserActivity.objects.create(
                user=self.user,
                activity_type='ai_interaction',
                application='Qyptos Chat',
                window_title=f"Sorgu: {message}",
                timestamp=timezone.now(),
                context={'query': message, 'results': len(clean_results)}
            )

            # Yanıt Oluştur
            if not clean_results:
                response_data["reply"] = f"Üzgünüm, hafızamda '{message}' ile ilgili net bir sonuç bulamadım."
            else:
                count = len(clean_results)
                top_result = clean_results[0]
                top_file = top_result['file_name']  # ← DÜZELTME: top_file değişkeni tanımlandı
                
                reply_text = f"Buldum! '{message}' ile ilgili {count} sonuç var. En yakını: **{top_file}**"
                
                if len(message.split()) > 2 or "?" in message:
                    # En iyi sonucun özetini (içeriğini) al
                    content_context = top_result.get('summary', '')
                    
                    # Eğer içerik varsa ve "Özet yok" değilse
                    if content_context and "Özet yok" not in content_context and len(content_context) > 20:
                        print(f"   🧠 Düşünüyor... ({top_file} üzerinden)")
                        
                        # AI Servisini çağırıp cevap iste
                        answer_data = self.memory_manager.ai_service.answer_question(content_context, message)
                        
                        if answer_data:
                            extracted_answer = answer_data['answer']
                            confidence = answer_data['score']
                            print(f"   💡 Cevap Bulundu: {extracted_answer} (Güven: {confidence:.2f})")
                            
                            if confidence > 0.3: # Güven eşiği
                                reply_text = f"Dosyaya göre sorunuzun cevabı: **{extracted_answer}**\n\n(Kaynak: {top_file})"

                # Video zaman damgası varsa ekle
                if top_result['file_type'] == 'video' and 'saniyesinde' in top_result['summary']:
                    timestamp_info = top_result['summary'].replace("✅ ", "")
                    reply_text += f"\n\n🎯 **{timestamp_info}**"

                response_data["reply"] = reply_text
                response_data["relevant_memories"] = clean_results

            return response_data

        except Exception as e:
            logger.error(f"Interaction error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "reply": f"Bir hata oluştu: {str(e)}",
                "relevant_memories": [],
                "error": str(e)
            }