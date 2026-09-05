"""
Management command: link_users_to_employees
Links User accounts to Employee profiles by matching on email.
Run: python manage.py link_users_to_employees

This is useful when users were created before employee profiles,
or when employee self-service accounts need to be connected.
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Link User accounts to Employee profiles by matching email'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Show what would be linked without making changes')

    def handle(self, *args, **options):
        from apps.accounts.models import User
        from apps.employees.models import Employee

        dry_run = options['dry_run']
        linked  = 0
        skipped = 0

        for user in User.objects.filter(role='employee'):
            if hasattr(user, 'employee_profile') and user.employee_profile:
                skipped += 1
                continue

            # Try to match by work email or personal email
            emp = (
                Employee.objects.filter(work_email=user.email).first()
                or Employee.objects.filter(personal_email=user.email).first()
            )

            if emp:
                if not dry_run:
                    emp.user = user
                    emp.save(update_fields=['user'])
                self.stdout.write(
                    self.style.SUCCESS(f'{"[DRY] " if dry_run else ""}Linked {user.email} → {emp.get_full_name()} ({emp.employee_id})')
                )
                linked += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f'No employee found for {user.email}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\nDone. Linked: {linked}, Already linked: {skipped}')
        )
