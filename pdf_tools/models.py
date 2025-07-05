# pdf_tools/models.py

from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
import uuid
import json
import pytz

class PDFTool(models.Model):
    """Model for different PDF tools available on the site"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=50, help_text="Font Awesome icon class")
    is_featured = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    seo_title = models.CharField(max_length=70, blank=True)
    seo_description = models.CharField(max_length=160, blank=True)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'PDF Tool'
        verbose_name_plural = 'PDF Tools'
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('pdf_tools:tool_detail', kwargs={'slug': self.slug})

class ProcessedFile(models.Model):
    """Model to track file processing (optional - for analytics)"""
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField(help_text="File size in bytes")
    tool_used = models.ForeignKey(PDFTool, on_delete=models.CASCADE)
    processed_at = models.DateTimeField(default=timezone.now)
    success = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-processed_at']
        verbose_name = 'Processed File'
        verbose_name_plural = 'Processed Files'
    
    def __str__(self):
        return f"{self.file_name} - {self.tool_used.name}"
    
    def get_processed_at_ist(self):
        """Get processing time in IST"""
        if self.processed_at:
            ist = pytz.timezone('Asia/Kolkata')
            if timezone.is_aware(self.processed_at):
                ist_time = self.processed_at.astimezone(ist)
            else:
                ist_time = ist.localize(self.processed_at)
            return ist_time.strftime('%B %d, %Y, %I:%M %p IST')
        return "-"
    
    def get_file_size_display(self):
        """Display file size in human readable format"""
        if self.file_size:
            size = self.file_size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
        return "Unknown"

class ContactMessage(models.Model):
    """Model for contact form messages"""
    CATEGORY_CHOICES = [
        ('technical_support', 'Technical Support'),
        ('billing', 'Billing & Pricing'),
        ('feature_request', 'Feature Request'),
        ('bug_report', 'Bug Report'),
        ('partnership', 'Partnership Inquiry'),
        ('general', 'General Question'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    company = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    subject = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    message = models.TextField()
    attachment = models.FileField(upload_to='contact_attachments/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    admin_notes = models.TextField(blank=True, null=True)
    assigned_to = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['category', 'created_at']),
            models.Index(fields=['priority', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.full_name} - {self.subject}"
    
    def get_age(self):
        """Get age of message in IST"""
        if self.created_at:
            ist = pytz.timezone('Asia/Kolkata')
            now_ist = timezone.now().astimezone(ist)
            
            if timezone.is_aware(self.created_at):
                created_ist = self.created_at.astimezone(ist)
            else:
                created_ist = ist.localize(self.created_at)
            
            diff = now_ist - created_ist
            
            if diff.days > 0:
                return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"{hours} hour{'s' if hours > 1 else ''} ago"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            else:
                return "Just now"
        return "-"
    
    def get_created_at_ist(self):
        """Get creation time in IST"""
        if self.created_at:
            ist = pytz.timezone('Asia/Kolkata')
            if timezone.is_aware(self.created_at):
                ist_time = self.created_at.astimezone(ist)
            else:
                ist_time = ist.localize(self.created_at)
            return ist_time.strftime('%B %d, %Y, %I:%M %p IST')
        return "-"
    
    def get_updated_at_ist(self):
        """Get update time in IST"""
        if self.updated_at:
            ist = pytz.timezone('Asia/Kolkata')
            if timezone.is_aware(self.updated_at):
                ist_time = self.updated_at.astimezone(ist)
            else:
                ist_time = ist.localize(self.updated_at)
            return ist_time.strftime('%B %d, %Y, %I:%M %p IST')
        return "-"
    
    def get_short_message(self, length=100):
        """Get truncated message for display"""
        if len(self.message) <= length:
            return self.message
        return self.message[:length] + '...'
    
    def is_urgent(self):
        """Check if message is urgent"""
        return self.priority == 'urgent'
    
    def is_new(self):
        """Check if message is new"""
        return self.status == 'new'

class ContactSettings(models.Model):
    """Model for contact page settings"""
    office_address = models.TextField(
        default="123 Tech Hub Drive\nSuite 456\nSan Francisco, CA 94107\nUnited States",
        help_text="Full office address with line breaks"
    )
    office_phone = models.CharField(max_length=20, default="+1 (555) SMALL-PDF")
    office_email = models.EmailField(default="support@smallpdf.us")
    business_hours_weekdays = models.CharField(
        max_length=50, 
        default="Monday - Friday: 9:00 AM - 6:00 PM (IST)"
    )
    business_hours_saturday = models.CharField(
        max_length=50, 
        default="Saturday: 10:00 AM - 4:00 PM (IST)"
    )
    business_hours_sunday = models.CharField(
        max_length=50, 
        default="Sunday: Closed"
    )
    facebook_url = models.URLField(blank=True, null=True)
    twitter_url = models.URLField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    instagram_url = models.URLField(blank=True, null=True)
    auto_response_enabled = models.BooleanField(
        default=True,
        help_text="Send automatic response emails to users"
    )
    response_time_hours = models.IntegerField(
        default=4,
        help_text="Expected response time in hours"
    )
    admin_notification_enabled = models.BooleanField(
        default=True,
        help_text="Send email notifications to admins for new messages"
    )
    admin_email = models.EmailField(default="admin@smallpdf.us")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Contact Settings'
        verbose_name_plural = 'Contact Settings'
    
    def __str__(self):
        return "Contact Page Settings"
    
    @classmethod
    def get_settings(cls):
        """Get or create contact settings instance"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings
    
    def get_social_media_links(self):
        """Get all social media links as a dictionary"""
        return {
            'facebook': self.facebook_url,
            'twitter': self.twitter_url,
            'linkedin': self.linkedin_url,
            'instagram': self.instagram_url,
        }

