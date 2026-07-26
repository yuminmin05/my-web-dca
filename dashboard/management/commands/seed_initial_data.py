from django.core.management.base import BaseCommand
from dashboard.models import Stock, DCAPreset


class Command(BaseCommand):
    help = 'Seed initial stock and preset data for the DCA platform'

    def handle(self, *args, **options):
        stock_symbols = ['ADVANC', 'AOT', 'BBL', 'CPALL', 'KBANK', 'PTT', 'SCB', 'TRUE']
        for symbol in stock_symbols:
            Stock.objects.get_or_create(symbol=symbol, defaults={'is_set50': True})

        presets = [
            {
                'name': 'Balanced SET50 DCA',
                'description': 'แผนลงทุนแบบสมดุลสำหรับหุ้น SET50',
                'monthly_investment': 5000,
                'duration_years': 10,
                'target_amount': 1000000,
                'selected_stocks': 'ADVANC,AOT,CPALL,KBANK,PTT',
                'expected_return': 10.5,
                'risk_level': 'medium',
                'is_active': True,
            },
            {
                'name': 'Conservative Growth',
                'description': 'แผนลงทุนแบบปลอดภัยและค่อยเป็นค่อยไป',
                'monthly_investment': 3000,
                'duration_years': 8,
                'target_amount': 800000,
                'selected_stocks': 'ADVANC,BBL,SCB,TRUE',
                'expected_return': 8.0,
                'risk_level': 'low',
                'is_active': True,
            },
        ]
        for preset in presets:
            DCAPreset.objects.get_or_create(name=preset['name'], defaults=preset)

        self.stdout.write(self.style.SUCCESS('Initial data seeded successfully'))
