# In your urls.py file, add these lines to your existing urlpatterns:

from django.urls import path
from . import views
from .views import sitemap_xml, robots_txt


# Your existing urlpatterns should look like this (add the WebP to PNG lines):
urlpatterns = [
    # Main pages
    path('', views.home, name='home'),
    path('contact/', views.contact, name='contact'),
    path('contact/submit/', views.contact_submit, name='contact_submit'),
    path('contact/success/', views.contact_success, name='contact_success'),
    path('faq/', views.faq_page, name='faq'),
    path('about/', views.about, name='about'),

    # Legal pages
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    path('sitemap.xml', sitemap_xml, name='sitemap_xml'),
    path('robots.txt', robots_txt, name='robots_txt'),

    path('admin/analytics/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/real-time/', views.real_time_monitor, name='real_time_monitor'),
    path('admin/api/live-data/', views.live_data_api, name='live_data_api'),
    path('admin/conversion-stats/', views.conversion_statistics, name='conversion_stats'),
    path('admin/system-health/', views.system_health, name='system_health'),
    path('admin/export/activities/', views.export_activities, name='export_activities'),
    path('admin/export/errors/', views.export_errors, name='export_errors'),
    
    # ===== ADMIN API ENDPOINTS =====
    path('admin/analytics/activity/', views.user_activity_detail, name='user_activity_detail'),
    path('admin/analytics/errors/', views.error_log_detail, name='error_log_detail'),
    path('admin/analytics/resolve-error/<uuid:error_id>/', views.resolve_error, name='resolve_error'),
    # Tool pages
    path('tools/', views.all_tools, name='all_tools'),
    path('merge-pdf/', views.merge_pdf, name='merge_pdf'),
    path('compress-pdf/', views.compress_pdf, name='compress_pdf'),
    path('convert-pdf/', views.convert_pdf, name='convert_pdf'),
    path('pdf-to-word/', views.pdf_to_word, name='pdf_to_word'),
    path('pdf-to-jpg/', views.pdf_to_jpg, name='pdf_to_jpg'),
    path('jpg-to-pdf/', views.jpg_to_pdf, name='jpg_to_pdf'),
    path('word-to-pdf/', views.word_to_pdf, name='word_to_pdf'),
    path('compress-pdf/', views.compress_pdf_page, name='compress_pdf'),
    path('compress-image/', views.compress_image_page, name='compress_image'),
    
    # ADD THESE NEW LINES FOR WEBP TO PNG:
    path('webp-to-png/', views.webp_to_png, name='webp_to_png'),
    path('png-to-webp/', views.png_to_webp, name='png_to_webp'),  # NEW
    path('pdf-to-png/', views.pdf_to_png, name='pdf_to_png'),
    path('png-to-pdf/', views.png_to_pdf, name='png_to_pdf'),
    path('split-pdf/', views.split_pdf, name='split_pdf'),


    # API endpoints for PDF processing
    path('api/merge-pdf/', views.merge_pdf_api, name='merge_pdf_api'),
    path('merge-pdf-api/', views.merge_pdf_api, name='merge_pdf_direct'),
    path('api/compress-pdf/', views.compress_pdf_api, name='compress_pdf_api'),
    path('api/convert-pdf/', views.convert_pdf_api, name='convert_pdf_api'),
    path('api/word-to-pdf/', views.word_to_pdf_api, name='word_to_pdf_api'),
    path('api/pdf-to-word/', views.pdf_to_word_api, name='pdf_to_word_api'),
    path('api/pdf-to-jpg/', views.pdf_to_jpg_api, name='pdf_to_jpg_api'),
    path('api/download-images-zip/', views.download_images_zip, name='download_images_zip'),
    path('api/jpg-to-pdf/', views.jpg_to_pdf_api, name='jpg_to_pdf_api'),
    path('api/compress-pdf/', views.compress_pdf_api, name='compress_pdf_api'),
    path('api/compress-image/', views.compress_image_api, name='compress_image_api'),
    path('api/png-to-webp/', views.png_to_webp_api, name='png_to_webp_api'),
    path('api/webp-to-png/', views.webp_to_png_api, name='webp_to_png_api'),
    path('api/pdf-to-png/', views.pdf_to_png_api, name='pdf_to_png_api'),
    path('pdf-to-png-api/', views.pdf_to_png_api, name='pdf_to_png_api_direct'),  # Add this for backward compatibility
    path('api/download-pdf-images-zip/', views.download_pdf_images_zip, name='download_pdf_images_zip'),
    path('download-pdf-images-zip/', views.download_pdf_images_zip, name='download_pdf_images_zip_direct'),
    path('api/png-to-pdf/', views.png_to_pdf_api, name='png_to_pdf_api'),
    path('png-to-pdf-api/', views.png_to_pdf_api, name='png_to_pdf_api_direct'),  # Backward compatibility
    path('api/split-pdf/', views.split_pdf_api, name='split_pdf_api'),
    path('split-pdf-api/', views.split_pdf_api, name='split_pdf_api_direct'),
]