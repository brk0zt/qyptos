# memory/views/chat_views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from memory.services.interaction_service import InteractionService

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_with_ai(request):
    """
    Dashboard'daki chatbox'tan gelen mesajları işler.
    """
    user_message = request.data.get('message')
    context = request.data.get('context', {}) # Örn: O an açık olan dosya bilgisi vb.
    
    if not user_message:
        return Response({"error": "Mesaj boş olamaz"}, status=400)
        
    service = InteractionService(request.user)
    response_data = service.process_message(user_message, context)
    
    return Response(response_data)
