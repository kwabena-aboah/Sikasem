"""
Management command: seed_ghana_tax_tables
Seeds GRA PAYE tax bands for Ghana into the TaxTable model.
Run: python manage.py seed_ghana_tax_tables
"""
from django.core.management.base import BaseCommand
from apps.payroll.models import TaxTable


class Command(BaseCommand):
    help = 'Seed Ghana GRA PAYE tax bands'

    def handle(self, *args, **options):
        # Clear existing
        TaxTable.objects.filter(country='GH').delete()

        # Ghana 2024 Annual Tax Bands (GHS)
        bands_2024 = [
            {'band_name': 'Band 1 (0%)',   'min': 0,       'max': 4380,   'rate': 0.00,  'cumulative': 0.00},
            {'band_name': 'Band 2 (5%)',   'min': 4380,    'max': 5580,   'rate': 0.05,  'cumulative': 0.00},
            {'band_name': 'Band 3 (10%)',  'min': 5580,    'max': 6780,   'rate': 0.10,  'cumulative': 60.00},
            {'band_name': 'Band 4 (17.5%)','min': 6780,    'max': 42780,  'rate': 0.175, 'cumulative': 180.00},
            {'band_name': 'Band 5 (25%)',  'min': 42780,   'max': 240000, 'rate': 0.25,  'cumulative': 6480.00},
            {'band_name': 'Band 6 (30%)',  'min': 240000,  'max': None,   'rate': 0.30,  'cumulative': 55905.00},
        ]

        # Ghana 2023 Annual Tax Bands (GHS)
        bands_2023 = [
            {'band_name': 'Band 1 (0%)',   'min': 0,       'max': 4380,   'rate': 0.00,  'cumulative': 0.00},
            {'band_name': 'Band 2 (5%)',   'min': 4380,    'max': 5580,   'rate': 0.05,  'cumulative': 0.00},
            {'band_name': 'Band 3 (10%)',  'min': 5580,    'max': 6780,   'rate': 0.10,  'cumulative': 60.00},
            {'band_name': 'Band 4 (17.5%)','min': 6780,    'max': 42780,  'rate': 0.175, 'cumulative': 180.00},
            {'band_name': 'Band 5 (25%)',  'min': 42780,   'max': 240000, 'rate': 0.25,  'cumulative': 6480.00},
            {'band_name': 'Band 6 (30%)',  'min': 240000,  'max': None,   'rate': 0.30,  'cumulative': 55905.00},
        ]

        created = 0
        for year, bands in [(2024, bands_2024), (2023, bands_2023)]:
            for b in bands:
                TaxTable.objects.create(
                    effective_year=year,
                    band_name=b['band_name'],
                    min_amount=b['min'],
                    max_amount=b['max'],
                    rate=b['rate'],
                    cumulative_tax_below=b['cumulative'],
                    is_monthly=False,
                    country='GH',
                )
                created += 1

        self.stdout.write(
            self.style.SUCCESS(f'✓ Seeded {created} Ghana PAYE tax bands (2023–2024)')
        )
