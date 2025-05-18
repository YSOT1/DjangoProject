from django.db import models

# Create your models here.
class Utilisateurs(models.Model):
    class Role(models.TextChoices):
        DOCTOR = 'doctor', 'Doctor'
        PATIENT = 'patient', 'Patient'
        SECRETAIRE = 'secretaire', 'Secretaire'
    
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    role = models.CharField(max_length=20, choices=Role.choices)
    
class Secretaire(models.Model):
    id = models.AutoField(primary_key=True)
    utilisateur = models.ForeignKey(Utilisateurs, on_delete=models.CASCADE)
    
class Doctor(models.Model):
    id = models.AutoField(primary_key=True)
    utilisateur = models.ForeignKey(Utilisateurs, on_delete=models.CASCADE)
    specialite = models.CharField(max_length=100)
    immatriculation = models.CharField(max_length=50, unique=True)
    rating = models.IntegerField(default=0)
    
class Patient(models.Model):
    id = models.AutoField(primary_key=True)
    utilisateur = models.ForeignKey(Utilisateurs, on_delete=models.CASCADE)
    birth_date = models.DateField()
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    
    
    