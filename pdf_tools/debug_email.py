import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings

def test_email_connection():
    """Test the email connection and settings"""
    try:
        # Create a test email
        msg = MIMEMultipart()
        msg['From'] = settings.EMAIL_HOST_USER
        msg['To'] = settings.ADMIN_EMAIL
        msg['Subject'] = 'Test Email Connection'
        
        body = 'This is a test email to verify SMTP connection.'
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect to SMTP server
        server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
        server.ehlo()
        
        # Start TLS if required
        if settings.EMAIL_USE_TLS:
            server.starttls()
            server.ehlo()
        
        # Login if credentials provided
        if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        
        # Send email
        text = msg.as_string()
        server.sendmail(settings.EMAIL_HOST_USER, settings.ADMIN_EMAIL, text)
        
        # Close connection
        server.quit()
        
        return {
            'success': True,
            'message': 'Email connection successful',
            'settings': {
                'EMAIL_HOST': settings.EMAIL_HOST,
                'EMAIL_PORT': settings.EMAIL_PORT,
                'EMAIL_USE_TLS': settings.EMAIL_USE_TLS,
                'EMAIL_HOST_USER': settings.EMAIL_HOST_USER,
                'EMAIL_HOST_PASSWORD': '********' if settings.EMAIL_HOST_PASSWORD else None,
                'DEFAULT_FROM_EMAIL': settings.DEFAULT_FROM_EMAIL,
                'ADMIN_EMAIL': settings.ADMIN_EMAIL
            }
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'settings': {
                'EMAIL_HOST': settings.EMAIL_HOST,
                'EMAIL_PORT': settings.EMAIL_PORT,
                'EMAIL_USE_TLS': settings.EMAIL_USE_TLS,
                'EMAIL_HOST_USER': settings.EMAIL_HOST_USER,
                'EMAIL_HOST_PASSWORD': '********' if settings.EMAIL_HOST_PASSWORD else None,
                'DEFAULT_FROM_EMAIL': settings.DEFAULT_FROM_EMAIL,
                'ADMIN_EMAIL': settings.ADMIN_EMAIL
            }
        }
