# ========================================
# File: pdf_tools/management/commands/monitor_system_health.py
# ========================================

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
from pdf_tools.models import UserActivity, ErrorLog
import psutil
import os

class Command(BaseCommand):
    help = 'Monitor system health and send alerts if needed'

    def add_arguments(self, parser):
        parser.add_argument(
            '--send-alerts',
            action='store_true',
            help='Send email alerts for critical issues',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Verbose output',
        )

    def handle(self, *args, **options):
        send_alerts = options['send_alerts']
        verbose = options['verbose']

        self.stdout.write(self.style.SUCCESS('🔍 Monitoring system health...'))

        # Check various health metrics
        health_issues = []
        
        # Check error rate
        error_rate = self.check_error_rate()
        if error_rate > 5.0:  # Alert if error rate > 5%
            issue = f"High error rate: {error_rate:.2f}%"
            health_issues.append(issue)
            if verbose:
                self.stdout.write(self.style.ERROR(f"❌ {issue}"))

        # Check response time
        avg_response_time = self.check_response_time()
        if avg_response_time > 10.0:  # Alert if avg response time > 10s
            issue = f"Slow response time: {avg_response_time:.2f}s"
            health_issues.append(issue)
            if verbose:
                self.stdout.write(self.style.WARNING(f"⚠️ {issue}"))

        # Check system resources
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_usage = psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage('/').percent

        if cpu_usage > 80:
            issue = f"High CPU usage: {cpu_usage:.1f}%"
            health_issues.append(issue)
            if verbose:
                self.stdout.write(self.style.WARNING(f"⚠️ {issue}"))

        if memory_usage > 80:
            issue = f"High memory usage: {memory_usage:.1f}%"
            health_issues.append(issue)
            if verbose:
                self.stdout.write(self.style.WARNING(f"⚠️ {issue}"))

        if disk_usage > 90:
            issue = f"High disk usage: {disk_usage:.1f}%"
            health_issues.append(issue)
            if verbose:
                self.stdout.write(self.style.ERROR(f"❌ {issue}"))

        # Check for unresolved critical errors
        critical_errors = ErrorLog.objects.filter(
            severity='critical',
            resolved=False,
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).count()

        if critical_errors > 0:
            issue = f"{critical_errors} unresolved critical errors"
            health_issues.append(issue)
            if verbose:
                self.stdout.write(self.style.ERROR(f"❌ {issue}"))

        # Report results
        if health_issues:
            self.stdout.write(self.style.ERROR(f"🚨 Found {len(health_issues)} health issues"))
            for issue in health_issues:
                self.stdout.write(f"  - {issue}")
            
            if send_alerts:
                self.send_health_alert(health_issues)
        else:
            self.stdout.write(self.style.SUCCESS("✅ System health is good"))

        # Display current stats if verbose
        if verbose:
            self.stdout.write("\n📊 Current System Stats:")
            self.stdout.write(f"CPU Usage: {cpu_usage:.1f}%")
            self.stdout.write(f"Memory Usage: {memory_usage:.1f}%")
            self.stdout.write(f"Disk Usage: {disk_usage:.1f}%")
            self.stdout.write(f"Error Rate (24h): {error_rate:.2f}%")
            self.stdout.write(f"Avg Response Time (24h): {avg_response_time:.2f}s")

    def check_error_rate(self):
        """Calculate error rate for the last 24 hours"""
        last_24h = timezone.now() - timedelta(hours=24)
        total_activities = UserActivity.objects.filter(created_at__gte=last_24h).count()
        total_errors = ErrorLog.objects.filter(created_at__gte=last_24h).count()
        
        if total_activities == 0:
            return 0
        
        return (total_errors / total_activities) * 100

    def check_response_time(self):
        """Calculate average response time for the last 24 hours"""
        last_24h = timezone.now() - timedelta(hours=24)
        avg_time = UserActivity.objects.filter(
            created_at__gte=last_24h,
            processing_time__isnull=False
        ).aggregate(avg=models.Avg('processing_time'))['avg']
        
        return avg_time or 0

    def send_health_alert(self, issues):
        """Send email alert about health issues"""
        subject = f"🚨 SmallPDF.us Health Alert - {len(issues)} Issues Detected"
        
        message = f"""
System health monitoring has detected the following issues:

{chr(10).join(f'• {issue}' for issue in issues)}

Time: {timezone.now()}
Server: {os.uname().nodename if hasattr(os, 'uname') else 'Unknown'}

Please investigate these issues as soon as possible.

---
SmallPDF.us Monitoring System
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                settings.ADMINS[0] if settings.ADMINS else ['admin@smallpdf.us'],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS("📧 Health alert sent successfully"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to send health alert: {e}"))