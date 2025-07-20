# ========================================
# File: pdf_tools/management/commands/cleanup_tracking_data.py
# ========================================

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from pdf_tools.models import UserActivity, ErrorLog

class Command(BaseCommand):
    help = 'Clean up old tracking data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Delete activities older than this many days (default: 90)',
        )
        parser.add_argument(
            '--error-days',
            type=int,
            default=180,
            help='Delete resolved errors older than this many days (default: 180)',
        )
        parser.add_argument(
            '--anonymize-days',
            type=int,
            default=30,
            help='Anonymize IP addresses older than this many days (default: 30)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        days = options['days']
        error_days = options['error_days']
        anonymize_days = options['anonymize_days']
        dry_run = options['dry_run']

        self.stdout.write(self.style.SUCCESS('🧹 Starting tracking data cleanup...'))

        # Calculate cutoff dates
        activities_cutoff = timezone.now() - timedelta(days=days)
        errors_cutoff = timezone.now() - timedelta(days=error_days)
        anonymize_cutoff = timezone.now() - timedelta(days=anonymize_days)

        # Count what will be affected
        old_activities = UserActivity.objects.filter(created_at__lt=activities_cutoff)
        old_errors = ErrorLog.objects.filter(created_at__lt=errors_cutoff, resolved=True)
        activities_to_anonymize = UserActivity.objects.filter(created_at__lt=anonymize_cutoff)
        errors_to_anonymize = ErrorLog.objects.filter(created_at__lt=anonymize_cutoff)

        self.stdout.write(f'📊 Found {old_activities.count()} old activities to delete')
        self.stdout.write(f'🚨 Found {old_errors.count()} old resolved errors to delete')
        self.stdout.write(f'🔒 Found {activities_to_anonymize.count()} activities to anonymize')
        self.stdout.write(f'🔒 Found {errors_to_anonymize.count()} errors to anonymize')

        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN - No data will be deleted'))
            return

        # Confirm deletion
        if old_activities.count() > 0 or old_errors.count() > 0:
            confirm = input('Are you sure you want to delete this data? (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING('❌ Cleanup cancelled'))
                return

        # Perform cleanup
        deleted_activities = old_activities.delete()[0]
        deleted_errors = old_errors.delete()[0]
        anonymized_activities = activities_to_anonymize.update(ip_address='0.0.0.0')
        anonymized_errors = errors_to_anonymize.update(ip_address='0.0.0.0')

        self.stdout.write(self.style.SUCCESS(f'✅ Deleted {deleted_activities} old activities'))
        self.stdout.write(self.style.SUCCESS(f'✅ Deleted {deleted_errors} old errors'))
        self.stdout.write(self.style.SUCCESS(f'🔒 Anonymized {anonymized_activities} activity IPs'))
        self.stdout.write(self.style.SUCCESS(f'🔒 Anonymized {anonymized_errors} error IPs'))
        self.stdout.write(self.style.SUCCESS('🧹 Cleanup completed!'))
