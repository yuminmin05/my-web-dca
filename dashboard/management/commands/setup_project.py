from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Run migrations and seed initial project data'

    def handle(self, *args, **options):
        self.stdout.write('Applying database migrations...')
        call_command('migrate', verbosity=0)

        self.stdout.write('Seeding initial data...')
        call_command('seed_initial_data', verbosity=0)

        self.stdout.write(self.style.SUCCESS('Project setup completed successfully'))
