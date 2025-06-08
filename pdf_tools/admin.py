# admin.py - Add these to your existing admin.py file

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import ContactMessage, ContactSettings
import csv
from django.http import HttpResponse

class ContactMessageAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 
        'email', 
        'subject', 
        'category', 
        'status_badge', 
        'priority_badge', 
        'created_at',
        'age_display'
    ]
    
    list_filter = [
        'status', 
        'priority', 
        'category', 
        'created_at',
        ('created_at', admin.DateFieldListFilter),
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
        'updated_at', 
        'ip_address', 
        'user_agent',
        'age_display',
        'attachment_link'
    ]
    
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
            'fields': ('id', 'created_at', 'updated_at', 'age_display', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    actions = ['mark_as_resolved', 'mark_as_closed', 'export_as_csv']
    
    def status_badge(self, obj):
        colors = {
            'new': 'red',
            'in_progress': 'orange', 
            'resolved': 'green',
            'closed': 'gray'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def priority_badge(self, obj):
        colors = {
            'urgent': '#dc3545',
            'high': '#fd7e14',
            'normal': '#28a745',
            'low': '#6c757d'
        }
        color = colors.get(obj.priority, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'
    priority_badge.admin_order_field = 'priority'
    
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


class ContactSettingsAdmin(admin.ModelAdmin):
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
        # Only allow one instance
        return not ContactSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of settings
        return False


# Register the models
admin.site.register(ContactMessage, ContactMessageAdmin)
admin.site.register(ContactSettings, ContactSettingsAdmin)

# Customize admin site headers
admin.site.site_header = "SmallPDF.us Administration"
admin.site.site_title = "SmallPDF.us Admin"
admin.site.index_title = "Welcome to SmallPDF.us Administration"