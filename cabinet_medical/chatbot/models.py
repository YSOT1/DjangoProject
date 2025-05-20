from django.db import models
from utilisateurs.models import Patient, Doctor, Utilisateurs

class ChatMessage(models.Model):
    """Model for storing chat messages."""
    user = models.ForeignKey(Utilisateurs, on_delete=models.CASCADE)
    message = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Chat message from {self.user.username} at {self.created_at}"

class ChatSession(models.Model):
    """Model for storing chat sessions."""
    user = models.ForeignKey(Utilisateurs, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    messages = models.ManyToManyField(ChatMessage, related_name='sessions')
    
    class Meta:
        ordering = ['-started_at']
        
    def __str__(self):
        return f"Chat session for {self.user.username} started at {self.started_at}"
