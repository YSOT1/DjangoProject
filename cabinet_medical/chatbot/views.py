from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import ChatMessage, ChatSession
from .services import ChatbotService
from utilisateurs.models import Patient, Doctor
from utilisateurs.views import custom_login_required
import google.generativeai as genai
import json
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

# Initialize the Google Generative AI client
# Note: In production, use environment variables for the API key
genai.configure(api_key="your-api-key")

# List available models
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            logger.info(f"Available model: {m.name}")
except Exception as e:
    logger.error(f"Error listing models: {str(e)}")

# Medical context prompts
MEDICAL_CONTEXT = """
You are a medical assistant AI in a medical cabinet. Your role is to:
1. Provide general medical information and guidance
2. Help patients understand their conditions and treatments
3. Assist with appointment scheduling and medical record inquiries
4. Offer basic health advice and wellness tips
5. Direct patients to appropriate medical professionals when needed

Important guidelines:
- Always maintain patient confidentiality
- Never provide specific medical diagnoses
- Encourage patients to consult their doctors for serious concerns
- Be clear about the limitations of AI medical advice
- Use simple, understandable language
- Be empathetic and professional
"""

@custom_login_required
def chat_interface(request):
    """Render the chat interface."""
    return render(request, 'chatbot/chat.html')

@custom_login_required
def send_message(request):
    """View for handling message sending and receiving AI responses."""
    try:
        if request.session['role'] != 'patient':
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        if request.method != 'POST':
            return JsonResponse({'error': 'Invalid request method'}, status=405)
        
        message = request.POST.get('message', '').strip()
        if not message:
            return JsonResponse({'error': 'Message cannot be empty'}, status=400)
        
        patient = Patient.objects.get(utilisateur_id=request.session['user_id'])
        
        # Save patient's message
        ChatMessage.objects.create(
            patient=patient,
            message=message,
            is_from_patient=True
        )
        
        # Check for emergency
        if ChatbotService.is_emergency(message):
            response = ("⚠️ This appears to be a medical emergency. "
                       "Please call emergency services (911) immediately or "
                       "go to the nearest emergency room.")
        else:
            # Get AI response
            response = ChatbotService.get_response(message)
        
        # Save AI's response
        ChatMessage.objects.create(
            patient=patient,
            message=response,
            is_from_patient=False
        )
        
        return JsonResponse({
            'response': response,
            'is_emergency': ChatbotService.is_emergency(message)
        })
        
    except Exception as e:
        logger.error(f"Error in send_message: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@custom_login_required
def clear_chat(request):
    """View for clearing chat history."""
    try:
        if request.session['role'] != 'patient':
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        if request.method != 'POST':
            return JsonResponse({'error': 'Invalid request method'}, status=405)
        
        patient = Patient.objects.get(utilisateur_id=request.session['user_id'])
        ChatMessage.objects.filter(patient=patient).delete()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        logger.error(f"Error in clear_chat: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@custom_login_required
def process_message(request):
    """Process incoming chat messages and generate AI responses."""
    try:
        data = json.loads(request.body)
        user_message = data.get('message')
        
        if not user_message:
            return JsonResponse({'error': 'No message provided'}, status=400)
        
        logger.info(f'AI received message: {user_message}')
        
        # Prepare the prompt with medical context
        prompt = f"""As a medical assistant in a medical cabinet, provide a helpful and professional response to: {user_message}
        
        Guidelines:
        - Maintain patient confidentiality
        - Don't provide specific medical diagnoses
        - Encourage consulting doctors for serious concerns
        - Use simple, understandable language
        - Be empathetic and professional"""
        
        # Generate response using Gemini
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        
        bot_response = response.text
        logger.info(f'AI bot response: {bot_response}')
        
        return JsonResponse({'response': bot_response})
        
    except Exception as e:
        logger.error(f'Error: {str(e)}')
        return JsonResponse({'error': 'An error occurred'}, status=500)

@custom_login_required
def get_chat_history(request):
    """Retrieve chat history for the current user."""
    try:
        user = request.user
        chat_messages = ChatMessage.objects.filter(user=user).order_by('created_at')
        
        chat_history = [{
            'message': msg.message,
            'response': msg.response,
            'timestamp': msg.created_at.isoformat()
        } for msg in chat_messages]
        
        return JsonResponse({'chat_history': chat_history})
        
    except Exception as e:
        logger.error(f"Error retrieving chat history: {str(e)}")
        return JsonResponse({'error': 'Error retrieving chat history'}, status=500)
