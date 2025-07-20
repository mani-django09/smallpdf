# pdf_tools/sitemaps.py - COMPLETE FIX
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, timedelta


class StaticViewSitemap(Sitemap):
    """Sitemap for static pages"""
    priority = 0.8
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        return [
            'home',
            'all_tools', 
            'about',
            'contact',
            'privacy_policy',
            'terms_of_service',
            'faq'
        ]

    def location(self, item):
        return reverse(item)

    def lastmod(self, item):
        # Return timezone-aware datetime objects
        if item in ['home', 'all_tools']:
            return timezone.now()
        # Return a timezone-aware fixed date for static content
        return timezone.make_aware(datetime(2024, 1, 1))

    def priority_func(self, item):
        # Higher priority for important pages
        priorities = {
            'home': 1.0,
            'all_tools': 0.9,
            'about': 0.6,
            'contact': 0.7,
            'privacy_policy': 0.4,
            'terms_of_service': 0.4,
            'faq': 0.6
        }
        return priorities.get(item, 0.5)


class PDFToolsSitemap(Sitemap):
    """Sitemap for PDF tools pages"""
    priority = 0.9
    changefreq = 'monthly'
    protocol = 'https'

    def items(self):
        return [
            'merge_pdf',
            'compress_pdf', 
            'pdf_to_word',
            'word_to_pdf',
            'pdf_to_jpg',
            'jpg_to_pdf',
            'webp_to_png',
            'png_to_webp',
            'pdf_to_png',
            'png_to_pdf',
            'split_pdf',
            'compress_image',
            'convert_pdf'
        ]

    def location(self, item):
        return reverse(item)

    def lastmod(self, item):
        # Return timezone-aware datetime (7 days ago)
        return timezone.now() - timedelta(days=7)

    def priority_func(self, item):
        # Higher priority for popular tools
        high_priority_tools = ['merge_pdf', 'compress_pdf', 'pdf_to_word', 'word_to_pdf']
        return 0.9 if item in high_priority_tools else 0.8