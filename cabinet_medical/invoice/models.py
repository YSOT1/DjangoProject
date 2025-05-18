from django.db import models
from django.utils import timezone

class Payment(models.Model):
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
        REFUNDED = 'refunded', 'Refunded'

    class PaymentMethod(models.TextChoices):
        CREDIT_CARD = 'credit_card', 'Credit Card'
        DEBIT_CARD = 'debit_card', 'Debit Card'
        BANK_TRANSFER = 'bank_transfer', 'Bank Transfer'
        PAYPAL = 'paypal', 'PayPal'

    invoice = models.ForeignKey('Invoice', on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'

    def __str__(self):
        return f"Payment #{self.id} - {self.invoice} - {self.amount}"

    def mark_as_completed(self, transaction_id):
        """Mark the payment as completed and update the invoice"""
        self.status = self.PaymentStatus.COMPLETED
        self.transaction_id = transaction_id
        self.payment_date = timezone.now()
        self.save()
        self.invoice.mark_as_paid()

class Invoice(models.Model):
    patient = models.ForeignKey('utilisateurs.Patient', on_delete=models.CASCADE, related_name='invoices')
    doctor = models.ForeignKey('utilisateurs.Doctor', on_delete=models.CASCADE, related_name='invoices')
    appointment = models.ForeignKey('appointements.Appointement', on_delete=models.CASCADE, related_name='invoice')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    issued_date = models.DateField(default=timezone.now)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-issued_date']
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'

    def __str__(self):
        return f"Invoice #{self.id} - {self.patient.utilisateur.username} - {self.amount}"

    def mark_as_paid(self):
        """Mark the invoice as paid and update the timestamp"""
        self.is_paid = True
        self.save(update_fields=['is_paid', 'updated_at'])

    @property
    def status(self):
        """Return the payment status of the invoice"""
        return "Paid" if self.is_paid else "Unpaid"

    @property
    def days_since_issued(self):
        """Calculate the number of days since the invoice was issued"""
        return (timezone.now().date() - self.issued_date).days

    @property
    def latest_payment(self):
        """Get the latest payment for this invoice"""
        return self.payments.order_by('-created_at').first()
