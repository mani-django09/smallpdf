from django.db import models
from django.utils import timezone
from django.urls import reverse

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
    
    def __str__(self):
        return f"{self.file_name} - {self.tool_used.name}"

# 4. Views.py - Homepage and Tool Views
# pdf_tools/views.py
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, TemplateView
from .models import PDFTool

class HomePageView(TemplateView):
    template_name = "pdf_tools/home.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_tools'] = PDFTool.objects.filter(is_featured=True).order_by('order')
        context['all_tools'] = PDFTool.objects.all().order_by('order')
        return context

class ToolDetailView(DetailView):
    model = PDFTool
    template_name = "pdf_tools/tool_pages/tool_detail.html"
    context_object_name = "tool"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add more tools for the sidebar
        context['related_tools'] = PDFTool.objects.exclude(pk=self.object.pk)[:5]
        return context


from django.db import models
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import uuid

class ContactMessage(models.Model):
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
    
    def __str__(self):
        return f"{self.full_name} - {self.subject}"
    
    def get_age(self):
        now = timezone.now()
        diff = now - self.created_at
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

class ContactSettings(models.Model):
    office_address = models.TextField(default="123 Tech Hub Drive\nSuite 456\nSan Francisco, CA 94107\nUnited States")
    office_phone = models.CharField(max_length=20, default="+1 (555) SMALL-PDF")
    office_email = models.EmailField(default="support@smallpdf.us")
    business_hours_weekdays = models.CharField(max_length=50, default="Monday - Friday: 9:00 AM - 6:00 PM (EST)")
    business_hours_saturday = models.CharField(max_length=50, default="Saturday: 10:00 AM - 4:00 PM (EST)")
    business_hours_sunday = models.CharField(max_length=50, default="Sunday: Closed")
    facebook_url = models.URLField(blank=True, null=True)
    twitter_url = models.URLField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    instagram_url = models.URLField(blank=True, null=True)
    auto_response_enabled = models.BooleanField(default=True)
    response_time_hours = models.IntegerField(default=4)
    admin_notification_enabled = models.BooleanField(default=True)
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
        settings, created = cls.objects.get_or_create(pk=1)
        return settings