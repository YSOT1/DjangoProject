from django.db import models
from utilisateurs.models import Patient
from django.utils import timezone

class ChatMessage(models.Model):
    """Model for storing chat messages between patients and the AI chatbot."""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='chat_messages')
    message = models.TextField()
    is_from_patient = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{'Patient' if self.is_from_patient else 'AI'} message at {self.created_at}"
