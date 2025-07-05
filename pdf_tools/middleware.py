# pdf_tools/middleware.py

from django.utils import timezone
from django.contrib.auth.models import User
from .models import UserActivity, ErrorLog
import uuid
import json

def get_client_ip(request):
    """Get the client's IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_device_type(user_agent):
    """Determine device type from user agent"""
    user_agent = user_agent.lower()
    if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
        return 'mobile'
    elif 'tablet' in user_agent or 'ipad' in user_agent:
        return 'tablet'
    else:
        return 'desktop'

def get_browser(user_agent):
    """Extract browser from user agent"""
    user_agent = user_agent.lower()
    if 'chrome' in user_agent:
        return 'Chrome'
    elif 'firefox' in user_agent:
        return 'Firefox'
    elif 'safari' in user_agent:
        return 'Safari'
    elif 'edge' in user_agent:
        return 'Edge'
    else:
        return 'Other'

def track_activity(request, activity_type, tool_name=None, file_name=None, 
                  file_size=None, file_type=None, processing_time=None, 
                  status='success', error_message=None, additional_data=None):
    """Helper function to track user activity"""
    
    session_id = request.session.session_key or request.session.create()
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    try:
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
    
    session_id = request.session.session_key or 'anonymous'
    
    try:
        error_log = ErrorLog.objects.create(
            session_id=session_id,
            user=request.user if request.user.is_authenticated else None,
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

class ActivityTrackingMiddleware:
    """Middleware to automatically track user activities"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Track page view for non-admin, non-API pages
        if not request.path.startswith('/admin/') and not request.path.startswith('/api/'):
            track_activity(
                request, 
                'page_view',
                additional_data={'path': request.path}
            )
        
        response = self.get_response(request)
        
        # Track errors (4xx, 5xx status codes)
        if response.status_code >= 400:
            log_error(
                request,
                f'HTTP_{response.status_code}',
                f'HTTP error {response.status_code} on {request.path}',
                severity='high' if response.status_code >= 500 else 'medium'
            )
        
        return response