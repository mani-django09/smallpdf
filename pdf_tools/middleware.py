# pdf_tools/middleware.py - Enhanced version

from django.utils import timezone
from django.contrib.auth.models import User
from .models import UserActivity, ErrorLog
import uuid
import json
import time
import traceback

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

def get_country_from_ip(ip_address):
    """Get country from IP address (basic implementation)"""
    # You can integrate with a GeoIP service here
    # For now, return None
    return None

def extract_tool_name_from_path(path):
    """Extract tool name from request path"""
    tool_mappings = {
        'merge-pdf': 'Merge PDF',
        'compress-pdf': 'Compress PDF',
        'pdf-to-word': 'PDF to Word',
        'word-to-pdf': 'Word to PDF',
        'pdf-to-jpg': 'PDF to JPG',
        'jpg-to-pdf': 'JPG to PDF',
        'webp-to-png': 'WebP to PNG',
        'png-to-webp': 'PNG to WebP',
        'pdf-to-png': 'PDF to PNG',
        'png-to-pdf': 'PNG to PDF',
        'split-pdf': 'Split PDF',
        'compress-image': 'Compress Image',
        'convert-pdf': 'Convert PDF',
    }
    
    for key, value in tool_mappings.items():
        if key in path:
            return value
    
    return 'Unknown Tool'

# Replace the track_activity function in your models.py with this fixed version:

def track_activity(request, activity_type, tool_name=None, file_name=None, 
                  file_size=None, file_type=None, processing_time=None, 
                  status='success', error_message=None, additional_data=None):
    """Helper function to track user activity - FIXED VERSION"""
    try:
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()
        
        session_id = request.session.session_key
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Prepare additional_data for the JSONField
        if additional_data is None:
            additional_data = {}
        
        # Add some default data
        additional_data.update({
            'path': request.path,
            'method': request.method
        })
        
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
            additional_data=additional_data
        )
        return activity
    except Exception as e:
        # Silent fail - don't break the app if tracking fails
        print(f"Failed to track activity: {str(e)}")
        return None
def log_error(request, error_type, error_message, stack_trace=None, 
              severity='medium', additional_data=None):
    """Enhanced helper function to log errors"""
    
    try:
        session_id = getattr(request, 'session', {}).get('session_key', 'anonymous')
        if not session_id and hasattr(request, 'session'):
            session_id = request.session.session_key or 'anonymous'
        
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        ip_address = get_client_ip(request)
        
        # Prepare request data
        request_data = {
            'method': request.method,
            'path': request.path,
            'GET': dict(request.GET),
        }
        
        # Only add POST data if it's not file upload (to avoid large data)
        if request.method == 'POST':
            try:
                if request.content_type != 'multipart/form-data':
                    request_data['POST'] = dict(request.POST)
                else:
                    request_data['POST'] = {'files': list(request.FILES.keys())}
            except:
                request_data['POST'] = {'error': 'Could not parse POST data'}
        
        error_log = ErrorLog.objects.create(
            session_id=session_id,
            user=request.user if hasattr(request, 'user') and request.user.is_authenticated else None,
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace or traceback.format_exc(),
            severity=severity,
            ip_address=ip_address,
            user_agent=user_agent,
            request_data=request_data,
            additional_data=additional_data or {}
        )
        
        # Print for debugging (remove in production)
        print(f"🚨 Logged Error: {error_type} - {severity} - {error_message[:100]}")
        return error_log
        
    except Exception as e:
        # Enhanced error handling
        print(f"❌ Failed to log error: {str(e)}")
        print(f"   Original Error Type: {error_type}")
        print(f"   Original Error Message: {error_message}")
        print(f"   Logging Error Details: {traceback.format_exc()}")
        return None

class ActivityTrackingMiddleware:
    """Fixed middleware to automatically track user activities"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Track page view (only for non-admin, non-api pages)
        if (not request.path.startswith('/admin/') and 
            not request.path.startswith('/api/') and
            not request.path.startswith('/static/') and
            not request.path.startswith('/media/')):
            
            try:
                track_activity(
                    request, 
                    'page_view',
                    status='success'
                )
                print(f"✅ Tracked Activity: page_view - {request.path} - success")
            except Exception as e:
                print(f"❌ Failed to track activity: {str(e)}")
        
        response = self.get_response(request)
        
        # Track errors (4xx, 5xx status codes) - FIXED VERSION
        if response.status_code >= 400:
            try:
                # Determine severity based on status code
                if response.status_code >= 500:
                    severity = 'high'
                elif response.status_code == 404:
                    severity = 'low'  # 404s are usually not critical
                else:
                    severity = 'medium'
                
                log_error(
                    request,
                    f'HTTP_{response.status_code}',
                    f'HTTP {response.status_code} error on {request.path}',
                    severity=severity
                    # Removed additional_data parameter that was causing the error
                )
                print(f"✅ Logged Error: HTTP_{response.status_code} - {request.path}")
            except Exception as e:
                print(f"❌ Failed to log error: {str(e)}")
                print(f"   Original Error Type: HTTP_{response.status_code}")
                print(f"   Original Error Message: HTTP {response.status_code} error on {request.path}")
                print(f"   Logging Error Details: {str(e)}")
        
        return response

    def process_exception(self, request, exception):
        """Track unhandled exceptions"""
        try:
            tool_name = None
            if '/api/' in request.path:
                tool_name = extract_tool_name_from_path(request.path)
            
            log_error(
                request,
                'UNHANDLED_EXCEPTION',
                str(exception),
                stack_trace=traceback.format_exc(),
                severity='critical',
                additional_data={
                    'exception_type': type(exception).__name__,
                    'tool_name': tool_name
                }
            )
            
            # Also track as failed activity
            if tool_name:
                track_activity(
                    request,
                    'error',
                    tool_name=tool_name,
                    status='error',
                    error_message=str(exception)
                )
                
        except Exception as e:
            print(f"Error in exception tracking: {str(e)}")
        
        # Don't suppress the exception
        return None