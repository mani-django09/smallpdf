from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from pdf_tools.models import ContactSettings, UserActivity, ErrorLog
import os

class Command(BaseCommand):
    help = 'Set up admin tracking system and create sample data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-superuser',
            action='store_true',
            help='Create a superuser for admin access',
        )
        parser.add_argument(
            '--sample-data',
            action='store_true',
            help='Create sample tracking data for testing',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up SmallPDF.us Admin Tracking System...'))

        # Create necessary directories
        self.create_directories()

        # Set up contact settings
        self.setup_contact_settings()

        # Create superuser if requested
        if options['create_superuser']:
            self.create_superuser()

        # Create sample data if requested
        if options['sample_data']:
            self.create_sample_data()

        self.stdout.write(self.style.SUCCESS('✅ Admin tracking system setup complete!'))
        self.stdout.write(self.style.WARNING('Next steps:'))
        self.stdout.write('1. Add middleware to settings.py: pdf_tools.middleware.ActivityTrackingMiddleware')
        self.stdout.write('2. Run migrations: python manage.py migrate')
        self.stdout.write('3. Access admin at: /admin/')
        self.stdout.write('4. View analytics at: /admin/analytics/')

    def create_directories(self):
        """Create necessary directories for logging and media"""
        directories = [
            'logs',
            'media/contact_attachments',
            'media/converted_files',
            'media/temp_files',
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                self.stdout.write(f'📁 Created directory: {directory}')

    def setup_contact_settings(self):
        """Set up default contact settings"""
        settings, created = ContactSettings.objects.get_or_create(pk=1)
        if created:
            self.stdout.write('⚙️ Created default contact settings')
        else:
            self.stdout.write('⚙️ Contact settings already exist')

    def create_superuser(self):
        """Create a superuser for admin access"""
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write('👤 Superuser already exists')
            return

        username = input('Enter superuser username (default: admin): ') or 'admin'
        email = input('Enter superuser email: ')
        
        if not email:
            email = 'admin@smallpdf.us'

        user = User.objects.create_superuser(
            username=username,
            email=email,
            password='admin123'  # Change this!
        )
        
        self.stdout.write(self.style.SUCCESS(f'👤 Created superuser: {username}'))
        self.stdout.write(self.style.WARNING('⚠️ Default password is "admin123" - please change it!'))

    def create_sample_data(self):
        """Create sample tracking data for testing"""
        from pdf_tools.middleware import track_activity, log_error
        import random
        from datetime import timedelta
        
        self.stdout.write('📊 Creating sample tracking data...')
        
        # Sample tools
        tools = [
            'PDF to Word', 'Merge PDF', 'Compress PDF', 'PDF to JPG',
            'JPG to PDF', 'WebP to PNG', 'PNG to WebP', 'Split PDF'
        ]
        # Continuation of setup_admin_tracking.py

        # Sample devices and browsers
        devices = ['desktop', 'mobile', 'tablet']
        browsers = ['Chrome', 'Firefox', 'Safari', 'Edge']
        
        # Sample IPs and countries
        sample_ips = [
            ('192.168.1.100', 'United States'),
            ('10.0.0.50', 'India'),
            ('172.16.0.20', 'United Kingdom'),
            ('203.0.113.1', 'Canada'),
            ('198.51.100.5', 'Germany'),
        ]
        
        # Create activities for the last 7 days
        for day in range(7):
            date = timezone.now() - timedelta(days=day)
            activities_per_day = random.randint(50, 200)
            
            for _ in range(activities_per_day):
                ip, country = random.choice(sample_ips)
                
                # Create a mock request object
                class MockRequest:
                    def __init__(self):
                        self.META = {
                            'HTTP_USER_AGENT': f'{random.choice(browsers)}/90.0',
                            'HTTP_REFERER': 'https://google.com',
                            'REMOTE_ADDR': ip
                        }
                        self.session = {'session_key': f'session_{random.randint(1000, 9999)}'}
                        self.user = None
                        self.path = f'/{random.choice(tools).lower().replace(" ", "-")}/'
                    
                    def build_absolute_uri(self):
                        return f'https://smallpdf.us{self.path}'
                
                mock_request = MockRequest()
                
                # Create activity
                UserActivity.objects.create(
                    session_id=mock_request.session['session_key'],
                    activity_type=random.choice(['page_view', 'tool_access', 'file_process', 'file_download']),
                    tool_name=random.choice(tools),
                    file_name=f'document_{random.randint(1, 1000)}.pdf' if random.random() > 0.3 else None,
                    file_size=random.randint(1024, 50*1024*1024) if random.random() > 0.5 else None,
                    file_type=random.choice(['pdf', 'docx', 'jpg', 'png']) if random.random() > 0.5 else None,
                    processing_time=random.uniform(0.5, 10.0) if random.random() > 0.4 else None,
                    status=random.choice(['success', 'success', 'success', 'failed']),  # More success
                    ip_address=ip,
                    country=country,
                    device_type=random.choice(devices),
                    browser=random.choice(browsers),
                    page_url=mock_request.build_absolute_uri(),
                    created_at=date - timedelta(
                        hours=random.randint(0, 23),
                        minutes=random.randint(0, 59)
                    )
                )
        
        # Create some sample errors
        error_types = [
            'CONVERSION_ERROR', 'FILE_UPLOAD_ERROR', 'PROCESSING_TIMEOUT',
            'INVALID_FILE_FORMAT', 'FILE_SIZE_EXCEEDED', 'SYSTEM_ERROR'
        ]
        
        for _ in range(20):
            ip, country = random.choice(sample_ips)
            ErrorLog.objects.create(
                session_id=f'session_{random.randint(1000, 9999)}',
                error_type=random.choice(error_types),
                error_message=f'Sample error message for testing purposes',
                severity=random.choice(['low', 'medium', 'high', 'critical']),
                ip_address=ip,
                user_agent=f'{random.choice(browsers)}/90.0 (Windows NT 10.0; Win64; x64)',
                created_at=timezone.now() - timedelta(
                    hours=random.randint(1, 168),  # Last week
                    minutes=random.randint(0, 59)
                ),
                resolved=random.choice([True, False])
            )
        
        self.stdout.write(self.style.SUCCESS('📊 Sample data created successfully!'))



