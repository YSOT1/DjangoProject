from django.db import models
from django.utils import timezone

# Create your models here.
class Appointement(models.Model):
    STATUS_CHOICES = [
        ('pending_payment', 'Pending Payment'),
        ('upcoming', 'Upcoming'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]
    
    id = models.AutoField(primary_key=True)
    patient = models.ForeignKey("utilisateurs.Patient", on_delete=models.CASCADE)
    doctor = models.ForeignKey("utilisateurs.Doctor", on_delete=models.CASCADE)
    date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_payment')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Appointment: {self.patient} with Dr. {self.doctor} on {self.date}"

    class Meta:
        ordering = ['date']
    