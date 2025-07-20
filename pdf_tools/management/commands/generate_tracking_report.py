# ========================================
# File: pdf_tools/management/commands/generate_tracking_report.py
# ========================================

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Avg, Sum, Q
from pdf_tools.models import UserActivity, ErrorLog
import json

class Command(BaseCommand):
    help = 'Generate a tracking report for the specified time period'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Generate report for the last N days (default: 7)',
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file path (optional)',
        )
        parser.add_argument(
            '--format',
            choices=['text', 'json'],
            default='text',
            help='Output format (default: text)',
        )

    def handle(self, *args, **options):
        days = options['days']
        output_file = options['output']
        output_format = options['format']

        start_date = timezone.now() - timedelta(days=days)
        
        self.stdout.write(self.style.SUCCESS(f'📊 Generating {days}-day tracking report...'))

        # Gather statistics
        report_data = self.generate_report_data(start_date)

        # Format output
        if output_format == 'json':
            output = json.dumps(report_data, indent=2, default=str)
        else:
            output = self.format_text_report(report_data, days)

        # Write to file or stdout
        if output_file:
            with open(output_file, 'w') as f:
                f.write(output)
            self.stdout.write(self.style.SUCCESS(f'📄 Report saved to {output_file}'))
        else:
            self.stdout.write(output)

    def generate_report_data(self, start_date):
        """Generate comprehensive report data"""
        # Basic statistics
        total_activities = UserActivity.objects.filter(created_at__gte=start_date).count()
        total_conversions = UserActivity.objects.filter(
            created_at__gte=start_date,
            activity_type='file_process'
        ).count()
        successful_conversions = UserActivity.objects.filter(
            created_at__gte=start_date,
            activity_type='file_process',
            status='success'
        ).count()
        total_errors = ErrorLog.objects.filter(created_at__gte=start_date).count()
        unique_users = UserActivity.objects.filter(
            created_at__gte=start_date
        ).values('session_id').distinct().count()

        # Success rate
        success_rate = (successful_conversions / total_conversions * 100) if total_conversions > 0 else 0

        # Tool usage
        tool_usage = list(UserActivity.objects.filter(
            created_at__gte=start_date,
            activity_type__in=['tool_access', 'file_process'],
            tool_name__isnull=False
        ).values('tool_name').annotate(
            total_uses=Count('id'),
            successful_uses=Count('id', filter=Q(status='success')),
            failed_uses=Count('id', filter=Q(status='failed'))
        ).order_by('-total_uses'))

        # Error breakdown
        error_breakdown = list(ErrorLog.objects.filter(
            created_at__gte=start_date
        ).values('error_type', 'severity').annotate(
            count=Count('id')
        ).order_by('-count'))

        # Device statistics
        device_stats = list(UserActivity.objects.filter(
            created_at__gte=start_date
        ).values('device_type').annotate(
            count=Count('id')
        ).order_by('-count'))

        # Geographic data
        geographic_data = list(UserActivity.objects.filter(
            created_at__gte=start_date,
            country__isnull=False
        ).values('country').annotate(
            unique_users=Count('session_id', distinct=True),
            total_activities=Count('id')
        ).order_by('-unique_users'))

        # File processing stats
        file_stats = UserActivity.objects.filter(
            created_at__gte=start_date,
            activity_type='file_process'
        ).aggregate(
            total_files=Count('id'),
            avg_file_size=Avg('file_size'),
            total_file_size=Sum('file_size'),
            avg_processing_time=Avg('processing_time')
        )

        return {
            'report_generated_at': timezone.now(),
            'period_start': start_date,
            'period_end': timezone.now(),
            'summary': {
                'total_activities': total_activities,
                'total_conversions': total_conversions,
                'successful_conversions': successful_conversions,
                'total_errors': total_errors,
                'unique_users': unique_users,
                'success_rate': round(success_rate, 2)
            },
            'tool_usage': tool_usage,
            'error_breakdown': error_breakdown,
            'device_stats': device_stats,
            'geographic_data': geographic_data,
            'file_processing': file_stats
        }

    def format_text_report(self, data, days):
        """Format report data as readable text"""
        report = []
        
        report.append("="*60)
        report.append(f"SmallPDF.us Tracking Report - Last {days} Days")
        report.append("="*60)
        report.append(f"Generated: {data['report_generated_at']}")
        report.append(f"Period: {data['period_start']} to {data['period_end']}")
        report.append("")
        
        # Summary
        report.append("📊 SUMMARY")
        report.append("-" * 20)
        summary = data['summary']
        report.append(f"Total Activities: {summary['total_activities']:,}")
        report.append(f"Total Conversions: {summary['total_conversions']:,}")
        report.append(f"Successful Conversions: {summary['successful_conversions']:,}")
        report.append(f"Total Errors: {summary['total_errors']:,}")
        report.append(f"Unique Users: {summary['unique_users']:,}")
        report.append(f"Success Rate: {summary['success_rate']}%")
        report.append("")
        
        # Tool usage
        report.append("🔧 TOP TOOLS")
        report.append("-" * 20)
        for tool in data['tool_usage'][:10]:
            success_rate = (tool['successful_uses'] / tool['total_uses'] * 100) if tool['total_uses'] > 0 else 0
            report.append(f"{tool['tool_name']}: {tool['total_uses']} uses ({success_rate:.1f}% success)")
        report.append("")
        
        # Error breakdown
        if data['error_breakdown']:
            report.append("🚨 TOP ERRORS")
            report.append("-" * 20)
            for error in data['error_breakdown'][:10]:
                report.append(f"{error['error_type']} ({error['severity']}): {error['count']} occurrences")
            report.append("")
        
        # Device stats
        report.append("📱 DEVICE BREAKDOWN")
        report.append("-" * 20)
        for device in data['device_stats']:
            report.append(f"{device['device_type'] or 'Unknown'}: {device['count']} activities")
        report.append("")
        
        # Geographic data
        if data['geographic_data']:
            report.append("🌍 TOP COUNTRIES")
            report.append("-" * 20)
            for country in data['geographic_data'][:10]:
                report.append(f"{country['country']}: {country['unique_users']} users, {country['total_activities']} activities")
            report.append("")
        
        # File processing
        file_stats = data['file_processing']
        if file_stats['total_files']:
            report.append("📁 FILE PROCESSING")
            report.append("-" * 20)
            report.append(f"Total Files Processed: {file_stats['total_files']:,}")
            if file_stats['avg_file_size']:
                report.append(f"Average File Size: {file_stats['avg_file_size']/1024/1024:.2f} MB")
            if file_stats['total_file_size']:
                report.append(f"Total Data Processed: {file_stats['total_file_size']/1024/1024/1024:.2f} GB")
            if file_stats['avg_processing_time']:
                report.append(f"Average Processing Time: {file_stats['avg_processing_time']:.2f} seconds")
        
        report.append("")
        report.append("="*60)
        
        return "\n".join(report)
