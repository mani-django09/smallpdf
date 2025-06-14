# context_processors.py - Create this file in your main app directory

def seo_context(request):
    """
    Add SEO-related context variables to all templates
    """
    return {
        'site_name': 'SmallPDF.us',
        'site_domain': 'smallpdf.us',
        'site_description': 'Free online PDF tools to convert, compress, merge, and edit PDF files.',
        'default_keywords': 'PDF converter, PDF to Word, Word to PDF, compress PDF, merge PDF, online PDF tools',
        'social_media': {
            'twitter': '@SmallPDFus',
            'facebook': 'https://facebook.com/SmallPDFus',
            'linkedin': 'https://linkedin.com/company/smallpdfus',
        },
        'company_info': {
            'name': 'SmallPDF.us',
            'founded': '2020',
            'email': 'support@smallpdf.us',
            'phone': '+1 (555) SMALL-PDF',
        }
    }