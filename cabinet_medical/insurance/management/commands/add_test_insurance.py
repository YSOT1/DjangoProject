from django.core.management.base import BaseCommand
from insurance.models import Insurance, PatientInsurance
from utilisateurs.models import Patient
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Adds a test insurance policy for the first patient'

    def handle(self, *args, **kwargs):
        try:
            # Get the first patient
            patient = Patient.objects.first()
            if not patient:
                self.stdout.write(self.style.ERROR('No patients found in the database'))
                return

            # Get the first insurance provider
            insurance = Insurance.objects.first()
            if not insurance:
                self.stdout.write(self.style.ERROR('No insurance providers found in the database'))
                return

            # Create an active insurance policy
            policy = PatientInsurance.objects.create(
                patient=patient,
                insurance=insurance,
                policy_number='TEST123',
                is_active=True,
                start_date=date.today(),
                end_date=date.today() + timedelta(days=365),
                requires_authorization=False
            )

            self.stdout.write(self.style.SUCCESS(f'Successfully created insurance policy: {policy}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating insurance policy: {str(e)}')) 