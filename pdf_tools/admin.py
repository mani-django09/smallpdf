# pdf_tools/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.utils.dateformat import format as date_format
import pytz
import csv
from django.http import HttpResponse
from .models import (
    PDFTool, ProcessedFile, ContactMessage, ContactSettings,
    UserActivity, ErrorLog, SystemMetrics
)

def format_ist_datetime(dt):
    """Convert datetime to IST and format it nicely"""
    if dt:
        # Convert to IST
        ist = pytz.timezone('Asia/Kolkata')
        if timezone.is_aware(dt):
            ist_time = dt.astimezone(ist)
        else:
            ist_time = ist.localize(dt)
        
        # Format as: June 19, 2025, 7:46 PM IST
        return ist_time.strftime('%B %d, %Y, %I:%M %p IST')
    return "-"

@admin.register(PDFTool)
class PDFToolAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_featured', 'order']
    list_editable = ['is_featured', 'order']
    list_filter = ['is_featured']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']

@admin.register(ProcessedFile)
class ProcessedFileAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'tool_used', 'file_size_display', 'processed_at_ist', 'success']
    list_filter = ['tool_used', 'success', 'processed_at']
    search_fields = ['file_name']
    readonly_fields = ['processed_at', 'processed_at_ist']
    date_hierarchy = 'processed_at'
    
    def processed_at_ist(self, obj):
        """Display processing time in IST"""
        return format_ist_datetime(obj.processed_at)
    processed_at_ist.short_description = 'Processed At (IST)'
    processed_at_ist.admin_order_field = 'processed_at'
    
    def file_size_display(self, obj):
        """Display file size in human readable format"""
        if obj.file_size:
            size = obj.file_size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
        return "Unknown"
    file_size_display.short_description = 'File Size'

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 
        'email', 
        'subject', 
        'category', 
        'status',        # Added status to list_display
        'priority',      # Added priority to list_display
        'created_at_ist',
        'age_display'
    ]
    
    list_filter = [
        'status', 
        'priority', 
        'category', 
        'created_at',
    ]
    
    search_fields = [
        'full_name', 
        'email', 
        'subject', 
        'message', 
        'company'
    ]
    
    readonly_fields = [
        'id', 
        'created_at', 
        'created_at_ist',
        'updated_at', 
        'updated_at_ist',
        'ip_address', 
        'user_agent',
        'age_display',
        'attachment_link'
    ]
    
    list_editable = ['status', 'priority']  # Now these are in list_display
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    actions = ['mark_as_resolved', 'mark_as_closed', 'export_as_csv']
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('full_name', 'email', 'company', 'phone')
        }),
        ('Message Details', {
            'fields': ('subject', 'category', 'message', 'attachment', 'attachment_link')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority', 'assigned_to')
        }),
        ('Admin Notes', {
            'fields': ('admin_notes',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'created_at_ist', 'updated_at', 'updated_at_ist', 'age_display', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    def created_at_ist(self, obj):
        """Display creation time in IST"""
        return format_ist_datetime(obj.created_at)
    created_at_ist.short_description = 'Created At (IST)'
    created_at_ist.admin_order_field = 'created_at'
    
    def updated_at_ist(self, obj):
        """Display update time in IST"""
        return format_ist_datetime(obj.updated_at)
    updated_at_ist.short_description = 'Updated At (IST)'
    
    def age_display(self, obj):
        return obj.get_age()
    age_display.short_description = 'Age'
    
    def attachment_link(self, obj):
        if obj.attachment:
            return format_html(
                '<a href="{}" target="_blank">Download Attachment</a>',
                obj.attachment.url
            )
        return "No attachment"
    attachment_link.short_description = 'Attachment'
    
    def mark_as_resolved(self, request, queryset):
        count = queryset.update(status='resolved')
        self.message_user(request, f'{count} messages marked as resolved.')
    mark_as_resolved.short_description = 'Mark selected messages as resolved'
    
    def mark_as_closed(self, request, queryset):
        count = queryset.update(status='closed')
        self.message_user(request, f'{count} messages marked as closed.')
    mark_as_closed.short_description = 'Mark selected messages as closed'
    
    def export_as_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="contact_messages.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Name', 'Email', 'Company', 'Phone', 'Subject', 
            'Category', 'Status', 'Priority', 'Created', 'Message'
        ])
        
        for message in queryset:
            writer.writerow([
                message.full_name,
                message.email,
                message.company or '',
                message.phone or '',
                message.subject,
                message.get_category_display(),
                message.get_status_display(),
                message.get_priority_display(),
                message.created_at.strftime('%Y-%m-%d %H:%M'),
                message.message[:100] + '...' if len(message.message) > 100 else message.message
            ])
        
        return response
    export_as_csv.short_description = 'Export selected messages as CSV'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()

@admin.register(ContactSettings)
class ContactSettingsAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'office_email', 'office_phone', 'auto_response_enabled']
    
    fieldsets = (
        ('Office Information', {
            'fields': ('office_address', 'office_phone', 'office_email')
        }),
        ('Business Hours', {
            'fields': ('business_hours_weekdays', 'business_hours_saturday', 'business_hours_sunday')
        }),
        ('Social Media', {
            'fields': ('facebook_url', 'twitter_url', 'linkedin_url', 'instagram_url'),
            'classes': ('collapse',)
        }),
        ('Notification Settings', {
            'fields': ('auto_response_enabled', 'response_time_hours', 'admin_notification_enabled', 'admin_email'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def has_add_permission(self, request):
        return not ContactSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = [
        'activity_type', 'tool_name', 'status', 'ip_address', 
        'device_type', 'browser', 'created_at_ist'
    ]
    list_filter = [
        'activity_type', 'status', 'tool_name', 'device_type', 
        'browser', 'created_at'
    ]
    search_fields = ['ip_address', 'tool_name', 'file_name', 'page_url']
    readonly_fields = [
        'id', 'session_id', 'created_at', 'created_at_ist', 'ip_address', 'user_agent',
        'referer', 'country', 'device_type', 'browser'
    ]
    date_hierarchy = 'created_at'
    
    def created_at_ist(self, obj):
        """Display creation time in IST"""
        return format_ist_datetime(obj.created_at)
    created_at_ist.short_description = 'Created At (IST)'
    created_at_ist.admin_order_field = 'created_at'
    
    fieldsets = (
        ('Activity Information', {
            'fields': ('activity_type', 'tool_name', 'status', 'page_url')
        }),
        ('File Information', {
            'fields': ('file_name', 'file_size', 'file_type', 'processing_time'),
            'classes': ('collapse',)
        }),
        ('User Information', {
            'fields': ('user', 'session_id', 'ip_address', 'country', 'device_type', 'browser'),
            'classes': ('collapse',)
        }),
        ('Technical Details', {
            'fields': ('user_agent', 'referer', 'error_message', 'additional_data'),
            'classes': ('collapse',)
        }),
        ('System', {
            'fields': ('id', 'created_at', 'created_at_ist'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False

@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = [
        'error_type', 'severity', 'ip_address', 'resolved', 
        'created_at_ist', 'resolved_by'
    ]
    list_filter = ['severity', 'resolved', 'error_type', 'created_at']
    search_fields = ['error_type', 'error_message', 'ip_address']
    readonly_fields = [
        'id', 'session_id', 'created_at', 'created_at_ist', 'ip_address', 'user_agent',
        'request_data', 'response_status', 'resolved_at_ist'
    ]
    list_editable = ['resolved']
    date_hierarchy = 'created_at'
    actions = ['mark_resolved']
    
    def created_at_ist(self, obj):
        """Display creation time in IST"""
        return format_ist_datetime(obj.created_at)
    created_at_ist.short_description = 'Created At (IST)'
    created_at_ist.admin_order_field = 'created_at'
    
    def resolved_at_ist(self, obj):
        """Display resolution time in IST"""
        return format_ist_datetime(obj.resolved_at)
    resolved_at_ist.short_description = 'Resolved At (IST)'
    
    def mark_resolved(self, request, queryset):
        queryset.update(resolved=True, resolved_at=timezone.now(), resolved_by=request.user)
    mark_resolved.short_description = "Mark selected errors as resolved"
    
    fieldsets = (
        ('Error Information', {
            'fields': ('error_type', 'error_message', 'severity', 'stack_trace')
        }),
        ('Resolution', {
            'fields': ('resolved', 'resolved_at', 'resolved_at_ist', 'resolved_by')
        }),
        ('User Information', {
            'fields': ('user', 'session_id', 'ip_address'),
            'classes': ('collapse',)
        }),
        ('Technical Details', {
            'fields': ('file_path', 'line_number', 'function_name', 'user_agent', 'request_data', 'response_status'),
            'classes': ('collapse',)
        }),
        ('System', {
            'fields': ('id', 'created_at', 'created_at_ist'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if 'resolved' in form.changed_data and obj.resolved:
            obj.resolved_at = timezone.now()
            obj.resolved_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(SystemMetrics)
class SystemMetricsAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp_ist', 'cpu_usage', 'memory_usage', 'disk_usage',
        'active_sessions', 'total_requests', 'error_rate'
    ]
    list_filter = ['timestamp']
    readonly_fields = [
        'timestamp', 'timestamp_ist', 'cpu_usage', 'memory_usage', 'disk_usage',
        'active_sessions', 'total_requests', 'error_rate',
        'avg_response_time', 'uptime'
    ]
    date_hierarchy = 'timestamp'
    
    def timestamp_ist(self, obj):
        """Display timestamp in IST"""
        return format_ist_datetime(obj.timestamp)
    timestamp_ist.short_description = 'Timestamp (IST)'
    timestamp_ist.admin_order_field = 'timestamp'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

# Customize admin site
admin.site.site_header = "SmallPDF.us Administration"
admin.site.site_title = "SmallPDF.us Admin"
admin.site.index_title = "Welcome to SmallPDF.us Administration"