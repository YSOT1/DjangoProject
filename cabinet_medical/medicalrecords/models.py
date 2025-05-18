from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from utilisateurs.models import Doctor, Patient
from django.utils import timezone

class MedicalRecord(models.Model):
    class BloodType(models.TextChoices):
        A_POSITIVE = 'A+', 'A+'
        A_NEGATIVE = 'A-', 'A-'
        B_POSITIVE = 'B+', 'B+'
        B_NEGATIVE = 'B-', 'B-'
        AB_POSITIVE = 'AB+', 'AB+'
        AB_NEGATIVE = 'AB-', 'AB-'
        O_POSITIVE = 'O+', 'O+'
        O_NEGATIVE = 'O-', 'O-'   

    # Basic Information
    patient = models.ForeignKey("utilisateurs.Patient", on_delete=models.CASCADE)
    blood_type = models.CharField(max_length=3, choices=BloodType.choices, null=True, blank=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # in cm
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # in kg
    allergies = models.TextField(null=True, blank=True)
    chronic_diseases = models.TextField(null=True, blank=True)
    family_history = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Medical Record - {self.patient.utilisateur.username}"

class Consultation(models.Model):
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='consultations')
    doctor = models.ForeignKey("utilisateurs.Doctor", on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    symptoms = models.TextField()
    diagnosis = models.TextField()
    prescription = models.TextField()
    notes = models.TextField(null=True, blank=True)
    follow_up_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Consultation - {self.patient.utilisateur.username} with Dr. {self.doctor.utilisateur.username}"

class MedicalTest(models.Model):
    class TestType(models.TextChoices):
        BLOOD_TEST = 'blood', 'Blood Test'
        X_RAY = 'xray', 'X-Ray'
        MRI = 'mri', 'MRI'
        CT_SCAN = 'ct', 'CT Scan'
        OTHER = 'other', 'Other'

    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='tests')
    doctor = models.ForeignKey("utilisateurs.Doctor", on_delete=models.CASCADE)
    test_type = models.CharField(max_length=20, choices=TestType.choices)
    test_date = models.DateTimeField(auto_now_add=True)
    test_results = models.TextField()
    test_file = models.FileField(upload_to='medical_tests/', null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_test_type_display()} - {self.medical_record.patient.utilisateur.username}"

class DoctorRating(models.Model):
    """Model for storing patient ratings of doctors."""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='doctor_ratings')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='ratings')
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5"
    )
    comment = models.TextField(blank=True, help_text="Optional comment about the consultation")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['patient', 'doctor']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.patient.utilisateur.username}'s rating for Dr. {self.doctor.utilisateur.username}"

    @property
    def stars(self):
        """Return the rating as a string of stars."""
        return '★' * self.rating + '☆' * (5 - self.rating)
