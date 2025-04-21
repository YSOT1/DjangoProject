from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

class Utilisateur(AbstractUser):
    ROLE_CHOICES = (
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
        ('secretaire', 'Secretaire'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    groups = models.ManyToManyField(
        Group,
        related_name='utilisateur_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='utilisateur_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )

class Patient(models.Model):
    user = models.OneToOneField(Utilisateur, on_delete=models.CASCADE)

class Doctor(models.Model):
    user = models.OneToOneField(Utilisateur, on_delete=models.CASCADE)
    specialite = models.CharField(max_length=100)
    rating = models.FloatField(default=0)

class Secretaire(models.Model):
    user = models.OneToOneField(Utilisateur, on_delete=models.CASCADE)

class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    date = models.DateTimeField()
    status = models.CharField(max_length=20, default='upcoming')

class MedicalReport(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Invoice(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True)
    amount = models.FloatField()
    issued_date = models.DateField(auto_now_add=True)
