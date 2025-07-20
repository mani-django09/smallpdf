# pdf_tools/admin.py - FIXED VERSION
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.utils.dateformat import format as date_format
from django.db.models import Count, Avg, Sum, Q
from django.http import JsonResponse, HttpResponse
from datetime import datetime, timedelta
import pytz
import csv
import json
from .models import (
    PDFTool, ProcessedFile, ContactMessage, ContactSettings,
    UserActivity, ErrorLog, SystemMetrics
)

def format_ist_datetime(dt):
    """Convert datetime to IST and format it nicely"""
    if dt:
        ist = pytz.timezone('Asia/Kolkata')
        if timezone.is_aware(dt):
            ist_time = dt.astimezone(ist)
        else:
            ist_time = ist.localize(dt)
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
        'status',
        'priority',
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
    
    list_editable = ['status', 'priority']
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
        'activity_type_badge', 
        'tool_name_link', 
        'file_info', 
        'status_badge',
        'device_browser_info',
        'ip_location',
        'processing_time_display',
        'created_at_ist'
    ]
    
    list_filter = [
        'activity_type', 
        'status', 
        'tool_name', 
        'device_type', 
        'browser',
        ('created_at', admin.DateFieldListFilter),
    ]
    
    search_fields = [
        'ip_address', 
        'tool_name', 
        'file_name', 
        'session_id',
        'error_message'
    ]
    
    readonly_fields = [
        'id', 'session_id', 'created_at', 'created_at_ist', 'ip_address',
        'user_agent', 'referer', 'country', 'device_type', 'browser',
        'processing_time_display', 'file_size_display'
    ]
    
    date_hierarchy = 'created_at'
    list_per_page = 50
    actions = ['mark_for_review', 'export_selected_activities']
    
    fieldsets = (
        ('Activity Information', {
            'fields': ('activity_type', 'tool_name', 'status', 'page_url'),
            'classes': ('wide',)
        }),
        ('File Details', {
            'fields': ('file_name', 'file_size', 'file_size_display', 'file_type', 'processing_time', 'processing_time_display'),
            'classes': ('collapse',)
        }),
        ('User Information', {
            'fields': ('user', 'session_id', 'ip_address', 'country'),
            'classes': ('collapse',)
        }),
        ('Technical Details', {
            'fields': ('device_type', 'browser', 'user_agent', 'referer'),
            'classes': ('collapse',)
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'created_at_ist', 'additional_data'),
            'classes': ('collapse',)
        }),
    )
    
    def activity_type_badge(self, obj):
        """Display activity type with colored badge"""
        colors = {
            'page_view': 'primary',
            'tool_access': 'success',
            'file_upload': 'warning',
            'file_process': 'info',
            'file_download': 'secondary',
            'error': 'danger',
        }
        color = colors.get(obj.activity_type, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color,
            obj.get_activity_type_display()
        )
    activity_type_badge.short_description = 'Activity Type'
    
    def tool_name_link(self, obj):
        """Display tool name with link to tool-specific activities"""
        if obj.tool_name:
            url = reverse('admin:pdf_tools_useractivity_changelist') + f'?tool_name={obj.tool_name}'
            return format_html('<a href="{}">{}</a>', url, obj.tool_name)
        return '-'
    tool_name_link.short_description = 'Tool'
    
    def file_info(self, obj):
        """Display file information in compact format"""
        if obj.file_name:
            size_info = obj.get_file_size_display()
            return format_html(
                '<div><strong>{}</strong><br><small>{}</small></div>',
                obj.file_name[:30] + '...' if len(obj.file_name) > 30 else obj.file_name,
                size_info
            )
        return '-'
    file_info.short_description = 'File Info'
    
    def status_badge(self, obj):
        """Display status with colored badge"""
        colors = {
            'success': 'success',
            'failed': 'danger',
            'pending': 'warning',
            'error': 'danger',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color,
            obj.status.title()
        )
    status_badge.short_description = 'Status'
    
    def device_browser_info(self, obj):
        """Display device and browser info"""
        return format_html(
            '<div>{}<br><small>{}</small></div>',
            obj.device_type.title() if obj.device_type else 'Unknown',
            obj.browser or 'Unknown'
        )
    device_browser_info.short_description = 'Device/Browser'
    
    def ip_location(self, obj):
        """Display IP and location info"""
        return format_html(
            '<div><strong>{}</strong><br><small>{}</small></div>',
            obj.ip_address,
            obj.country or 'Unknown'
        )
    ip_location.short_description = 'IP/Location'
    
    def processing_time_display(self, obj):
        """Display processing time"""
        return obj.get_processing_time_display()
    processing_time_display.short_description = 'Processing Time'
    
    def file_size_display(self, obj):
        """Display file size"""
        return obj.get_file_size_display()
    file_size_display.short_description = 'File Size'
    
    def created_at_ist(self, obj):
        """Display creation time in IST"""
        return format_ist_datetime(obj.created_at)
    created_at_ist.short_description = 'Time (IST)'
    created_at_ist.admin_order_field = 'created_at'
    
    def mark_for_review(self, request, queryset):
        """Mark activities for manual review"""
        count = queryset.count()
        self.message_user(request, f'{count} activities marked for review.')
    mark_for_review.short_description = 'Mark selected activities for review'
    
    def export_selected_activities(self, request, queryset):
        """Export selected activities to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="user_activities.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Activity Type', 'Tool Name', 'File Name', 'File Size', 'Status',
            'Processing Time', 'IP Address', 'Device Type', 'Browser',
            'Country', 'Created At', 'Error Message'
        ])
        
        for activity in queryset:
            writer.writerow([
                activity.get_activity_type_display(),
                activity.tool_name or '',
                activity.file_name or '',
                activity.get_file_size_display(),
                activity.status,
                activity.get_processing_time_display(),
                activity.ip_address,
                activity.device_type or '',
                activity.browser or '',
                activity.country or '',
                activity.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                activity.error_message or ''
            ])
        
        return response
    export_selected_activities.short_description = 'Export selected activities as CSV'
    
    def has_add_permission(self, request):
        return False

@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = [
        'error_type_badge',
        'severity_badge', 
        'error_preview',
        'ip_address',
        'affected_tool',
        'resolved_status',
        'created_at_ist',
        'resolution_info'
    ]
    
    list_filter = [
        'severity', 
        'resolved', 
        'error_type',
        ('created_at', admin.DateFieldListFilter),
        ('resolved_at', admin.DateFieldListFilter),
    ]
    
    search_fields = [
        'error_type', 
        'error_message', 
        'ip_address',
        'stack_trace'
    ]
    
    readonly_fields = [
        'id', 'session_id', 'created_at', 'created_at_ist', 'ip_address',
        'user_agent', 'request_data', 'response_status', 'resolved_at_ist'
    ]
    
    date_hierarchy = 'created_at'
    actions = ['mark_resolved', 'assign_high_priority', 'export_error_report']
    
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
    
    def error_type_badge(self, obj):
        """Display error type with badge"""
        return format_html(
            '<span class="badge badge-danger">{}</span>',
            obj.error_type
        )
    error_type_badge.short_description = 'Error Type'
    
    def severity_badge(self, obj):
        """Display severity with colored badge"""
        colors = {
            'low': 'success',
            'medium': 'warning',
            'high': 'danger',
            'critical': 'dark',
        }
        color = colors.get(obj.severity, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color,
            obj.severity.title()
        )
    severity_badge.short_description = 'Severity'
    
    def error_preview(self, obj):
        """Display error message preview"""
        preview = obj.get_short_error_message(80)
        return format_html(
            '<div title="{}">{}</div>',
            obj.error_message,
            preview
        )
    error_preview.short_description = 'Error Message'
    
    def affected_tool(self, obj):
        """Extract tool information from request data"""
        if obj.request_data and 'path' in obj.request_data:
            path = obj.request_data['path']
            if 'pdf-to-word' in path:
                return 'PDF to Word'
            elif 'merge-pdf' in path:
                return 'Merge PDF'
            elif 'compress-pdf' in path:
                return 'Compress PDF'
            elif 'pdf-to-jpg' in path:
                return 'PDF to JPG'
            elif 'jpg-to-pdf' in path:
                return 'JPG to PDF'
        return 'Unknown'
    affected_tool.short_description = 'Affected Tool'
    
    def resolved_status(self, obj):
        """Display resolution status with badge"""
        if obj.resolved:
            return format_html(
                '<span class="badge badge-success">✓ Resolved</span>'
            )
        else:
            return format_html(
                '<span class="badge badge-warning">⚠ Open</span>'
            )
    resolved_status.short_description = 'Status'
    
    def resolution_info(self, obj):
        """Display resolution information"""
        if obj.resolved and obj.resolved_by:
            return format_html(
                '<div>By: {}<br><small>{}</small></div>',
                obj.resolved_by.username,
                format_ist_datetime(obj.resolved_at)
            )
        return '-'
    resolution_info.short_description = 'Resolution Info'
    
    def created_at_ist(self, obj):
        """Display creation time in IST"""
        return format_ist_datetime(obj.created_at)
    created_at_ist.short_description = 'Occurred At (IST)'
    created_at_ist.admin_order_field = 'created_at'
    
    def resolved_at_ist(self, obj):
        """Display resolution time in IST"""
        return format_ist_datetime(obj.resolved_at)
    resolved_at_ist.short_description = 'Resolved At (IST)'
    
    def mark_resolved(self, request, queryset):
        queryset.update(resolved=True, resolved_at=timezone.now(), resolved_by=request.user)
    mark_resolved.short_description = "Mark selected errors as resolved"
    
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

# Add custom admin views URLs
from django.urls import path
from django.contrib.admin import AdminSite

def get_admin_urls():
    """Get custom admin URLs"""
    from . import views
    return [
        path('analytics/', views.admin_dashboard, name='admin_analytics'),
        path('real-time/', views.real_time_monitor, name='admin_real_time'),
        path('api/live-data/', views.live_data_api, name='admin_live_data'),
        path('activities/', views.user_activity_detail, name='admin_activities'),
        path('errors/', views.error_log_detail, name='admin_errors'),
        path('conversion-stats/', views.conversion_statistics, name='admin_conversion_stats'),
        path('export/activities/', views.export_activities, name='admin_export_activities'),
        path('export/errors/', views.export_errors, name='admin_export_errors'),
        path('resolve-error/<uuid:error_id>/', views.resolve_error, name='admin_resolve_error'),
    ]

# Extend the default admin site
original_get_urls = admin.site.get_urls

def get_urls():
    urls = original_get_urls()
    custom_urls = get_admin_urls()
    return custom_urls + urls

admin.site.get_urls = get_urls