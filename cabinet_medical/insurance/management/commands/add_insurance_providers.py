from django.core.management.base import BaseCommand
from insurance.models import Insurance

class Command(BaseCommand):
    help = 'Adds default insurance providers'

    def handle(self, *args, **kwargs):
        providers = [
            {
                'name': 'CNSS',
                'contact_info': '080 100 47 47'
            },
            {
                'name': 'CNOPS',
                'contact_info': '080 200 47 47'
            },
            {
                'name': 'RAMED',
                'contact_info': '080 300 47 47'
            },
            {
                'name': 'AXA Assurance',
                'contact_info': '080 400 47 47'
            },
            {
                'name': 'Wafa Assurance',
                'contact_info': '080 500 47 47'
            },
            {
                'name': 'Atlanta Assurance',
                'contact_info': '080 600 47 47'
            }
        ]

        for provider in providers:
            Insurance.objects.get_or_create(
                name=provider['name'],
                defaults={'contact_info': provider['contact_info']}
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully added insurance provider "{provider["name"]}"')
            ) 