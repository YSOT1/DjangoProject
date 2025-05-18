from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from .models import ChatMessage
from .services import ChatbotService
from utilisateurs.models import Patient
import logging

logger = logging.getLogger(__name__)

@login_required
def chat_interface(request):
    """View for the chat interface."""
    try:
        if request.session['role'] != 'patient':
            messages.error(request, 'Access denied')
            return redirect('signin')
        
        patient = Patient.objects.get(utilisateur_id=request.session['user_id'])
        chat_messages = ChatMessage.objects.filter(patient=patient).order_by('created_at')
        
        context = {
            'chat_messages': chat_messages,
            'patient': patient
        }
        return render(request, 'chat_interface.html', context)
        
    except Exception as e:
        logger.error(f"Error in chat_interface: {str(e)}")
        messages.error(request, 'Error loading chat interface')
        return redirect('patientDashboard')

@login_required
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

@login_required
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