class UserActivity(models.Model):
    """Track all user activities on the platform"""
    ACTIVITY_TYPES = [
        ('page_view', 'Page View'),
        ('tool_access', 'Tool Access'),
        ('file_upload', 'File Upload'),
        ('file_process', 'File Process'),
        ('file_download', 'File Download'),
        ('error', 'Error'),
        ('contact_form', 'Contact Form'),
        ('search', 'Search'),
    ]
    
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
        ('error', 'Error'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_id = models.CharField(max_length=100, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES, db_index=True)
    page_url = models.URLField(max_length=500)
    tool_name = models.CharField(max_length=100, blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file_size = models.BigIntegerField(null=True, blank=True)  # in bytes
    file_type = models.CharField(max_length=50, blank=True, null=True)
    processing_time = models.FloatField(null=True, blank=True)  # in seconds
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='success')
    error_message = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(db_index=True)
    user_agent = models.TextField()
    referer = models.URLField(max_length=500, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    device_type = models.CharField(max_length=20, blank=True, null=True)  # mobile, desktop, tablet
    browser = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    additional_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User Activity'
        verbose_name_plural = 'User Activities'
        indexes = [
            models.Index(fields=['activity_type', 'created_at']),
            models.Index(fields=['tool_name', 'created_at']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['ip_address', 'created_at']),
            models.Index(fields=['session_id', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.activity_type} - {self.ip_address} - {self.created_at}"
    
    def get_created_at_ist(self):
        """Get creation time in IST"""
        if self.created_at:
            ist = pytz.timezone('Asia/Kolkata')
            if timezone.is_aware(self.created_at):
                ist_time = self.created_at.astimezone(ist)
            else:
                ist_time = ist.localize(self.created_at)
            return ist_time.strftime('%B %d, %Y, %I:%M %p IST')
        return "-"
    
    def get_file_size_display(self):
        """Display file size in human readable format"""
        if self.file_size:
            size = self.file_size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
        return "-"
    
    def get_processing_time_display(self):
        """Display processing time in human readable format"""
        if self.processing_time:
            if self.processing_time < 1:
                return f"{self.processing_time * 1000:.0f}ms"
            elif self.processing_time < 60:
                return f"{self.processing_time:.1f}s"
            else:
                minutes = int(self.processing_time // 60)
                seconds = int(self.processing_time % 60)
                return f"{minutes}m {seconds}s"
        return "-"

class ErrorLog(models.Model):
    """Detailed error logging"""
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_id = models.CharField(max_length=100, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    error_type = models.CharField(max_length=100)
    error_message = models.TextField()
    stack_trace = models.TextField(blank=True, null=True)
    file_path = models.CharField(max_length=500, blank=True, null=True)
    line_number = models.IntegerField(null=True, blank=True)
    function_name = models.CharField(max_length=100, blank=True, null=True)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='medium')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    request_data = models.JSONField(default=dict, blank=True)
    response_status = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='resolved_errors'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Error Log'
        verbose_name_plural = 'Error Logs'
        indexes = [
            models.Index(fields=['error_type', 'created_at']),
            models.Index(fields=['severity', 'created_at']),
            models.Index(fields=['resolved', 'created_at']),
            models.Index(fields=['ip_address', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.error_type} - {self.severity} - {self.created_at}"
    
    def get_created_at_ist(self):
        """Get creation time in IST"""
        if self.created_at:
            ist = pytz.timezone('Asia/Kolkata')
            if timezone.is_aware(self.created_at):
                ist_time = self.created_at.astimezone(ist)
            else:
                ist_time = ist.localize(self.created_at)
            return ist_time.strftime('%B %d, %Y, %I:%M %p IST')
        return "-"
    
    def get_resolved_at_ist(self):
        """Get resolution time in IST"""
        if self.resolved_at:
            ist = pytz.timezone('Asia/Kolkata')
            if timezone.is_aware(self.resolved_at):
                ist_time = self.resolved_at.astimezone(ist)
            else:
                ist_time = ist.localize(self.resolved_at)
            return ist_time.strftime('%B %d, %Y, %I:%M %p IST')
        return "-"
    
    def get_short_error_message(self, length=100):
        """Get truncated error message for display"""
        if len(self.error_message) <= length:
            return self.error_message
        return self.error_message[:length] + '...'
    
    def is_critical(self):
        """Check if error is critical"""
        return self.severity == 'critical'
    
    def get_severity_color(self):
        """Get color code for severity level"""
        colors = {
            'low': '#28a745',      # Green
            'medium': '#ffc107',   # Yellow
            'high': '#fd7e14',     # Orange
            'critical': '#dc3545'  # Red
        }
        return colors.get(self.severity, '#6c757d')

class SystemMetrics(models.Model):
    """System performance metrics"""
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    cpu_usage = models.FloatField(help_text="CPU usage percentage")
    memory_usage = models.FloatField(help_text="Memory usage percentage")
    disk_usage = models.FloatField(help_text="Disk usage percentage")
    active_sessions = models.IntegerField(help_text="Number of active user sessions")
    total_requests = models.IntegerField(help_text="Total requests in the period")
    error_rate = models.FloatField(help_text="Error rate percentage")
    avg_response_time = models.FloatField(help_text="Average response time in milliseconds")
    uptime = models.BigIntegerField(help_text="System uptime in seconds")
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'System Metrics'
        verbose_name_plural = 'System Metrics'
        indexes = [
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"Metrics - {self.timestamp}"
    
    def get_timestamp_ist(self):
        """Get timestamp in IST"""
        if self.timestamp:
            ist = pytz.timezone('Asia/Kolkata')
            if timezone.is_aware(self.timestamp):
                ist_time = self.timestamp.astimezone(ist)
            else:
                ist_time = ist.localize(self.timestamp)
            return ist_time.strftime('%B %d, %Y, %I:%M %p IST')
        return "-"
    
    def get_uptime_display(self):
        """Display uptime in human readable format"""
        if self.uptime:
            days = self.uptime // 86400
            hours = (self.uptime % 86400) // 3600
            minutes = (self.uptime % 3600) // 60
            
            if days > 0:
                return f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
        return "-"
    
    def get_avg_response_time_display(self):
        """Display response time in human readable format"""
        if self.avg_response_time:
            if self.avg_response_time < 1000:
                return f"{self.avg_response_time:.0f}ms"
            else:
                return f"{self.avg_response_time/1000:.1f}s"
        return "-"

# Utility functions for tracking
def get_client_ip(request):
    """Get the client's IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_device_type(user_agent):
    """Determine device type from user agent"""
    if not user_agent:
        return 'unknown'
    
    user_agent = user_agent.lower()
    if any(mobile in user_agent for mobile in ['mobile', 'android', 'iphone', 'ipod']):
        return 'mobile'
    elif any(tablet in user_agent for tablet in ['tablet', 'ipad']):
        return 'tablet'
    else:
        return 'desktop'

def get_browser(user_agent):
    """Extract browser from user agent"""
    if not user_agent:
        return 'Unknown'
    
    user_agent = user_agent.lower()
    if 'edg' in user_agent:  # Edge (new)
        return 'Edge'
    elif 'chrome' in user_agent and 'safari' in user_agent:
        return 'Chrome'
    elif 'firefox' in user_agent:
        return 'Firefox'
    elif 'safari' in user_agent and 'chrome' not in user_agent:
        return 'Safari'
    elif 'opera' in user_agent or 'opr' in user_agent:
        return 'Opera'
    elif 'msie' in user_agent or 'trident' in user_agent:
        return 'Internet Explorer'
    else:
        return 'Other'

def track_activity(request, activity_type, tool_name=None, file_name=None, 
                  file_size=None, file_type=None, processing_time=None, 
                  status='success', error_message=None, additional_data=None):
    """Helper function to track user activity"""
    try:
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()
        
        session_id = request.session.session_key
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        activity = UserActivity.objects.create(
            session_id=session_id,
            user=request.user if request.user.is_authenticated else None,
            activity_type=activity_type,
            page_url=request.build_absolute_uri(),
            tool_name=tool_name,
            file_name=file_name,
            file_size=file_size,
            file_type=file_type,
            processing_time=processing_time,
            status=status,
            error_message=error_message,
            ip_address=get_client_ip(request),
            user_agent=user_agent,
            referer=request.META.get('HTTP_REFERER'),
            device_type=get_device_type(user_agent),
            browser=get_browser(user_agent),
            additional_data=additional_data or {}
        )
        return activity
    except Exception as e:
        # Silent fail - don't break the app if tracking fails
        print(f"Failed to track activity: {str(e)}")
        return None

def log_error(request, error_type, error_message, stack_trace=None, 
              severity='medium', additional_data=None):
    """Helper function to log errors"""
    try:
        session_id = getattr(request.session, 'session_key', None) or 'anonymous'
        
        error_log = ErrorLog.objects.create(
            session_id=session_id,
            user=request.user if hasattr(request, 'user') and request.user.is_authenticated else None,
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace,
            severity=severity,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            request_data={
                'method': request.method,
                'path': request.path,
                'GET': dict(request.GET),
                'POST': dict(request.POST) if request.method == 'POST' else {},
            }
        )
        return error_log
    except Exception as e:
        # Silent fail - don't break the app if error logging fails
        print(f"Failed to log error: {str(e)}")
        return None