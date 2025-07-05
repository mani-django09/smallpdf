from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from your_app.models import UserActivity, ErrorLog

class Command(BaseCommand):
    help = 'Clean up old analytics data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of days to keep (default: 90)',
        )

    def handle(self, *args, **options):
        days = options['days']
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Clean up old activities
        old_activities = UserActivity.objects.filter(created_at__lt=cutoff_date)
        activity_count = old_activities.count()
        old_activities.delete()
        
        # Clean up old error logs
        old_errors = ErrorLog.objects.filter(created_at__lt=cutoff_date)
        error_count = old_errors.count()
        old_errors.delete()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully cleaned up {activity_count} activities and {error_count} errors older than {days} days'
            )
        )