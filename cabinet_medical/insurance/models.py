from django.db import models
from utilisateurs.models import Patient
from django.core.validators import FileExtensionValidator
from django.utils import timezone

class Insurance(models.Model):
    """Model representing an insurance provider."""
    name = models.CharField(max_length=100, unique=True)
    contact_info = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Insurance Provider"
        verbose_name_plural = "Insurance Providers"
        ordering = ['name']

class PatientInsurance(models.Model):
    """Model representing a patient's insurance policy."""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='insurance_policies')
    insurance = models.ForeignKey(Insurance, on_delete=models.CASCADE, related_name='patient_policies')
    policy_number = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    requires_authorization = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.patient.utilisateur.username} - {self.insurance.name} ({self.policy_number})"

    class Meta:
        verbose_name = "Patient Insurance Policy"
        verbose_name_plural = "Patient Insurance Policies"
        unique_together = ['patient', 'insurance', 'policy_number']
        ordering = ['-is_active', 'insurance__name']

    def is_valid(self):
        """Check if the insurance policy is currently valid."""
        from django.utils import timezone
        today = timezone.now().date()
        return self.is_active and (self.end_date is None or self.end_date >= today)

class ReimbursementFolder(models.Model):
    """Model representing an insurance reimbursement request folder."""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('reimbursed', 'Reimbursed'),
        ('rejected', 'Rejected')
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='reimbursement_folders')
    insurance_policy = models.ForeignKey(PatientInsurance, on_delete=models.CASCADE, related_name='reimbursement_folders')
    title = models.CharField(max_length=200)
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    submission_date = models.DateTimeField(null=True, blank=True)
    review_date = models.DateTimeField(null=True, blank=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.patient.utilisateur.username} - {self.title} ({self.get_status_display()})"

    class Meta:
        verbose_name = "Reimbursement Folder"
        verbose_name_plural = "Reimbursement Folders"
        ordering = ['-created_at']

    def submit(self):
        """Submit the reimbursement folder to the insurance provider."""
        if self.status == 'draft':
            self.status = 'submitted'
            self.submission_date = timezone.now()
            self.save()
            return True
        return False

    def update_status(self, new_status):
        """Update the status of the reimbursement folder."""
        if new_status in dict(self.STATUS_CHOICES):
            self.status = new_status
            if new_status == 'under_review':
                self.review_date = timezone.now()
            elif new_status in ['approved', 'reimbursed', 'rejected']:
                self.completion_date = timezone.now()
            self.save()
            return True
        return False

class ReimbursementDocument(models.Model):
    """Model representing a document in a reimbursement folder."""
    folder = models.ForeignKey(ReimbursementFolder, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=200)
    file = models.FileField(
        upload_to='reimbursement_documents/%Y/%m/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    description = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.folder.title} - {self.title}"

    class Meta:
        verbose_name = "Reimbursement Document"
        verbose_name_plural = "Reimbursement Documents"
        ordering = ['-uploaded_at']
