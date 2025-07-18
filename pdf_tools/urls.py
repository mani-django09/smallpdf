# Add these to your existing urlpatterns in urls.py

from django.urls import path
from . import views   

# Your complete urlpatterns might look like this:
urlpatterns = [
    # Main pages
    path('', views.home, name='home'),
    path('contact/', views.contact, name='contact'),
    path('contact/submit/', views.contact_submit, name='contact_submit'),
    path('contact/success/', views.contact_success, name='contact_success'),
    path('faq/', views.faq_page, name='faq'),  # 👈 This 'name' must match
    path('about/', views.about, name='about'),

    # Legal pages
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    path('robots.txt', views.robots_txt, name='robots_txt'),

    path('admin/analytics/', views.admin_dashboard, name='admin_dashboard'),

    path('admin/analytics/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/analytics/activity/', views.user_activity_detail, name='user_activity_detail'),
    path('admin/analytics/errors/', views.error_log_detail, name='error_log_detail'),
    path('admin/analytics/api/data/', views.api_dashboard_data, name='api_dashboard_data'),
    path('admin/analytics/resolve-error/<uuid:error_id>/', views.resolve_error, name='resolve_error'),
    # Tool pages
    path('tools/', views.all_tools, name='all_tools'),
    path('merge-pdf/', views.merge_pdf, name='merge_pdf'),
    path('compress-pdf/', views.compress_pdf, name='compress_pdf'),
    path('convert-pdf/', views.convert_pdf, name='convert_pdf'),
    path('pdf-to-word/', views.pdf_to_word, name='pdf_to_word'),
    path('pdf-to-jpg/', views.pdf_to_jpg, name='pdf_to_jpg'),
    path('jpg-to-pdf/', views.jpg_to_pdf, name='jpg_to_pdf'),
    path('word-to-pdf/', views.word_to_pdf, name='word_to_pdf'),  # New Word to PDF route
    path('compress-pdf/', views.compress_pdf_page, name='compress_pdf'),
    path('compress-image/', views.compress_image_page, name='compress_image'),
    path('word-to-pdf/', views.word_to_pdf, name='word_to_pdf'),
    path('api/word-to-pdf/', views.word_to_pdf_api, name='word_to_pdf_api'),
    # API endpoints for PDF processing
    path('api/merge-pdf/', views.merge_pdf_api, name='merge_pdf_api'),
    path('merge-pdf-api/', views.merge_pdf_api, name='merge_pdf_direct'),
    path('api/compress-pdf/', views.compress_pdf_api, name='compress_pdf_api'),
    path('api/convert-pdf/', views.convert_pdf_api, name='convert_pdf_api'),
    path('api/word-to-pdf/', views.word_to_pdf_api, name='word_to_pdf_api'),  # New Word to PDF API endpoint
    path('api/pdf-to-word/', views.pdf_to_word_api, name='pdf_to_word_api'),
    path('api/pdf-to-jpg/', views.pdf_to_jpg_api, name='pdf_to_jpg_api'),
    path('api/download-images-zip/', views.download_images_zip, name='download_images_zip'),
    path('api/jpg-to-pdf/', views.jpg_to_pdf_api, name='jpg_to_pdf_api'),
    path('api/compress-pdf/', views.compress_pdf_api, name='compress_pdf_api'),
    path('api/compress-image/', views.compress_image_api, name='compress_image_api'),
    
]