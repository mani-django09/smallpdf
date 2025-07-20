# smallpdf/urls.py - COMPLETE FIX
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from pdf_tools.sitemaps import StaticViewSitemap, PDFToolsSitemap

# Sitemap configuration
sitemaps = {
    'static': StaticViewSitemap,
    'tools': PDFToolsSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('pdf_tools.urls')),
    
    # Sitemap URLs
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, 
         name='django.contrib.sitemaps.views.sitemap'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)