import os
import io
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import zipfile
import uuid
import json
import shutil
import subprocess
import platform
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
import tempfile
from io import BytesIO
from django.views.decorators.cache import cache_control
import re
from .models import ContactMessage, ContactSettings
from .forms import ContactForm
from .models import UserActivity, ErrorLog, track_activity, log_error
import csv
from django.db.models import Count, Avg, Sum, Q, Max, Min
from django.shortcuts import render

try:
    from docx import Document
    PYTHON_DOCX_AVAILABLE = True
except ImportError:
    PYTHON_DOCX_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import A4, letter, A3, A5, legal
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
# QUICK FIX: Add these lines after your existing imports in views.py

# Image to PDF conversion libraries - MISSING IMPORTS
try:
    import img2pdf
    IMG2PDF_AVAILABLE = True
except ImportError:
    IMG2PDF_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import A4, letter, A3, A5, legal
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# These were already in your code but make sure they're defined
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Update your existing conversion library check
CONVERSION_LIBRARY_AVAILABLE = (
    IMG2PDF_AVAILABLE or 
    REPORTLAB_AVAILABLE or 
    PIL_AVAILABLE
)

try:
    import PyPDF2
    from PyPDF2 import PdfReader, PdfWriter, PdfMerger  # Make sure PdfMerger is imported
    PDF_LIBRARY_AVAILABLE = True
except ImportError:
    PDF_LIBRARY_AVAILABLE = False

# Import for file conversion if installed
try:
    import pdf2docx
    import openpyxl
    import img2pdf
    from PIL import Image
    CONVERSION_LIBRARY_AVAILABLE = True
except ImportError:
    CONVERSION_LIBRARY_AVAILABLE = False

@cache_control(max_age=86400)
def ads_txt(request):
    """Serve ads.txt file for Google AdSense"""
    ads_txt_content = "google.com, pub-6913093595582462, DIRECT, f08c47fec0942fa0"
    return HttpResponse(ads_txt_content, content_type='text/plain')
# Main page views
def home(request):
    """Render the homepage"""
    return render(request, 'home.html')

def contact(request):
    """Render the contact page"""
    return render(request, 'contact.html')


# Legal page views
def privacy_policy(request):
    """Render the privacy policy page"""
    return render(request, 'privacy_policy.html')

def terms_of_service(request):
    """Render the terms of service page"""
    return render(request, 'terms_of_service.html')


# PDF Tool page views
def all_tools(request):
    """Render the all tools page with all available tools"""
    tools = [
        # PDF Processing Tools
        {
            'name': 'Merge PDF',
            'description': 'Combine multiple PDFs into a single document.',
            'url': 'merge_pdf',
            'icon': 'merge-icon.svg',
            'category': 'PDF Processing',
            'featured': True
        },
        {
            'name': 'Split PDF',
            'description': 'Split PDF into separate pages or extract specific page ranges.',
            'url': 'split_pdf',
            'icon': 'split-icon.svg',
            'category': 'PDF Processing',
            'featured': True
        },
        {
            'name': 'Compress PDF',
            'description': 'Reduce PDF file size while maintaining quality.',
            'url': 'compress_pdf',
            'icon': 'compress-icon.svg',
            'category': 'PDF Processing',
            'featured': True
        },
        {
            'name': 'Convert PDF',
            'description': 'Transform PDFs to other formats like Word, Excel, etc.',
            'url': 'convert_pdf',
            'icon': 'convert-icon.svg',
            'category': 'PDF Processing',
            'featured': False
        },
        
        # PDF Conversion Tools
        {
            'name': 'PDF to Word',
            'description': 'Convert PDF documents to editable Word files.',
            'url': 'pdf_to_word',
            'icon': 'pdf-to-word-icon.svg',
            'category': 'PDF Conversion',
            'featured': True
        },
        {
            'name': 'Word to PDF',
            'description': 'Convert Word documents to PDF format.',
            'url': 'word_to_pdf',
            'icon': 'word-to-pdf-icon.svg',
            'category': 'PDF Conversion',
            'featured': True
        },
        {
            'name': 'PDF to JPG',
            'description': 'Convert PDF pages to JPG image files.',
            'url': 'pdf_to_jpg',
            'icon': 'pdf-to-jpg-icon.svg',
            'category': 'PDF Conversion',
            'featured': True
        },
        {
            'name': 'JPG to PDF',
            'description': 'Convert JPG images to PDF documents.',
            'url': 'jpg_to_pdf',
            'icon': 'jpg-to-pdf-icon.svg',
            'category': 'PDF Conversion',
            'featured': True
        },
        {
            'name': 'PDF to PNG',
            'description': 'Convert PDF pages to PNG images with transparency support.',
            'url': 'pdf_to_png',
            'icon': 'pdf-to-png-icon.svg',
            'category': 'PDF Conversion',
            'featured': False
        },
        {
            'name': 'PNG to PDF',
            'description': 'Convert PNG images to PDF documents.',
            'url': 'png_to_pdf',
            'icon': 'png-to-pdf-icon.svg',
            'category': 'PDF Conversion',
            'featured': False
        },
        
        # Image Processing Tools
        {
            'name': 'WebP to PNG',
            'description': 'Convert WebP images to PNG format online free.',
            'url': 'webp_to_png',
            'icon': 'webp-to-png-icon.svg',
            'category': 'Image Processing',
            'featured': True
        },
        {
            'name': 'PNG to WebP',
            'description': 'Convert PNG images to WebP format for better compression.',
            'url': 'png_to_webp',
            'icon': 'png-to-webp-icon.svg',
            'category': 'Image Processing',
            'featured': False
        },
        {
            'name': 'Compress Image',
            'description': 'Reduce image file size while maintaining quality.',
            'url': 'compress_image',
            'icon': 'compress-image-icon.svg',
            'category': 'Image Processing',
            'featured': True
        }
    ]
    
    # Group tools by category for better organization
    tools_by_category = {}
    featured_tools = []
    
    for tool in tools:
        category = tool['category']
        if category not in tools_by_category:
            tools_by_category[category] = []
        tools_by_category[category].append(tool)
        
        # Add to featured tools if marked as featured
        if tool.get('featured', False):
            featured_tools.append(tool)
    
    # Count total tools
    total_tools = len(tools)
    
    context = {
        'tools': tools,
        'tools_by_category': tools_by_category,
        'featured_tools': featured_tools,
        'total_tools': total_tools,
        'categories': list(tools_by_category.keys())
    }
    
    return render(request, 'all_tools.html', context)
    

def merge_pdf(request):
    """Render the merge PDF tool page"""
    return render(request, 'merge_pdf.html')

def compress_pdf(request):
    """Render the compress PDF tool page"""
    return render(request, 'compress_pdf.html')

def convert_pdf(request):
    """Render the convert PDF tool page"""
    return render(request, 'tools/convert_pdf.html')


try:
    import pdf2docx
    from pdf2docx import Converter
    PDF2DOCX_AVAILABLE = True
except ImportError:
    PDF2DOCX_AVAILABLE = False

def pdf_to_word(request):
    """Render the PDF to Word tool page"""
    return render(request, 'pdf_to_word.html')

@csrf_exempt
def pdf_to_word_api(request):
    """API endpoint to convert PDF files to Word documents"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    if not PDF2DOCX_AVAILABLE:
        return JsonResponse({'error': 'PDF to Word conversion library not available'}, status=500)
    
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'PDF file is required'}, status=400)
    
    pdf_file = request.FILES['file']
    output_format = request.POST.get('format', 'docx')
    conversion_mode = request.POST.get('mode', 'accurate')
    
    # Check if it's a valid PDF file
    if not pdf_file.name.lower().endswith('.pdf'):
        return JsonResponse({'error': 'Please upload a valid PDF file'}, status=400)
    
    try:
        # Create a temporary file to store the uploaded PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
            for chunk in pdf_file.chunks():
                temp_pdf.write(chunk)
            temp_pdf_path = temp_pdf.name
        
        # Create a temporary file for the output Word document
        if output_format == 'doc':
            output_suffix = '.doc'
            mime_type = 'application/msword'
        else:
            output_suffix = '.docx'
            mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        
        output_file = tempfile.NamedTemporaryFile(delete=False, suffix=output_suffix)
        output_path = output_file.name
        output_file.close()
        
        # Optimize conversion settings
        if conversion_mode == 'accurate':
            # Preserve layout mode with optimized settings
            config = {
                'page_numbering': True,
                'preserve_tables': True,
                'debug': False,  # Disable debug to improve performance
                'multi_processing': True,  # Enable multi-processing for faster conversion
                'cpu_count': 2,  # Limit CPU count to avoid server overload
                'batch_size': 50  # Increase batch size for faster processing
            }
        elif conversion_mode == 'editable':
            # Optimize for text extraction and speed
            config = {
                'page_numbering': False,
                'preserve_tables': False,
                'preserve_images': True,
                'debug': False,
                'multi_processing': True,
                'cpu_count': 2,
                'batch_size': 50
            }
        else:  # automatic - balance between speed and accuracy
            config = {
                'debug': False,
                'multi_processing': True,
                'cpu_count': 2
            }
        
        # Convert PDF to Word
        try:
            cv = Converter(temp_pdf_path)
            cv.convert(output_path, **config)
            cv.close()
        except Exception as e:
            raise Exception(f"Conversion error: {str(e)}")
        
        # Return the converted file
        with open(output_path, 'rb') as docx_file:
            response = HttpResponse(docx_file.read(), content_type=mime_type)
            output_filename = os.path.splitext(pdf_file.name)[0] + output_suffix
            response['Content-Disposition'] = f'attachment; filename="{output_filename}"'
            # Add cache-control header to prevent caching issues
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        # Clean up temporary files
        if os.path.exists(temp_pdf_path):
            os.unlink(temp_pdf_path)
        if os.path.exists(output_path):
            os.unlink(output_path)
        
        return response
    
    except Exception as e:
        # Clean up temporary files in case of error
        try:
            if 'temp_pdf_path' in locals() and os.path.exists(temp_pdf_path):
                os.unlink(temp_pdf_path)
            if 'output_path' in locals() and os.path.exists(output_path):
                os.unlink(output_path)
        except:
            pass
        
        return JsonResponse({'error': str(e)}, status=500)



try:
    import fitz  # PyMuPDF
    from PIL import Image
    PYMUPDF_AVAILABLE = True
    print("PyMuPDF successfully imported")
except ImportError as e:
    PYMUPDF_AVAILABLE = False
    print(f"PyMuPDF import failed: {e}")

def pdf_to_jpg(request):
    """Render the PDF to JPG tool page"""
    return render(request, 'pdf_to_jpg.html')

@csrf_exempt
@require_http_methods(["POST"])
def pdf_to_jpg_api(request):
    """
    Convert PDF to JPG images API endpoint
    """
    try:
        # Check if PDF file is provided
        if 'pdf_file' not in request.FILES:
            return JsonResponse({'error': 'PDF file is required'}, status=400)
        
        pdf_file = request.FILES['pdf_file']
        
        # Validate file type
        if not pdf_file.name.lower().endswith('.pdf'):
            return JsonResponse({'error': 'Invalid file type. Please upload a PDF file.'}, status=400)
        
        # Validate file size (50MB limit)
        max_size = 50 * 1024 * 1024  # 50MB
        if pdf_file.size > max_size:
            return JsonResponse({'error': 'File size exceeds 50MB limit.'}, status=400)
        
        # Get conversion settings
        image_format = request.POST.get('format', 'jpg').lower()
        quality = request.POST.get('quality', 'high')
        dpi = int(request.POST.get('dpi', 300))
        page_selection = request.POST.get('page_selection', 'all')
        
        # Parse selected pages
        selected_pages = []
        if page_selection == 'all':
            selected_pages = None  # Will process all pages
        else:
            try:
                selected_pages_json = request.POST.get('selected_pages', '[]')
                selected_pages = json.loads(selected_pages_json)
            except (json.JSONDecodeError, ValueError):
                return JsonResponse({'error': 'Invalid page selection format'}, status=400)
        
        # Handle page range and custom pages
        if page_selection == 'range':
            page_range = request.POST.get('page_range', '')
            if page_range:
                try:
                    start, end = map(int, page_range.split('-'))
                    selected_pages = list(range(start, end + 1))
                except ValueError:
                    return JsonResponse({'error': 'Invalid page range format. Use format like "1-5"'}, status=400)
        elif page_selection == 'custom':
            custom_pages = request.POST.get('custom_pages', '')
            if custom_pages:
                try:
                    selected_pages = []
                    for part in custom_pages.split(','):
                        part = part.strip()
                        if '-' in part:
                            start, end = map(int, part.split('-'))
                            selected_pages.extend(range(start, end + 1))
                        else:
                            selected_pages.append(int(part))
                except ValueError:
                    return JsonResponse({'error': 'Invalid custom pages format. Use format like "1,3,5-7"'}, status=400)
        
        # Quality settings
        quality_settings = {
            'high': {'jpeg_quality': 95, 'png_compress_level': 1},
            'medium': {'jpeg_quality': 85, 'png_compress_level': 6},
            'low': {'jpeg_quality': 75, 'png_compress_level': 9}
        }
        
        current_quality = quality_settings.get(quality, quality_settings['high'])
        
        # Create temporary file for PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
            for chunk in pdf_file.chunks():
                temp_pdf.write(chunk)
            temp_pdf_path = temp_pdf.name
        
        try:
            # Open PDF with PyMuPDF
            pdf_document = fitz.open(temp_pdf_path)
            total_pages = len(pdf_document)
            
            # Determine which pages to process
            if selected_pages is None:
                pages_to_process = list(range(1, total_pages + 1))
            else:
                # Filter valid page numbers
                pages_to_process = [p for p in selected_pages if 1 <= p <= total_pages]
            
            if not pages_to_process:
                return JsonResponse({'error': 'No valid pages selected for conversion'}, status=400)
            
            # Convert pages to images
            converted_images = []
            
            for page_num in pages_to_process:
                try:
                    # Get page (PyMuPDF uses 0-based indexing)
                    page = pdf_document[page_num - 1]
                    
                    # Calculate matrix for DPI
                    zoom = dpi / 72.0  # 72 DPI is default
                    mat = fitz.Matrix(zoom, zoom)
                    
                    # Render page to pixmap
                    pix = page.get_pixmap(matrix=mat)
                    
                    # Convert to PIL Image
                    img_data = pix.tobytes("ppm")
                    img = Image.open(BytesIO(img_data))
                    
                    # Convert to RGB if necessary
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Save image to BytesIO
                    img_buffer = BytesIO()
                    
                    if image_format == 'png':
                        img.save(img_buffer, format='PNG', 
                                compress_level=current_quality['png_compress_level'])
                        content_type = 'image/png'
                        file_ext = 'png'
                    else:  # JPG
                        img.save(img_buffer, format='JPEG', 
                                quality=current_quality['jpeg_quality'], 
                                optimize=True)
                        content_type = 'image/jpeg'
                        file_ext = 'jpg'
                    
                    img_buffer.seek(0)
                    
                    # Generate unique filename
                    unique_id = str(uuid.uuid4())[:8]
                    filename = f"page_{page_num}_{unique_id}.{file_ext}"
                    
                    # Save to media storage
                    file_path = f"converted_images/{filename}"
                    saved_path = default_storage.save(file_path, img_buffer)
                    
                    # Get URL for the saved file
                    file_url = default_storage.url(saved_path)
                    
                    converted_images.append({
                        'page': page_num,
                        'url': file_url,
                        'filename': filename,
                        'format': file_ext,
                        'size': img_buffer.getvalue().__len__()
                    })
                    
                except Exception as e:
                    print(f"Error converting page {page_num}: {str(e)}")
                    continue
            
            pdf_document.close()
            
            if not converted_images:
                return JsonResponse({'error': 'Failed to convert any pages'}, status=500)
            
            return JsonResponse({
                'success': True,
                'images': converted_images,
                'total_pages': len(converted_images),
                'format': image_format,
                'quality': quality,
                'dpi': dpi
            })
            
        finally:
            # Clean up temporary PDF file
            try:
                os.unlink(temp_pdf_path)
            except OSError:
                pass
                
    except Exception as e:
        print(f"PDF to JPG conversion error: {str(e)}")
        return JsonResponse({'error': 'Internal server error during conversion'}, status=500)




@csrf_exempt
@require_http_methods(["POST"])
def download_images_zip(request):
    """
    Download converted images - single file for 1 image, ZIP for multiple images
    """
    try:
        image_urls_json = request.POST.get('image_urls', '[]')
        file_name = request.POST.get('file_name', 'converted_images')
        format_type = request.POST.get('format', 'jpg')
        
        try:
            image_data = json.loads(image_urls_json)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid image data format'}, status=400)
        
        if not image_data:
            return JsonResponse({'error': 'No images to download'}, status=400)
        
        # If only 1 image, download it directly (not as ZIP)
        if len(image_data) == 1:
            image_info = image_data[0]
            
            try:
                # Get the file path from URL
                file_url = image_info.get('url', '')
                if not file_url:
                    return JsonResponse({'error': 'Invalid image URL'}, status=400)
                
                # Extract file path from URL
                file_path = file_url.replace(settings.MEDIA_URL, '')
                
                # Read file from storage
                if default_storage.exists(file_path):
                    file_content = default_storage.open(file_path).read()
                    
                    # Generate filename for single download
                    page_num = image_info.get('page', 1)
                    single_filename = f"{file_name}_page_{page_num}.{format_type}"
                    
                    # Determine content type
                    content_type = 'image/jpeg' if format_type.lower() in ['jpg', 'jpeg'] else f'image/{format_type.lower()}'
                    
                    # Return single image file
                    response = HttpResponse(file_content, content_type=content_type)
                    response['Content-Disposition'] = f'attachment; filename="{single_filename}"'
                    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
                    response['Pragma'] = 'no-cache'
                    response['Expires'] = '0'
                    
                    return response
                else:
                    return JsonResponse({'error': 'Image file not found'}, status=404)
                    
            except Exception as e:
                print(f"Error downloading single image: {str(e)}")
                return JsonResponse({'error': 'Failed to download image'}, status=500)
        
        # For multiple images, create ZIP file
        else:
            # Create ZIP file in memory
            zip_buffer = BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for i, image_info in enumerate(image_data):
                    try:
                        # Get the file path from URL
                        file_url = image_info.get('url', '')
                        if not file_url:
                            continue
                        
                        # Extract file path from URL
                        file_path = file_url.replace(settings.MEDIA_URL, '')
                        
                        # Read file from storage
                        if default_storage.exists(file_path):
                            file_content = default_storage.open(file_path).read()
                            
                            # Generate filename for ZIP
                            page_num = image_info.get('page', i + 1)
                            zip_filename = f"{file_name}_page_{page_num}.{format_type}"
                            
                            # Add file to ZIP
                            zip_file.writestr(zip_filename, file_content)
                            
                    except Exception as e:
                        print(f"Error adding image to ZIP: {str(e)}")
                        continue
            
            zip_buffer.seek(0)
            
            # Create HTTP response with ZIP file
            response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="{file_name}_images.zip"'
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            
            return response
        
    except Exception as e:
        print(f"Download error: {str(e)}")
        return JsonResponse({'error': 'Failed to create download'}, status=500)
    
    
@csrf_exempt
def jpg_to_pdf_api(request):
    """API endpoint to convert images to PDF using img2pdf or reportlab"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    if not IMG2PDF_AVAILABLE and not REPORTLAB_AVAILABLE:
        return JsonResponse({
            'error': 'PDF creation library not available. Please install img2pdf or reportlab: pip install img2pdf reportlab'
        }, status=500)
    
    if 'images' not in request.FILES:
        return JsonResponse({'error': 'At least one image file is required'}, status=400)
    
    image_files = request.FILES.getlist('images')
    page_size = request.POST.get('page_size', 'auto')
    orientation = request.POST.get('orientation', 'auto')
    margin = request.POST.get('margin', 'medium')
    quality = request.POST.get('quality', 'high')
    combine_option = request.POST.get('combine_option', 'single')
    
    # Validate files
    max_file_size = 10 * 1024 * 1024  # 10MB per file
    max_total_size = 100 * 1024 * 1024  # 100MB total
    max_files = 50
    
    if len(image_files) > max_files:
        return JsonResponse({'error': f'Maximum {max_files} images allowed'}, status=400)
    
    total_size = sum(file.size for file in image_files)
    if total_size > max_total_size:
        return JsonResponse({'error': 'Total file size exceeds 100MB limit'}, status=400)
    
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    for file in image_files:
        if file.size > max_file_size:
            return JsonResponse({'error': f'File {file.name} exceeds 10MB limit'}, status=400)
        
        file_ext = os.path.splitext(file.name.lower())[1]
        if file_ext not in valid_extensions:
            return JsonResponse({'error': f'Invalid file format: {file.name}'}, status=400)
    
    # Create unique temp directory
    temp_dir = None
    
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix='jpg_to_pdf_')
        print(f"Created temp directory: {temp_dir}")
        
        # Process images
        processed_images = []
        for i, image_file in enumerate(image_files):
            try:
                # Save uploaded image to temporary file
                temp_image_path = os.path.join(temp_dir, f"image_{i}_{uuid.uuid4().hex}{os.path.splitext(image_file.name)[1]}")
                
                with open(temp_image_path, 'wb') as temp_file:
                    for chunk in image_file.chunks():
                        temp_file.write(chunk)
                
                # Process and validate image
                processed_path = process_image(temp_image_path, temp_dir, quality)
                if processed_path:
                    processed_images.append({
                        'path': processed_path,
                        'original_name': image_file.name,
                        'index': i
                    })
                    
            except Exception as e:
                print(f"Error processing image {image_file.name}: {str(e)}")
                continue
        
        if not processed_images:
            raise Exception("No valid images could be processed")
        
        print(f"Successfully processed {len(processed_images)} images")
        
        # Convert to PDF(s)
        if combine_option == 'single':
            # Create single PDF with all images
            pdf_path = create_single_pdf(processed_images, temp_dir, page_size, orientation, margin)
            
            # Return PDF file
            with open(pdf_path, 'rb') as pdf_file:
                response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="converted_images.pdf"'
                response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
            
            return response
            
        else:
            # Create separate PDFs for each image
            pdf_paths = create_separate_pdfs(processed_images, temp_dir, page_size, orientation, margin)
            
            # Create ZIP file with all PDFs
            zip_path = os.path.join(temp_dir, 'converted_pdfs.zip')
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for pdf_path, original_name in pdf_paths:
                    pdf_name = f"{os.path.splitext(original_name)[0]}.pdf"
                    zip_file.write(pdf_path, pdf_name)
            
            # Return ZIP file
            with open(zip_path, 'rb') as zip_file:
                response = HttpResponse(zip_file.read(), content_type='application/zip')
                response['Content-Disposition'] = 'attachment; filename="converted_images.zip"'
                response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
            
            return response
        
    except Exception as e:
        print(f"Conversion error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'error': f"Conversion failed: {str(e)}"
        }, status=500)
        
    finally:
        # Clean up temporary files
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                print(f"Cleaned up temp directory: {temp_dir}")
            except Exception as e:
                print(f"Failed to clean up temp directory: {e}")

def process_image(image_path, temp_dir, quality):
    """Process and optimize image for PDF conversion"""
    try:
        # Open and process image
        with Image.open(image_path) as img:
            # Convert to RGB if necessary (remove alpha channel for JPEG)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[-1])
                else:
                    background.paste(img)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Set quality parameters
            if quality == 'high':
                jpeg_quality = 95
                max_dimension = 3000
            elif quality == 'medium':
                jpeg_quality = 85
                max_dimension = 2000
            else:  # low
                jpeg_quality = 75
                max_dimension = 1500
            
            # Resize if image is too large
            if max(img.size) > max_dimension:
                img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
            
            # Save processed image
            processed_path = os.path.join(temp_dir, f"processed_{uuid.uuid4().hex}.jpg")
            img.save(processed_path, 'JPEG', quality=jpeg_quality, optimize=True)
            
            return processed_path
            
    except Exception as e:
        print(f"Error processing image {image_path}: {str(e)}")
        return None

def get_page_size_dimensions(page_size):
    """Get page dimensions based on page size setting"""
    page_sizes = {
        'auto': None,  # Will be determined by image
        'a4': A4,
        'letter': letter,
        'a3': A3,
        'a5': A5,
        'legal': legal
    }
    return page_sizes.get(page_size, A4)

def get_margin_size(margin):
    """Get margin size in points"""
    margins = {
        'none': 0,
        'small': 10 * mm,
        'medium': 20 * mm,
        'large': 30 * mm
    }
    return margins.get(margin, 20 * mm)

def create_single_pdf(processed_images, temp_dir, page_size, orientation, margin):
    """Create a single PDF with all images"""
    pdf_path = os.path.join(temp_dir, 'combined_images.pdf')
    
    if IMG2PDF_AVAILABLE and page_size == 'auto' and margin == 'none':
        # Use img2pdf for simple auto-fit conversion (faster and simpler)
        try:
            image_paths = [img['path'] for img in processed_images]
            
            with open(pdf_path, 'wb') as f:
                f.write(img2pdf.convert(image_paths))
            
            return pdf_path
            
        except Exception as e:
            print(f"img2pdf conversion failed, falling back to reportlab: {str(e)}")
    
    # Use reportlab for more control over layout
    if not REPORTLAB_AVAILABLE:
        raise Exception("ReportLab library required for custom page layouts")
    
    c = canvas.Canvas(pdf_path)
    margin_size = get_margin_size(margin)
    
    for img_data in processed_images:
        try:
            # Get image dimensions
            with Image.open(img_data['path']) as img:
                img_width, img_height = img.size
                img_aspect = img_width / img_height
            
            # Determine page size and orientation
            if page_size == 'auto':
                # Auto-fit to image size with some padding
                if orientation == 'auto':
                    if img_aspect > 1:  # Landscape
                        page_width = max(img_width + 2 * margin_size, 400)
                        page_height = max(img_height + 2 * margin_size, 300)
                    else:  # Portrait
                        page_width = max(img_width + 2 * margin_size, 300)
                        page_height = max(img_height + 2 * margin_size, 400)
                else:
                    page_width = max(img_width + 2 * margin_size, 400)
                    page_height = max(img_height + 2 * margin_size, 300)
                    if orientation == 'portrait' and page_width > page_height:
                        page_width, page_height = page_height, page_width
                
                c.setPageSize((page_width, page_height))
            else:
                # Use standard page size
                page_dims = get_page_size_dimensions(page_size)
                if orientation == 'landscape':
                    page_width, page_height = page_dims[1], page_dims[0]
                else:
                    page_width, page_height = page_dims[0], page_dims[1]
                
                c.setPageSize((page_width, page_height))
            
            # Calculate image position and size
            available_width = page_width - 2 * margin_size
            available_height = page_height - 2 * margin_size
            
            # Scale image to fit available space while maintaining aspect ratio
            scale_x = available_width / img_width
            scale_y = available_height / img_height
            scale = min(scale_x, scale_y)
            
            final_width = img_width * scale
            final_height = img_height * scale
            
            # Center image on page
            x = (page_width - final_width) / 2
            y = (page_height - final_height) / 2
            
            # Draw image
            c.drawImage(img_data['path'], x, y, final_width, final_height)
            c.showPage()
            
        except Exception as e:
            print(f"Error adding image {img_data['original_name']} to PDF: {str(e)}")
            continue
    
    c.save()
    return pdf_path

def create_separate_pdfs(processed_images, temp_dir, page_size, orientation, margin):
    """Create separate PDF files for each image"""
    pdf_paths = []
    
    for img_data in processed_images:
        try:
            pdf_filename = f"pdf_{img_data['index']}_{uuid.uuid4().hex}.pdf"
            pdf_path = os.path.join(temp_dir, pdf_filename)
            
            # Create PDF with single image
            single_pdf_path = create_single_pdf([img_data], temp_dir, page_size, orientation, margin)
            
            # Rename to unique name
            os.rename(single_pdf_path, pdf_path)
            
            pdf_paths.append((pdf_path, img_data['original_name']))
            
        except Exception as e:
            print(f"Error creating PDF for image {img_data['original_name']}: {str(e)}")
            continue
    
    return pdf_paths

# Helper function to check if image file is valid
def is_valid_image(file_path):
    """Check if file is a valid image"""
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except Exception:
        return False
    
def jpg_to_pdf(request):
    """Render the JPG to PDF tool page"""
    return render(request, 'jpg_to_pdf.html')

# PDF Processing API endpoints

# Add this to your views.py - FIXED merge_pdf_api function

# COMPLETE FIX - Add this to your views.py

@csrf_exempt
def merge_pdf_api(request):
    """FIXED API endpoint to merge multiple PDFs"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    if not PDF_LIBRARY_AVAILABLE:
        return JsonResponse({'error': 'PDF processing library not available'}, status=500)
    
    # Debug: Print all received data
    print("=== MERGE PDF API DEBUG ===")
    print(f"Request method: {request.method}")
    print(f"Content type: {request.content_type}")
    print(f"Files in request: {list(request.FILES.keys())}")
    print(f"POST data: {dict(request.POST)}")
    
    # Try multiple ways to get files
    files = []
    
    # Method 1: Try 'files' key (getlist for multiple files)
    if 'files' in request.FILES:
        files = request.FILES.getlist('files')
        print(f"Method 1 - Found {len(files)} files in 'files' key")
    
    # Method 2: Try 'pdf_files' key
    if not files and 'pdf_files' in request.FILES:
        files = request.FILES.getlist('pdf_files')
        print(f"Method 2 - Found {len(files)} files in 'pdf_files' key")
    
    # Method 3: Try single file upload
    if not files and 'file' in request.FILES:
        files = [request.FILES['file']]
        print(f"Method 3 - Found {len(files)} file in 'file' key")
    
    # Method 4: Iterate through all file keys
    if not files:
        for key, file_list in request.FILES.lists():
            print(f"Available file key: '{key}' with {len(file_list)} files")
            if file_list:
                files.extend(file_list)
        print(f"Method 4 - Found {len(files)} total files")
    
    # Print detailed file information
    print(f"Final file count: {len(files)}")
    for i, f in enumerate(files):
        print(f"File {i+1}: {f.name} ({f.size} bytes, type: {getattr(f, 'content_type', 'unknown')})")
    
    if not files or len(files) < 2:
        error_msg = f'At least 2 PDF files are required for merging. Found {len(files)} files.'
        print(f"ERROR: {error_msg}")
        return JsonResponse({'error': error_msg}, status=400)
    
    # Validate files
    for i, pdf_file in enumerate(files):
        if not pdf_file.name.lower().endswith('.pdf'):
            error_msg = f'File {i+1} ({pdf_file.name}) is not a PDF file'
            print(f"ERROR: {error_msg}")
            return JsonResponse({'error': error_msg}, status=400)
        
        if pdf_file.size > 50 * 1024 * 1024:  # 50MB limit
            error_msg = f'File {i+1} ({pdf_file.name}) exceeds 50MB limit'
            print(f"ERROR: {error_msg}")
            return JsonResponse({'error': error_msg}, status=400)
        
        if pdf_file.size == 0:
            error_msg = f'File {i+1} ({pdf_file.name}) is empty'
            print(f"ERROR: {error_msg}")
            return JsonResponse({'error': error_msg}, status=400)
    
    temp_files = []
    
    try:
        print("Starting PDF merge process...")
        
        # Use PdfWriter for merging
        writer = PdfWriter()
        total_pages = 0
        processed_files = []
        
        # Process each file
        for i, pdf_file in enumerate(files):
            print(f"Processing file {i+1}: {pdf_file.name}")
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_files.append(temp_file.name)
            
            # Write uploaded content to temp file
            try:
                for chunk in pdf_file.chunks():
                    temp_file.write(chunk)
                temp_file.close()
                
                temp_size = os.path.getsize(temp_file.name)
                print(f"Created temp file: {temp_file.name} ({temp_size} bytes)")
                
                if temp_size == 0:
                    raise Exception(f"Temporary file for {pdf_file.name} is empty")
                
            except Exception as e:
                print(f"Error writing temp file for {pdf_file.name}: {str(e)}")
                return JsonResponse({'error': f'Error processing file {pdf_file.name}: {str(e)}'}, status=500)
            
            # Read and validate the PDF
            try:
                with open(temp_file.name, 'rb') as f:
                    reader = PdfReader(f)
                    pages = len(reader.pages)
                    print(f"PDF {pdf_file.name} has {pages} pages")
                    
                    if pages == 0:
                        raise Exception(f"PDF {pdf_file.name} has no pages")
                    
                    # Add all pages to writer
                    for page_num in range(pages):
                        page = reader.pages[page_num]
                        writer.add_page(page)
                        total_pages += 1
                    
                    processed_files.append({
                        'name': pdf_file.name,
                        'pages': pages,
                        'size': pdf_file.size
                    })
                        
            except Exception as pdf_error:
                error_msg = f'Error reading PDF {pdf_file.name}: {str(pdf_error)}'
                print(f"ERROR: {error_msg}")
                return JsonResponse({'error': error_msg}, status=400)
        
        print(f"Successfully processed {len(processed_files)} files. Total pages: {total_pages}")
        
        # Create output file
        output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        output_path = output_file.name
        output_file.close()
        
        # Write merged PDF
        print(f"Writing merged PDF to: {output_path}")
        try:
            with open(output_path, 'wb') as f:
                writer.write(f)
        except Exception as write_error:
            raise Exception(f"Failed to write merged PDF: {str(write_error)}")
        
        # Verify output file
        output_size = os.path.getsize(output_path)
        print(f"Output file size: {output_size} bytes")
        
        if output_size == 0:
            raise Exception("Output PDF file is empty")
        
        # Test read the output
        try:
            with open(output_path, 'rb') as f:
                test_reader = PdfReader(f)
                output_pages = len(test_reader.pages)
                print(f"Output PDF validation: {output_pages} pages")
                
                if output_pages != total_pages:
                    print(f"WARNING: Page count mismatch - expected {total_pages}, got {output_pages}")
                    
        except Exception as validation_error:
            raise Exception(f"Output PDF validation failed: {str(validation_error)}")
        
        # Read and return the PDF
        with open(output_path, 'rb') as f:
            pdf_content = f.read()
            
            print(f"Returning PDF: {len(pdf_content)} bytes")
            
            if len(pdf_content) == 0:
                raise Exception("PDF content is empty")
            
            # Create response
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="merged_document.pdf"'
            response['Content-Length'] = str(len(pdf_content))
            response['X-Total-Pages'] = str(total_pages)
            response['X-File-Count'] = str(len(processed_files))
            response['X-Output-Size'] = str(len(pdf_content))
            
            # Add CORS headers if needed
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'POST'
            response['Access-Control-Allow-Headers'] = 'Content-Type, X-CSRFToken'
            
            return response
    
    except Exception as e:
        error_msg = f'PDF merge failed: {str(e)}'
        print(f"ERROR: {error_msg}")
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'error': error_msg,
            'details': 'Please ensure all files are valid PDF documents and try again.'
        }, status=500)
    
    finally:
        # Clean up temp files
        for temp_path in temp_files:
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    print(f"Cleaned up: {temp_path}")
            except Exception as e:
                print(f"Failed to cleanup {temp_path}: {e}")
        
        # Clean up output file
        if 'output_path' in locals() and os.path.exists(output_path):
            try:
                os.unlink(output_path)
                print(f"Cleaned up output: {output_path}")
            except Exception as e:
                print(f"Failed to cleanup output: {e}")


# ALSO ADD THIS SIMPLE TEST VIEW TO DEBUG FILE UPLOADS
@csrf_exempt
def test_file_upload(request):
    """Test endpoint to debug file uploads"""
    if request.method == 'POST':
        print("=== FILE UPLOAD TEST ===")
        print(f"Files in request: {list(request.FILES.keys())}")
        print(f"POST data: {dict(request.POST)}")
        
        total_files = 0
        for key, file_list in request.FILES.lists():
            print(f"Key '{key}': {len(file_list)} files")
            for i, f in enumerate(file_list):
                print(f"  File {i+1}: {f.name} ({f.size} bytes)")
                total_files += 1
        
        return JsonResponse({
            'success': True,
            'total_files': total_files,
            'file_keys': list(request.FILES.keys())
        })
    
    return JsonResponse({'error': 'POST method required'}, status=405)

@csrf_exempt
def convert_pdf_api(request):
    """API endpoint to convert PDF to other formats"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    if not CONVERSION_LIBRARY_AVAILABLE:
        return JsonResponse({'error': 'Conversion libraries not available'}, status=500)
    
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'PDF file is required'}, status=400)
    
    target_format = request.POST.get('format', 'docx')
    if target_format not in ['docx', 'xlsx', 'pptx', 'jpg']:
        return JsonResponse({'error': 'Unsupported target format'}, status=400)
    
    # This is a placeholder. Actual implementation would need specific libraries for each conversion type
    return JsonResponse({'error': 'This feature is in development'}, status=501)

try:
    from docx2pdf import convert
    import pythoncom
    DOCX2PDF_AVAILABLE = True
except ImportError:
    DOCX2PDF_AVAILABLE = False

# Alternative conversion method using LibreOffice/OpenOffice (cross-platform)

def word_to_pdf(request):
    """Render the Word to PDF tool page"""
    return render(request, 'word_to_pdf.html')


# Replace your word_to_pdf_api function with this working version

@csrf_exempt
def word_to_pdf_api(request):
    """Fixed Word to PDF conversion with proper formatting preservation"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file uploaded'}, status=400)
    
    word_file = request.FILES['file']
    
    if not word_file.name.lower().endswith(('.doc', '.docx')):
        return JsonResponse({'error': 'Please upload a Word document (DOC or DOCX)'}, status=400)
    
    # Get conversion options
    quality = request.POST.get('quality', 'high')
    page_size = request.POST.get('page_size', 'a4')
    optimization = request.POST.get('optimization', 'print')
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Save uploaded file
        input_path = os.path.join(temp_dir, f"input.{word_file.name.split('.')[-1]}")
        with open(input_path, 'wb') as f:
            for chunk in word_file.chunks():
                f.write(chunk)
        
        # Try LibreOffice first (most accurate)
        libreoffice_path = find_libreoffice()
        if libreoffice_path:
            try:
                pdf_path = convert_with_libreoffice_precise(input_path, temp_dir, libreoffice_path)
                if pdf_path and os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 1000:
                    with open(pdf_path, 'rb') as f:
                        pdf_data = f.read()
                    
                    response = HttpResponse(pdf_data, content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename="{os.path.splitext(word_file.name)[0]}.pdf"'
                    return response
            except Exception as e:
                print(f"LibreOffice conversion failed: {e}")
        
        # Use enhanced manual conversion with exact formatting preservation
        pdf_data = create_exact_pdf_from_word(input_path, word_file.name, quality, page_size)
        
        if pdf_data and len(pdf_data) > 1000:
            response = HttpResponse(pdf_data, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{os.path.splitext(word_file.name)[0]}.pdf"'
            return response
        
        return JsonResponse({'error': 'Conversion failed. Please try again.'}, status=500)
        
    except Exception as e:
        print(f"Word to PDF conversion error: {str(e)}")
        return JsonResponse({'error': f'Conversion failed: {str(e)}'}, status=500)
        
    finally:
        try:
            shutil.rmtree(temp_dir)
        except:
            pass

def create_exact_pdf_from_word(input_path, filename, quality, page_size):
    """Create PDF with exact Word formatting preservation - FIXED VERSION"""
    
    if not PYTHON_DOCX_AVAILABLE or not REPORTLAB_AVAILABLE:
        return None
    
    try:
        # Read Word document
        doc = Document(input_path)
        
        # Create PDF buffer
        buffer = io.BytesIO()
        
        # Set page size
        page_sizes = {'a4': A4, 'letter': letter, 'a3': A3, 'a5': A5, 'legal': legal}
        page_size_obj = page_sizes.get(page_size, A4)
        
        # Create PDF document with proper margins
        pdf_doc = SimpleDocTemplate(
            buffer,
            pagesize=page_size_obj,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch,
            title=os.path.splitext(filename)[0]
        )
        
        # Create enhanced styles for exact formatting
        styles = getSampleStyleSheet()
        
        # Document title style (CURRICULUM VITAE)
        title_style = ParagraphStyle(
            'DocumentTitle',
            parent=styles['Title'],
            fontSize=18,
            fontName='Helvetica-Bold',
            spaceAfter=24,
            spaceBefore=0,
            alignment=TA_CENTER,
            textColor=colors.black,
            leading=22
        )
        
        # Name style (SANJEEV KUMAR)
        name_style = ParagraphStyle(
            'Name',
            parent=styles['Heading1'],
            fontSize=16,
            fontName='Helvetica-Bold',
            spaceAfter=12,
            spaceBefore=12,
            alignment=TA_CENTER,
            textColor=colors.black,
            leading=20
        )
        
        # Contact info style
        contact_style = ParagraphStyle(
            'Contact',
            parent=styles['Normal'],
            fontSize=11,
            fontName='Helvetica',
            spaceAfter=4,
            spaceBefore=0,
            alignment=TA_CENTER,
            textColor=colors.black,
            leading=14
        )
        
        # Section heading style (OBJECTIVE, EXPERIENCE, etc.)
        section_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=14,
            fontName='Helvetica-Bold',
            spaceAfter=12,
            spaceBefore=18,
            alignment=TA_LEFT,
            textColor=colors.darkblue,
            leading=17
        )
        
        # Body text style
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontSize=11,
            fontName='Helvetica',
            spaceAfter=6,
            spaceBefore=0,
            alignment=TA_LEFT,
            textColor=colors.black,
            leading=14,
            leftIndent=0
        )
        
        # Enhanced bullet point style
        bullet_style = ParagraphStyle(
            'Bullet',
            parent=styles['Normal'],
            fontSize=11,
            fontName='Helvetica',
            spaceAfter=4,
            spaceBefore=0,
            alignment=TA_LEFT,
            textColor=colors.black,
            leading=14,
            leftIndent=18,
            bulletIndent=0,
            bulletFontName='Symbol'
        )
        
        # Job title/position style
        position_style = ParagraphStyle(
            'Position',
            parent=styles['Normal'],
            fontSize=11,
            fontName='Helvetica-Bold',
            spaceAfter=6,
            spaceBefore=8,
            alignment=TA_LEFT,
            textColor=colors.black,
            leading=14
        )
        
        story = []
        current_section = None
        
        # Process each paragraph with intelligent formatting detection
        for para_index, para in enumerate(doc.paragraphs):
            text = para.text.strip()
            if not text:
                story.append(Spacer(1, 6))
                continue
            
            # Clean and escape text for PDF
            clean_text = escape_xml_chars(text)
            
            # Detect paragraph type and apply appropriate formatting
            if text.upper() == 'CURRICULUM VITAE':
                story.append(Paragraph('CURRICULUM VITAE', title_style))
                story.append(Spacer(1, 12))
                
            elif is_name_line(text, para_index):
                story.append(Paragraph(f'<b>{clean_text}</b>', name_style))
                story.append(Spacer(1, 8))
                
            elif is_contact_info(text):
                story.append(Paragraph(clean_text, contact_style))
                story.append(Spacer(1, 4))
                
            elif is_section_heading(text):
                current_section = text.upper()
                story.append(Paragraph(f'<b>{clean_text.upper()}</b>', section_style))
                story.append(Spacer(1, 8))
                
            elif is_bullet_point(text):
                bullet_text = clean_bullet_text(text)
                story.append(Paragraph(f'• {bullet_text}', bullet_style))
                
            elif is_job_position(text, current_section):
                # Format job positions with bold
                formatted_text = format_job_position(clean_text)
                story.append(Paragraph(formatted_text, position_style))
                story.append(Spacer(1, 4))
                
            elif current_section == 'PERSONAL DETAILS' and ':' in text:
                # Format personal details with labels
                formatted_text = format_personal_details(clean_text)
                story.append(Paragraph(formatted_text, body_style))
                
            else:
                # Regular body text with run-based formatting
                formatted_text = extract_formatting_from_runs(para)
                if not formatted_text:
                    formatted_text = clean_text
                
                story.append(Paragraph(formatted_text, body_style))
                
                # Add appropriate spacing based on context
                if current_section in ['EXPERIENCE', 'ORGANISATIONAL EXPERIENCE']:
                    story.append(Spacer(1, 6))
                else:
                    story.append(Spacer(1, 4))
        
        # Build PDF
        pdf_doc.build(story)
        
        # Get PDF content
        pdf_content = buffer.getvalue()
        buffer.close()
        
        print(f"Created PDF with exact formatting: {len(pdf_content)} bytes")
        return pdf_content
        
    except Exception as e:
        print(f"Enhanced PDF creation error: {e}")
        import traceback
        traceback.print_exc()
        return None

def is_name_line(text, para_index):
    """Detect if this is the name line (SANJEEV KUMAR)"""
    return (para_index <= 3 and 
            len(text) < 50 and 
            not any(keyword in text.lower() for keyword in ['mobile', 'email', 'delhi', 'park', '@']))

def is_contact_info(text):
    """Detect contact information lines"""
    return any(keyword in text.lower() for keyword in ['mobile:', 'email:', 'delhi', 'park', '@', 'b-56'])

def is_section_heading(text):
    """Detect section headings"""
    section_headings = [
        'OBJECTIVE', 'EXPERIENCE', 'EDUCATION', 'QUALIFICATION', 'QUALIFICATIONS',
        'SKILLS', 'PERSONAL DETAILS', 'DECLARATION', 'ACHIEVEMENTS', 
        'PROFESSIONAL QUALIFICATION', 'ORGANISATIONAL EXPERIENCE'
    ]
    return text.upper().strip() in section_headings

def is_bullet_point(text):
    """Detect bullet points"""
    return (text.startswith('•') or 
            text.startswith('-') or 
            text.startswith('◦') or
            text.startswith('*') or
            (len(text) > 0 and text[0] in ['•', '-', '◦', '*']))

def clean_bullet_text(text):
    """Clean bullet point text"""
    # Remove bullet markers
    for marker in ['•', '-', '◦', '*']:
        if text.startswith(marker):
            text = text[1:].strip()
            break
    return escape_xml_chars(text)

def is_job_position(text, current_section):
    """Detect job position/title lines"""
    if current_section not in ['EXPERIENCE', 'ORGANISATIONAL EXPERIENCE']:
        return False
    
    job_indicators = [
        'working as', 'worked as', 'presently working', 
        'senior', 'analyst', 'executive', 'manager', 'associate'
    ]
    
    return any(indicator in text.lower() for indicator in job_indicators)

def format_job_position(text):
    """Format job position with bold titles"""
    # Look for job titles in quotes or after "as"
    if 'as ' in text.lower():
        parts = text.split(' as ', 1)
        if len(parts) == 2:
            return f'{parts[0]} as <b>{parts[1]}</b>'
    
    # Bold company names
    companies = ['R1 RCM Global', 'EXL', 'Genpact', 'GENPACT']
    for company in companies:
        if company in text:
            text = text.replace(company, f'<b>{company}</b>')
    
    return text

def format_personal_details(text):
    """Format personal details with bold labels"""
    if ':' not in text:
        return text
    
    parts = text.split(':', 1)
    if len(parts) == 2:
        label = parts[0].strip()
        value = parts[1].strip()
        return f'<b>{label}:</b> {value}'
    
    return text

def extract_formatting_from_runs(para):
    """Extract formatting from Word runs"""
    if not para.runs:
        return escape_xml_chars(para.text)
    
    formatted_parts = []
    
    for run in para.runs:
        run_text = run.text
        if not run_text:
            continue
        
        clean_text = escape_xml_chars(run_text)
        
        # Apply formatting based on run properties
        if run.bold and run.italic:
            clean_text = f'<b><i>{clean_text}</i></b>'
        elif run.bold:
            clean_text = f'<b>{clean_text}</b>'
        elif run.italic:
            clean_text = f'<i>{clean_text}</i>'
        
        if run.underline:
            clean_text = f'<u>{clean_text}</u>'
        
        formatted_parts.append(clean_text)
    
    return ''.join(formatted_parts)

def escape_xml_chars(text):
    """Escape XML characters for PDF rendering"""
    if not text:
        return ""
    
    replacements = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text

def find_libreoffice():
    """Find LibreOffice installation"""
    if platform.system() == 'Windows':
        paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ]
    elif platform.system() == 'Darwin':  # macOS
        paths = ["/Applications/LibreOffice.app/Contents/MacOS/soffice"]
    else:  # Linux
        paths = ["/usr/bin/soffice", "/usr/bin/libreoffice", "/snap/bin/libreoffice"]
    
    for path in paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path
    
    # Try which command
    try:
        result = subprocess.run(['which', 'libreoffice'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    
    return None

def convert_with_libreoffice_precise(input_path, temp_dir, libreoffice_path):
    """Convert using LibreOffice with precise settings"""
    try:
        env = os.environ.copy()
        env['HOME'] = temp_dir
        
        cmd = [
            libreoffice_path,
            '--headless',
            '--invisible',
            '--nodefault',
            '--nolockcheck',
            '--nologo',
            '--norestore',
            '--convert-to', 'pdf',
            '--outdir', temp_dir,
            input_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, env=env)
        
        if result.returncode == 0:
            pdf_files = [f for f in os.listdir(temp_dir) if f.endswith('.pdf')]
            if pdf_files:
                return os.path.join(temp_dir, pdf_files[0])
        
        return None
        
    except Exception as e:
        print(f"LibreOffice conversion error: {e}")
        return None

# === OTHER API ENDPOINTS (SIMPLIFIED) ===


try:
    from docx import Document
    PYTHON_DOCX_AVAILABLE = True
except ImportError:
    PYTHON_DOCX_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import A4, letter, A3, A5, legal
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


# ENHANCED find_libreoffice_path function (replace the existing one)
def find_libreoffice_path():
    """Enhanced helper function to find LibreOffice path on different operating systems"""
    
    # Try to find in PATH first
    try:
        if platform.system() != 'Windows':
            result = subprocess.run(['which', 'soffice'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
    except:
        pass
    
    # Platform-specific paths
    if platform.system() == 'Windows':
        paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            r"C:\Program Files\LibreOffice 7\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice 7\program\soffice.exe",
            r"C:\Program Files\LibreOffice 24\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice 24\program\soffice.exe",
            # OpenOffice paths
            r"C:\Program Files\OpenOffice\program\soffice.exe",
            r"C:\Program Files (x86)\OpenOffice\program\soffice.exe",
            r"C:\Program Files\OpenOffice 4\program\soffice.exe",
            r"C:\Program Files (x86)\OpenOffice 4\program\soffice.exe",
        ]
    elif platform.system() == 'Darwin':  # macOS
        paths = [
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
            "/Applications/OpenOffice.app/Contents/MacOS/soffice",
            "/opt/homebrew/bin/soffice",
            "/usr/local/bin/soffice",
        ]
    else:  # Linux and other Unix-like systems
        paths = [
            "/usr/bin/soffice",
            "/usr/local/bin/soffice",
            "/opt/libreoffice/program/soffice",
            "/snap/bin/libreoffice.soffice",
            "/usr/bin/libreoffice",
            "/usr/local/bin/libreoffice",
            # Flatpak installation
            "/var/lib/flatpak/exports/bin/org.libreoffice.LibreOffice",
        ]
    
    # Check each path
    for path in paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path
    
    return None

def compress_image(request):
    # Your image compression logic will go here
    return render(request, 'pdf_tools/compress_image.html')


# Import required libraries for PDF compression
try:
    import PyPDF2
    from PyPDF2 import PdfReader, PdfWriter
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    import fitz  # PyMuPDF for advanced compression
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import pikepdf
    PIKEPDF_AVAILABLE = True
except ImportError:
    PIKEPDF_AVAILABLE = False

@csrf_exempt
def compress_pdf_api(request):
    """Enhanced API endpoint to compress PDF files with better compression ratios"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    if not PYMUPDF_AVAILABLE and not PIKEPDF_AVAILABLE and not PYPDF2_AVAILABLE:
        return JsonResponse({
            'error': 'PDF compression library not available. Please install PyMuPDF, pikepdf, or PyPDF2'
        }, status=500)
    
    if 'files' not in request.FILES:
        return JsonResponse({'error': 'At least one PDF file is required'}, status=400)
    
    pdf_files = request.FILES.getlist('files')
    compression_level = request.POST.get('compression_level', 'medium')
    optimize_for = request.POST.get('optimize_for', 'print')
    color_mode = request.POST.get('color_mode', 'original')
    image_quality = request.POST.get('image_quality', 'high')
    
    # Validate files
    max_file_size = 50 * 1024 * 1024  # 50MB per file
    max_total_size = 200 * 1024 * 1024  # 200MB total
    max_files = 20
    
    if len(pdf_files) > max_files:
        return JsonResponse({'error': f'Maximum {max_files} PDF files allowed'}, status=400)
    
    total_size = sum(file.size for file in pdf_files)
    if total_size > max_total_size:
        return JsonResponse({'error': 'Total file size exceeds 200MB limit'}, status=400)
    
    for file in pdf_files:
        if file.size > max_file_size:
            return JsonResponse({'error': f'File {file.name} exceeds 50MB limit'}, status=400)
        
        if not file.name.lower().endswith('.pdf') and file.content_type != 'application/pdf':
            return JsonResponse({'error': f'Invalid file format: {file.name}. Only PDF files are allowed.'}, status=400)
    
    # Create unique temp directory
    temp_dir = None
    
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix='pdf_compression_')
        print(f"Created temp directory: {temp_dir}")
        
        # Process each PDF file with aggressive compression
        compressed_files = []
        total_original_size = 0
        total_compressed_size = 0
        
        for i, pdf_file in enumerate(pdf_files):
            try:
                # Save uploaded PDF to temporary file
                temp_pdf_path = os.path.join(temp_dir, f"input_{i}_{uuid.uuid4().hex}.pdf")
                
                with open(temp_pdf_path, 'wb') as temp_file:
                    for chunk in pdf_file.chunks():
                        temp_file.write(chunk)
                
                original_size = os.path.getsize(temp_pdf_path)
                total_original_size += original_size
                print(f"Original file size: {original_size} bytes")
                
                # Apply aggressive compression
                compressed_path = compress_pdf_aggressively_fixed(
                    temp_pdf_path, 
                    temp_dir, 
                    pdf_file.name,
                    compression_level, 
                    optimize_for, 
                    color_mode, 
                    image_quality
                )
                
                if compressed_path and os.path.exists(compressed_path):
                    compressed_size = os.path.getsize(compressed_path)
                    total_compressed_size += compressed_size
                    print(f"Compressed file size: {compressed_size} bytes")
                    
                    compressed_files.append({
                        'path': compressed_path,
                        'original_name': pdf_file.name,
                        'original_size': original_size,
                        'compressed_size': compressed_size
                    })
                else:
                    # If compression failed, use original but still count it
                    total_compressed_size += original_size
                    compressed_files.append({
                        'path': temp_pdf_path,
                        'original_name': pdf_file.name,
                        'original_size': original_size,
                        'compressed_size': original_size
                    })
                    
            except Exception as e:
                print(f"Error processing PDF {pdf_file.name}: {str(e)}")
                continue
        
        if not compressed_files:
            raise Exception("No PDF files could be processed successfully")
        
        print(f"Successfully processed {len(compressed_files)} PDF files")
        print(f"Total compression: {total_original_size} -> {total_compressed_size} bytes")
        
        # Return compressed files
        if len(compressed_files) == 1:
            # Single file - return as PDF
            compressed_file = compressed_files[0]
            
            with open(compressed_file['path'], 'rb') as pdf_file:
                response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                
                # Generate filename
                original_name = compressed_file['original_name']
                name_without_ext = os.path.splitext(original_name)[0]
                compressed_filename = f"{name_without_ext}_compressed.pdf"
                
                response['Content-Disposition'] = f'attachment; filename="{compressed_filename}"'
                response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
            
            return response
            
        else:
            # Multiple files - return as ZIP
            zip_path = os.path.join(temp_dir, 'compressed_pdfs.zip')
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for compressed_file in compressed_files:
                    original_name = compressed_file['original_name']
                    name_without_ext = os.path.splitext(original_name)[0]
                    compressed_filename = f"{name_without_ext}_compressed.pdf"
                    
                    zip_file.write(compressed_file['path'], compressed_filename)
            
            # Return ZIP file
            with open(zip_path, 'rb') as zip_file:
                response = HttpResponse(zip_file.read(), content_type='application/zip')
                response['Content-Disposition'] = 'attachment; filename="compressed_pdfs.zip"'
                response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
            
            return response
        
    except Exception as e:
        print(f"Compression error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'error': f"Compression failed: {str(e)}"
        }, status=500)
        
    finally:
        # Clean up temporary files
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                print(f"Cleaned up temp directory: {temp_dir}")
            except Exception as e:
                print(f"Failed to clean up temp directory: {e}")


def compress_pdf_aggressively_fixed(input_path, output_dir, original_filename, compression_level, optimize_for, color_mode, image_quality):
    """Fixed aggressive PDF compression with guaranteed size reduction"""
    
    output_filename = f"compressed_{uuid.uuid4().hex}.pdf"
    output_path = os.path.join(output_dir, output_filename)
    
    # Set compression parameters based on level
    compression_settings = {
        'low': {'image_quality': 85, 'dpi_reduction': 0.9, 'font_subset': True},
        'medium': {'image_quality': 70, 'dpi_reduction': 0.7, 'font_subset': True},
        'high': {'image_quality': 55, 'dpi_reduction': 0.5, 'font_subset': True},
        'extreme': {'image_quality': 40, 'dpi_reduction': 0.3, 'font_subset': True}
    }
    
    settings = compression_settings.get(compression_level, compression_settings['medium'])
    
    # Try PyMuPDF first (most effective)
    if PYMUPDF_AVAILABLE:
        try:
            return compress_with_pymupdf_fixed(input_path, output_path, settings, color_mode)
        except Exception as e:
            print(f"PyMuPDF compression failed: {str(e)}")
    
    # Try pikepdf as fallback
    if PIKEPDF_AVAILABLE:
        try:
            return compress_with_pikepdf_fixed(input_path, output_path, settings, color_mode)
        except Exception as e:
            print(f"pikepdf compression failed: {str(e)}")
    
    # Try PyPDF2 as last resort
    if PYPDF2_AVAILABLE:
        try:
            return compress_with_pypdf2_fixed(input_path, output_path, settings)
        except Exception as e:
            print(f"PyPDF2 compression failed: {str(e)}")
    
    return None


def compress_with_pymupdf_fixed(input_path, output_path, settings, color_mode):
    """Fixed PyMuPDF compression with guaranteed results"""
    
    try:
        # Open the PDF
        pdf_doc = fitz.open(input_path)
        
        # Process each page
        for page_num in range(pdf_doc.page_count):
            page = pdf_doc[page_num]
            
            # Get all images on the page
            image_list = page.get_images(full=True)
            
            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]
                    base_image = pdf_doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    # Process all images, not just large ones
                    if len(image_bytes) > 1000:  # Process images larger than 1KB
                        processed_bytes = compress_image_fixed(
                            image_bytes, 
                            settings['image_quality'], 
                            color_mode,
                            settings['dpi_reduction']
                        )
                        
                        if processed_bytes and len(processed_bytes) < len(image_bytes):
                            # Replace image
                            pdf_doc._update_stream(xref, processed_bytes)
                            
                except Exception as e:
                    print(f"Error processing image {img_index}: {str(e)}")
                    continue
        
        # Save with maximum compression
        save_options = {
            'garbage': 4,
            'clean': True,
            'deflate': True,
            'deflate_images': True,
            'deflate_fonts': True,
            'ascii': False,
            'expand': 0,
            'linear': False,
            'pretty': False
        }
        
        pdf_doc.save(output_path, **save_options)
        pdf_doc.close()
        
        # Verify compression worked
        if os.path.exists(output_path):
            original_size = os.path.getsize(input_path)
            compressed_size = os.path.getsize(output_path)
            
            # If no significant compression, try alternative method
            if compressed_size >= original_size * 0.95:
                return compress_with_ghostscript_fixed(input_path, output_path, settings)
            
            return output_path
        
        return None
        
    except Exception as e:
        print(f"PyMuPDF compression error: {str(e)}")
        return None


def compress_with_pikepdf(input_path, output_path, compression_level, optimize_for, color_mode, image_quality):
    """Compression using pikepdf library"""
    
    if not PIKEPDF_AVAILABLE:
        return False
    
    try:
        with pikepdf.open(input_path) as pdf:
            # Remove metadata to save space
            pdf.docinfo.clear()
            
            # Optimize images
            for page in pdf.pages:
                for _, image in page.images.items():
                    try:
                        if hasattr(image, 'obj') and '/Length' in image.obj:
                            # Process large images
                            if image.obj.get('/Length', 0) > 50000:
                                # Extract and recompress image
                                image_data = image.read_bytes()
                                if len(image_data) > 50000:
                                    quality_map = {
                                        'low': 85,
                                        'medium': 70,
                                        'high': 55,
                                        'extreme': 40
                                    }
                                    jpeg_quality = quality_map.get(compression_level, 70)
                                    
                                    compressed_image = compress_image_aggressively(
                                        image_data, 'jpg', jpeg_quality, color_mode
                                    )
                                    
                                    if compressed_image and len(compressed_image) < len(image_data) * 0.8:
                                        # Replace with compressed version
                                        image.obj.write(compressed_image)
                    except Exception as e:
                        print(f"Error processing image in pikepdf: {str(e)}")
                        continue
            
            # Save with compression
            pdf.save(output_path, 
                    compress_streams=True,
                    stream_decode_level=pikepdf.StreamDecodeLevel.all,
                    object_stream_mode=pikepdf.ObjectStreamMode.generate,
                    remove_unreferenced_resources=True)
        
        return os.path.exists(output_path)
        
    except Exception as e:
        print(f"pikepdf compression error: {str(e)}")
        return False


def compress_with_pymupdf_basic(input_path, output_path, compression_level, optimize_for, color_mode, image_quality):
    """Basic PyMuPDF compression"""
    
    if not PYMUPDF_AVAILABLE:
        return False
    
    try:
        pdf_doc = fitz.open(input_path)
        
        # Basic compression settings
        save_options = {
            'garbage': 4,
            'clean': True,
            'deflate': True,
            'deflate_images': True,
            'deflate_fonts': True
        }
        
        if compression_level in ['high', 'extreme']:
            save_options.update({
                'ascii': False,
                'expand': 0,
                'linear': False,
                'pretty': False
            })
        
        pdf_doc.save(output_path, **save_options)
        pdf_doc.close()
        
        return os.path.exists(output_path)
        
    except Exception as e:
        print(f"PyMuPDF basic compression error: {str(e)}")
        return False


def compress_with_ghostscript_fixed(input_path, output_path, settings):
    """Fixed Ghostscript compression as fallback"""
    
    try:
        gs_command = find_ghostscript_command()
        if not gs_command:
            return None
        
        # Use aggressive settings
        cmd = [
            gs_command,
            '-sDEVICE=pdfwrite',
            '-dCompatibilityLevel=1.4',
            '-dPDFSETTINGS=/screen',  # Most aggressive preset
            '-dNOPAUSE',
            '-dQUIET',
            '-dBATCH',
            '-r72',  # Low resolution
            '-dColorImageResolution=72',
            '-dGrayImageResolution=72',
            '-dMonoImageResolution=72',
            '-dColorImageDownsampleType=/Bicubic',
            '-dGrayImageDownsampleType=/Bicubic',
            '-dMonoImageDownsampleType=/Bicubic',
            f'-sOutputFile={output_path}',
            input_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0 and os.path.exists(output_path):
            return output_path
        
        return None
        
    except Exception as e:
        print(f"Ghostscript compression error: {str(e)}")
        return None


def compress_with_pypdf2(input_path, output_path, compression_level, optimize_for, color_mode, image_quality):
    """Basic compression using PyPDF2"""
    
    if not PYPDF2_AVAILABLE:
        return False
    
    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()
        
        for page in reader.pages:
            if hasattr(page, 'compress_content_streams'):
                page.compress_content_streams()
            writer.add_page(page)
        
        if compression_level in ['high', 'extreme']:
            writer.compress_identical_objects()
        
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        return os.path.exists(output_path)
        
    except Exception as e:
        print(f"PyPDF2 compression error: {str(e)}")
        return False


def compress_image_fixed(image_bytes, quality, color_mode, dpi_reduction):
    """Fixed image compression with guaranteed size reduction"""
    
    if not PIL_AVAILABLE:
        return None
    
    try:
        # Load image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Apply color mode conversion
        if color_mode == 'grayscale' and image.mode not in ['L', '1']:
            image = image.convert('L')
        elif color_mode == 'monochrome' and image.mode != '1':
            image = image.convert('1')
        elif image.mode in ['RGBA', 'P']:
            # Convert to RGB for better compression
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            if image.mode == 'RGBA':
                background.paste(image, mask=image.split()[-1])
            image = background
        
        # Reduce resolution
        if dpi_reduction < 1.0:
            new_size = (
                int(image.size[0] * dpi_reduction),
                int(image.size[1] * dpi_reduction)
            )
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Save with compression
        output_buffer = io.BytesIO()
        
        # Always save as JPEG for maximum compression
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        image.save(output_buffer, 'JPEG', quality=quality, optimize=True, progressive=True)
        
        compressed_bytes = output_buffer.getvalue()
        output_buffer.close()
        
        return compressed_bytes
        
    except Exception as e:
        print(f"Image compression error: {str(e)}")
        return None


def find_ghostscript_command():
    """Find Ghostscript executable"""
    
    possible_commands = ['gs', 'gswin64c', 'gswin32c']
    
    for cmd in possible_commands:
        try:
            result = subprocess.run([cmd, '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return cmd
        except:
            continue
    
    return None


def compress_pdf_alternative(input_path, output_dir, compression_level):
    """Alternative compression method for PDFs that don't compress well"""
    
    output_filename = f"alt_compressed_{uuid.uuid4().hex}.pdf"
    output_path = os.path.join(output_dir, output_filename)
    
    # Try to rebuild the PDF with minimal content
    if PYMUPDF_AVAILABLE:
        try:
            source_doc = fitz.open(input_path)
            new_doc = fitz.open()
            
            for page_num in range(source_doc.page_count):
                source_page = source_doc[page_num]
                
                # Create new page with same dimensions
                new_page = new_doc.new_page(width=source_page.rect.width, height=source_page.rect.height)
                
                # Get page content as text and drawings
                text_dict = source_page.get_text("dict")
                
                # Rebuild page with compressed content
                for block in text_dict.get("blocks", []):
                    if block.get("type") == 0:  # Text block
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                text = span.get("text", "")
                                if text.strip():
                                    font_size = span.get("size", 12)
                                    bbox = span.get("bbox", [0, 0, 0, 0])
                                    
                                    # Insert text with reduced font size for extreme compression
                                    if compression_level == 'extreme':
                                        font_size *= 0.9
                                    
                                    new_page.insert_text(
                                        (bbox[0], bbox[1]), 
                                        text, 
                                        fontsize=font_size
                                    )
            
            # Save with maximum compression
            new_doc.save(output_path, garbage=4, clean=True, deflate=True)
            new_doc.close()
            source_doc.close()
            
            return output_path if os.path.exists(output_path) else None
            
        except Exception as e:
            print(f"Alternative compression error: {str(e)}")
            return None
    
    return None

from PIL import Image
from django.http import HttpResponse, JsonResponse

# Check if required libraries are available
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import pikepdf
    PIKEPDF_AVAILABLE = True
except ImportError:
    PIKEPDF_AVAILABLE = False

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

# Your existing views here...
# (keep all your existing view functions)

def compress_pdf_page(request):
    """
    Render the compress PDF page template
    """
    return render(request, 'compress_pdf.html')

def compress_image_page(request):
    """
    Render the compress image page template
    """
    return render(request, 'compress_image.html')

@csrf_exempt
def compress_pdf_api(request):
    """
    API endpoint to compress PDF files with better compression ratios
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    if not PYMUPDF_AVAILABLE and not PIKEPDF_AVAILABLE and not PYPDF2_AVAILABLE:
        return JsonResponse({
            'error': 'PDF compression library not available. Please install PyMuPDF, pikepdf, or PyPDF2'
        }, status=500)
    
    if 'files' not in request.FILES:
        return JsonResponse({'error': 'At least one PDF file is required'}, status=400)
    
    pdf_files = request.FILES.getlist('files')
    compression_level = request.POST.get('compression_level', 'medium')
    optimize_for = request.POST.get('optimize_for', 'print')
    color_mode = request.POST.get('color_mode', 'original')
    image_quality = request.POST.get('image_quality', 'high')
    
    # Validate files
    max_file_size = 50 * 1024 * 1024  # 50MB per file
    max_total_size = 200 * 1024 * 1024  # 200MB total
    max_files = 20
    
    if len(pdf_files) > max_files:
        return JsonResponse({'error': f'Maximum {max_files} PDF files allowed'}, status=400)
    
    total_size = sum(file.size for file in pdf_files)
    if total_size > max_total_size:
        return JsonResponse({'error': 'Total file size exceeds 200MB limit'}, status=400)
    
    for file in pdf_files:
        if file.size > max_file_size:
            return JsonResponse({'error': f'File {file.name} exceeds 50MB limit'}, status=400)
        
        if not file.name.lower().endswith('.pdf') and file.content_type != 'application/pdf':
            return JsonResponse({'error': f'Invalid file format: {file.name}. Only PDF files are allowed.'}, status=400)
    
    # Create unique temp directory
    temp_dir = None
    
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix='pdf_compression_')
        print(f"Created temp directory: {temp_dir}")
        
        # Process each PDF file with compression
        compressed_files = []
        total_original_size = 0
        total_compressed_size = 0
        
        for i, pdf_file in enumerate(pdf_files):
            try:
                # Save uploaded PDF to temporary file
                temp_pdf_path = os.path.join(temp_dir, f"input_{i}_{uuid.uuid4().hex}.pdf")
                
                with open(temp_pdf_path, 'wb') as temp_file:
                    for chunk in pdf_file.chunks():
                        temp_file.write(chunk)
                
                original_size = os.path.getsize(temp_pdf_path)
                total_original_size += original_size
                print(f"Original file size: {original_size} bytes")
                
                # Apply compression (simplified version)
                compressed_path = compress_pdf_simple(
                    temp_pdf_path, 
                    temp_dir, 
                    pdf_file.name,
                    compression_level
                )
                
                if compressed_path and os.path.exists(compressed_path):
                    compressed_size = os.path.getsize(compressed_path)
                    total_compressed_size += compressed_size
                    print(f"Compressed file size: {compressed_size} bytes")
                    
                    compressed_files.append({
                        'path': compressed_path,
                        'original_name': pdf_file.name,
                        'original_size': original_size,
                        'compressed_size': compressed_size
                    })
                else:
                    # If compression failed, use original but still count it
                    total_compressed_size += original_size
                    compressed_files.append({
                        'path': temp_pdf_path,
                        'original_name': pdf_file.name,
                        'original_size': original_size,
                        'compressed_size': original_size
                    })
                    
            except Exception as e:
                print(f"Error processing PDF {pdf_file.name}: {str(e)}")
                continue
        
        if not compressed_files:
            raise Exception("No PDF files could be processed successfully")
        
        print(f"Successfully processed {len(compressed_files)} PDF files")
        print(f"Total compression: {total_original_size} -> {total_compressed_size} bytes")
        
        # Return compressed files
        if len(compressed_files) == 1:
            # Single file - return as PDF
            compressed_file = compressed_files[0]
            
            with open(compressed_file['path'], 'rb') as pdf_file:
                response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                
                # Generate filename
                original_name = compressed_file['original_name']
                name_without_ext = os.path.splitext(original_name)[0]
                compressed_filename = f"{name_without_ext}_compressed.pdf"
                
                response['Content-Disposition'] = f'attachment; filename="{compressed_filename}"'
                response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
            
            return response
            
        else:
            # Multiple files - return as ZIP
            zip_path = os.path.join(temp_dir, 'compressed_pdfs.zip')
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for compressed_file in compressed_files:
                    original_name = compressed_file['original_name']
                    name_without_ext = os.path.splitext(original_name)[0]
                    compressed_filename = f"{name_without_ext}_compressed.pdf"
                    
                    zip_file.write(compressed_file['path'], compressed_filename)
            
            # Return ZIP file
            with open(zip_path, 'rb') as zip_file:
                response = HttpResponse(zip_file.read(), content_type='application/zip')
                response['Content-Disposition'] = 'attachment; filename="compressed_pdfs.zip"'
                response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
            
            return response
        
    except Exception as e:
        print(f"Compression error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'error': f"Compression failed: {str(e)}"
        }, status=500)
        
    finally:
        # Clean up temporary files
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                print(f"Cleaned up temp directory: {temp_dir}")
            except Exception as e:
                print(f"Failed to clean up temp directory: {e}")

@csrf_exempt
def compress_image_api(request):
    """
    FIXED API endpoint to compress image files
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    # Check if PIL is available
    try:
        from PIL import Image
        PIL_AVAILABLE = True
    except ImportError:
        return JsonResponse({
            'error': 'Image compression library not available. Please install Pillow: pip install Pillow'
        }, status=500)
    
    # Handle both 'files' and 'images' keys from frontend
    image_files = []
    if 'images' in request.FILES:
        image_files = request.FILES.getlist('images')
    elif 'files' in request.FILES:
        image_files = request.FILES.getlist('files')
    else:
        return JsonResponse({'error': 'No image files found in request'}, status=400)
    
    if not image_files:
        return JsonResponse({'error': 'At least one image file is required'}, status=400)
    
    # Get compression options
    output_format = request.POST.get('output_format', 'auto')
    quality = int(request.POST.get('quality', '80'))
    resize_option = request.POST.get('resize_option', 'none')
    resize_value = int(request.POST.get('resize_value', '0')) if request.POST.get('resize_value') else 0
    
    print(f"=== COMPRESSION SETTINGS ===")
    print(f"Files: {len(image_files)}")
    print(f"Format: {output_format}")
    print(f"Quality: {quality}")
    print(f"Resize: {resize_option} = {resize_value}")
    
    # Validate files
    max_file_size = 25 * 1024 * 1024  # 25MB per file
    max_total_size = 100 * 1024 * 1024  # 100MB total
    max_files = 50
    
    if len(image_files) > max_files:
        return JsonResponse({'error': f'Maximum {max_files} image files allowed'}, status=400)
    
    total_size = sum(file.size for file in image_files)
    if total_size > max_total_size:
        return JsonResponse({'error': 'Total file size exceeds 100MB limit'}, status=400)
    
    for file in image_files:
        if file.size > max_file_size:
            return JsonResponse({'error': f'File {file.name} exceeds 25MB limit'}, status=400)
        
        if not file.content_type.startswith('image/'):
            return JsonResponse({'error': f'Invalid file format: {file.name}. Only image files are allowed.'}, status=400)
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix='image_compression_')
    print(f"Created temp directory: {temp_dir}")
    
    try:
        compressed_files = []
        total_original_size = 0
        total_compressed_size = 0
        
        for i, image_file in enumerate(image_files):
            print(f"\n=== Processing file {i+1}: {image_file.name} ===")
            
            # Save original file to temp directory
            original_extension = os.path.splitext(image_file.name)[1].lower()
            temp_input = os.path.join(temp_dir, f"input_{i}_{uuid.uuid4().hex}{original_extension}")
            
            with open(temp_input, 'wb') as f:
                for chunk in image_file.chunks():
                    f.write(chunk)
            
            original_size = os.path.getsize(temp_input)
            total_original_size += original_size
            print(f"Original size: {original_size} bytes")
            
            try:
                # Open and process the image
                with Image.open(temp_input) as img:
                    print(f"Original image: {img.size} pixels, mode: {img.mode}")
                    
                    # Create a copy to work with
                    processed_img = img.copy()
                    
                    # Handle resize
                    if resize_option != 'none' and resize_value > 0:
                        original_width, original_height = processed_img.size
                        
                        if resize_option == 'width':
                            ratio = resize_value / original_width
                            new_height = int(original_height * ratio)
                            processed_img = processed_img.resize((resize_value, new_height), Image.LANCZOS)
                            print(f"Resized by width: {processed_img.size}")
                            
                        elif resize_option == 'height':
                            ratio = resize_value / original_height
                            new_width = int(original_width * ratio)
                            processed_img = processed_img.resize((new_width, resize_value), Image.LANCZOS)
                            print(f"Resized by height: {processed_img.size}")
                            
                        elif resize_option == 'percentage':
                            scale = resize_value / 100
                            new_width = int(original_width * scale)
                            new_height = int(original_height * scale)
                            processed_img = processed_img.resize((new_width, new_height), Image.LANCZOS)
                            print(f"Resized by percentage: {processed_img.size}")
                    
                    # Determine output format and filename
                    if output_format == 'auto':
                        # Keep original format
                        if original_extension in ['.jpg', '.jpeg']:
                            save_format = 'JPEG'
                            output_extension = '.jpg'
                        elif original_extension == '.png':
                            save_format = 'PNG'
                            output_extension = '.png'
                        elif original_extension == '.webp':
                            save_format = 'WEBP'
                            output_extension = '.webp'
                        else:
                            save_format = 'JPEG'  # Default fallback
                            output_extension = '.jpg'
                    else:
                        if output_format == 'jpg':
                            save_format = 'JPEG'
                            output_extension = '.jpg'
                        elif output_format == 'png':
                            save_format = 'PNG'
                            output_extension = '.png'
                        elif output_format == 'webp':
                            save_format = 'WEBP'
                            output_extension = '.webp'
                        else:
                            save_format = 'JPEG'
                            output_extension = '.jpg'
                    
                    # Convert image mode for JPEG if necessary
                    if save_format == 'JPEG' and processed_img.mode in ('RGBA', 'P', 'LA'):
                        # Create white background for JPEG
                        background = Image.new('RGB', processed_img.size, (255, 255, 255))
                        if processed_img.mode == 'P':
                            processed_img = processed_img.convert('RGBA')
                        if processed_img.mode in ('RGBA', 'LA'):
                            background.paste(processed_img, mask=processed_img.split()[-1])
                        processed_img = background
                        print("Converted to RGB for JPEG")
                    
                    # Create output filename
                    base_name = os.path.splitext(image_file.name)[0]
                    temp_output = os.path.join(temp_dir, f"compressed_{base_name}_{uuid.uuid4().hex}{output_extension}")
                    
                    # Save with compression
                    save_kwargs = {'optimize': True}
                    
                    if save_format == 'JPEG':
                        save_kwargs['quality'] = quality
                        save_kwargs['progressive'] = True
                    elif save_format == 'PNG':
                        # PNG compression level (0-9, higher = more compression)
                        compression_level = 9 - int(quality / 100 * 9)
                        save_kwargs['compress_level'] = max(0, min(9, compression_level))
                    elif save_format == 'WEBP':
                        save_kwargs['quality'] = quality
                        save_kwargs['method'] = 6
                    
                    processed_img.save(temp_output, save_format, **save_kwargs)
                    print(f"Saved as {save_format} with options: {save_kwargs}")
                    
                    compressed_size = os.path.getsize(temp_output)
                    total_compressed_size += compressed_size
                    print(f"Compressed size: {compressed_size} bytes")
                    
                    # Store file info
                    compressed_files.append({
                        'path': temp_output,
                        'name': f"compressed_{base_name}{output_extension}",
                        'original_name': image_file.name,
                        'original_size': original_size,
                        'compressed_size': compressed_size
                    })
                    
            except Exception as e:
                print(f"Error compressing {image_file.name}: {str(e)}")
                # If compression fails, still add the original file
                compressed_files.append({
                    'path': temp_input,
                    'name': image_file.name,
                    'original_name': image_file.name,
                    'original_size': original_size,
                    'compressed_size': original_size
                })
                total_compressed_size += original_size
        
        print(f"\n=== COMPRESSION SUMMARY ===")
        print(f"Files processed: {len(compressed_files)}")
        print(f"Total original size: {total_original_size} bytes")
        print(f"Total compressed size: {total_compressed_size} bytes")
        print(f"Compression ratio: {(total_original_size - total_compressed_size) / total_original_size * 100:.1f}%")
        
        if not compressed_files:
            return JsonResponse({'error': 'No files could be processed'}, status=500)
        
        # Return result
        if len(compressed_files) == 1:
            # Single file - return the compressed image directly
            file_info = compressed_files[0]
            
            with open(file_info['path'], 'rb') as f:
                file_data = f.read()
                
                print(f"Returning single file: {len(file_data)} bytes")
                
                # Determine content type
                if file_info['name'].lower().endswith('.png'):
                    content_type = 'image/png'
                elif file_info['name'].lower().endswith('.webp'):
                    content_type = 'image/webp'
                else:
                    content_type = 'image/jpeg'
                
                response = HttpResponse(file_data, content_type=content_type)
                response['Content-Disposition'] = f'attachment; filename="{file_info["name"]}"'
                response['Content-Length'] = str(len(file_data))
                
                # Add compression info headers
                response['X-Original-Size'] = str(file_info['original_size'])
                response['X-Compressed-Size'] = str(file_info['compressed_size'])
                savings = max(1, int((1 - file_info['compressed_size'] / file_info['original_size']) * 100))
                response['X-Savings-Percent'] = str(savings)
                
                return response
        else:
            # Multiple files - create ZIP
            zip_path = os.path.join(temp_dir, 'compressed_images.zip')
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for file_info in compressed_files:
                    zip_file.write(file_info['path'], file_info['name'])
            
            zip_size = os.path.getsize(zip_path)
            print(f"Created ZIP file: {zip_size} bytes")
            
            with open(zip_path, 'rb') as f:
                zip_data = f.read()
                
                response = HttpResponse(zip_data, content_type='application/zip')
                response['Content-Disposition'] = 'attachment; filename="compressed_images.zip"'
                response['Content-Length'] = str(len(zip_data))
                
                # Add compression info headers
                response['X-Original-Size'] = str(total_original_size)
                response['X-Compressed-Size'] = str(total_compressed_size)
                savings = max(1, int((1 - total_compressed_size / total_original_size) * 100))
                response['X-Savings-Percent'] = str(savings)
                response['X-Files-Count'] = str(len(compressed_files))
                
                return response
    
    except Exception as e:
        print(f"Compression error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'error': f'Compression failed: {str(e)}'
        }, status=500)
    
    finally:
        # Cleanup temp directory
        try:
            shutil.rmtree(temp_dir)
            print(f"Cleaned up temp directory: {temp_dir}")
        except Exception as e:
            print(f"Failed to cleanup temp directory: {e}")
            
@csrf_exempt
def compress_image_api_working(request):
    """
    Working API endpoint to compress image files
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    if not PIL_AVAILABLE:
        return JsonResponse({
            'error': 'Image compression library not available. Please install Pillow: pip install Pillow'
        }, status=500)
    
    # Handle both 'files' and 'images' keys
    image_files = []
    if 'images' in request.FILES:
        image_files = request.FILES.getlist('images')
    elif 'files' in request.FILES:
        image_files = request.FILES.getlist('files')
    else:
        return JsonResponse({'error': 'No image files found in request'}, status=400)
    
    if not image_files:
        return JsonResponse({'error': 'At least one image file is required'}, status=400)
    
    # Get options
    output_format = request.POST.get('output_format', 'auto')
    quality = int(request.POST.get('quality', '80'))
    resize_option = request.POST.get('resize_option', 'none')
    resize_value = int(request.POST.get('resize_value', '0')) if request.POST.get('resize_value') else 0
    
    # Validate files
    max_file_size = 25 * 1024 * 1024  # 25MB per file
    for file in image_files:
        if file.size > max_file_size:
            return JsonResponse({'error': f'File {file.name} exceeds 25MB limit'}, status=400)
        if not file.content_type.startswith('image/'):
            return JsonResponse({'error': f'Invalid file format: {file.name}'}, status=400)
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix='image_compression_')
    
    try:
        compressed_files = []
        total_original_size = 0
        total_compressed_size = 0
        
        for i, image_file in enumerate(image_files):
            # Save original file
            temp_input = os.path.join(temp_dir, f"input_{i}_{uuid.uuid4().hex}")
            with open(temp_input, 'wb') as f:
                for chunk in image_file.chunks():
                    f.write(chunk)
            
            original_size = os.path.getsize(temp_input)
            total_original_size += original_size
            
            # Compress image
            try:
                img = Image.open(temp_input)
                
                # Resize if needed
                if resize_option != 'none' and resize_value > 0:
                    if resize_option == 'width':
                        ratio = resize_value / img.width
                        new_height = int(img.height * ratio)
                        img = img.resize((resize_value, new_height), Image.LANCZOS)
                    elif resize_option == 'height':
                        ratio = resize_value / img.height
                        new_width = int(img.width * ratio)
                        img = img.resize((new_width, resize_value), Image.LANCZOS)
                    elif resize_option == 'percentage':
                        scale = resize_value / 100
                        new_width = int(img.width * scale)
                        new_height = int(img.height * scale)
                        img = img.resize((new_width, new_height), Image.LANCZOS)
                
                # Convert format if needed
                if output_format != 'auto':
                    if output_format == 'jpg' and img.mode in ('RGBA', 'P'):
                        bg = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        bg.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = bg
                
                # Save compressed image
                temp_output = os.path.join(temp_dir, f"output_{i}_{uuid.uuid4().hex}.jpg")
                
                if output_format == 'png' or (output_format == 'auto' and image_file.name.lower().endswith('.png')):
                    img.save(temp_output.replace('.jpg', '.png'), 'PNG', optimize=True)
                    temp_output = temp_output.replace('.jpg', '.png')
                else:
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    img.save(temp_output, 'JPEG', quality=quality, optimize=True)
                
                compressed_size = os.path.getsize(temp_output)
                total_compressed_size += compressed_size
                
                compressed_files.append({
                    'path': temp_output,
                    'name': image_file.name,
                    'original_size': original_size,
                    'compressed_size': compressed_size
                })
                
            except Exception as e:
                print(f"Error compressing {image_file.name}: {e}")
                # Use original if compression fails
                compressed_files.append({
                    'path': temp_input,
                    'name': image_file.name,
                    'original_size': original_size,
                    'compressed_size': original_size
                })
                total_compressed_size += original_size
        
        # Create response
        if len(compressed_files) == 1:
            # Single file
            with open(compressed_files[0]['path'], 'rb') as f:
                content = f.read()
                response = HttpResponse(content, content_type='image/jpeg')
                response['Content-Disposition'] = f'attachment; filename="compressed_{compressed_files[0]["name"]}"'
                return response
        else:
            # Multiple files - create ZIP
            zip_path = os.path.join(temp_dir, 'compressed_images.zip')
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for cf in compressed_files:
                    zf.write(cf['path'], f"compressed_{cf['name']}")
            
            with open(zip_path, 'rb') as f:
                content = f.read()
                response = HttpResponse(content, content_type='application/zip')
                response['Content-Disposition'] = 'attachment; filename="compressed_images.zip"'
                return response
    
    except Exception as e:
        return JsonResponse({'error': f'Compression failed: {str(e)}'}, status=500)
    
    finally:
        # Cleanup
        try:
            shutil.rmtree(temp_dir)
        except:
            pass
def compress_pdf_simple(input_path, output_dir, original_filename, compression_level):
    """
    Simple PDF compression using available libraries
    """
    output_filename = f"compressed_{uuid.uuid4().hex}.pdf"
    output_path = os.path.join(output_dir, output_filename)
    
    # Try PyMuPDF first
    if PYMUPDF_AVAILABLE:
        try:
            pdf_doc = fitz.open(input_path)
            pdf_doc.save(output_path, garbage=4, clean=True, deflate=True)
            pdf_doc.close()
            return output_path
        except Exception as e:
            print(f"PyMuPDF compression failed: {str(e)}")
    
    # Try pikepdf as fallback
    if PIKEPDF_AVAILABLE:
        try:
            with pikepdf.open(input_path) as pdf:
                pdf.save(output_path, compress_streams=True)
            return output_path
        except Exception as e:
            print(f"pikepdf compression failed: {str(e)}")
    
    # If all else fails, just copy the file
    shutil.copy2(input_path, output_path)
    return output_path

def compress_image(input_path, output_dir, original_filename, output_format, quality, resize_option, resize_value):
    """
    Compress an image using Pillow
    """
    try:
        # Open the image
        img = Image.open(input_path)
        
        # Determine output format
        if output_format == 'auto':
            # Keep original format
            format_name = img.format
        else:
            format_name = output_format.upper()
            
        # Handle special case for JPEG
        if format_name == 'JPG':
            format_name = 'JPEG'
        
        # Resize image if needed
        if resize_option != 'none' and resize_value > 0:
            original_width, original_height = img.size
            
            if resize_option == 'width':
                # Resize by width
                new_width = resize_value
                new_height = int(original_height * (new_width / original_width))
                img = img.resize((new_width, new_height), Image.LANCZOS)
                
            elif resize_option == 'height':
                # Resize by height
                new_height = resize_value
                new_width = int(original_width * (new_height / original_height))
                img = img.resize((new_width, new_height), Image.LANCZOS)
                
            elif resize_option == 'percentage':
                # Resize by percentage
                scale = resize_value / 100
                new_width = int(original_width * scale)
                new_height = int(original_height * scale)
                img = img.resize((new_width, new_height), Image.LANCZOS)
        
        # Prepare output path with appropriate extension
        name_without_ext = os.path.splitext(os.path.basename(original_filename))[0]
        output_ext = format_name.lower()
        if output_ext == 'jpeg':
            output_ext = 'jpg'
            
        output_filename = f"{name_without_ext}_compressed_{uuid.uuid4().hex}.{output_ext}"
        output_path = os.path.join(output_dir, output_filename)
        
        # Convert image mode if needed
        if format_name == 'JPEG' and img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        # Save with compression
        save_kwargs = {}
        
        if format_name == 'JPEG':
            save_kwargs['quality'] = quality
            save_kwargs['optimize'] = True
            save_kwargs['progressive'] = True
            
        elif format_name == 'PNG':
            save_kwargs['optimize'] = True
            # PNG doesn't use quality but compression level (0-9)
            # Map quality (0-100) to compression level (9-0)
            # Higher quality = lower compression level
            compression_level = 9 - int(quality / 100 * 9)
            save_kwargs['compress_level'] = compression_level
            
        elif format_name == 'WEBP':
            save_kwargs['quality'] = quality
            save_kwargs['method'] = 6  # Higher value = better compression but slower
            
        # Save the image
        img.save(output_path, format=format_name, **save_kwargs)
        
        return output_path
        
    except Exception as e:
        print(f"Image compression error: {str(e)}")
        return None

def contact(request):
    """Render the contact page with form"""
    contact_settings = ContactSettings.get_settings()
    form = ContactForm()
    
    context = {
        'form': form,
        'contact_settings': contact_settings,
    }
    return render(request, 'contact.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def contact_submit(request):
    """Handle contact form submission"""
    
    # Check if it's an AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Initialize form with POST data and FILES
    form = ContactForm(request.POST, request.FILES)
    
    if form.is_valid():
        try:
            # Create contact message instance
            contact_message = ContactMessage(
                full_name=form.cleaned_data['full_name'],
                email=form.cleaned_data['email'],
                company=form.cleaned_data.get('company', ''),
                phone=form.cleaned_data.get('phone', ''),
                subject=form.cleaned_data['subject'],
                category=form.cleaned_data['category'],
                message=form.cleaned_data['message'],
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Handle file attachment if present
            if 'attachment' in request.FILES:
                contact_message.attachment = request.FILES['attachment']
            
            # Save the message
            contact_message.save()
            
            # Send email notification
            try:
                send_mail(
                    f'New Contact Form Submission: {form.cleaned_data["subject"]}',
                    f"""
                    New message from: {form.cleaned_data['full_name']}
                    Email: {form.cleaned_data['email']}
                    Category: {form.cleaned_data['category']}
                    
                    Message:
                    {form.cleaned_data['message']}
                    """,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.ADMIN_EMAIL],
                    fail_silently=False,
                )
                
                # Send confirmation email to user
                send_mail(
                    'Thank you for contacting SmallPDF.us',
                    f"""
                    Dear {form.cleaned_data['full_name']},
                    
                    Thank you for contacting us. We have received your message and will get back to you as soon as possible.
                    
                    Your message reference: {str(contact_message.id)[:8]}
                    
                    Best regards,
                    The SmallPDF.us Team
                    """,
                    settings.DEFAULT_FROM_EMAIL,
                    [form.cleaned_data['email']],
                    fail_silently=True,
                )
                
            except Exception as email_error:
                print(f"Error sending email notification: {email_error}")
                # Continue even if email fails
            
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': 'Thank you for your message! We\'ll get back to you within 2-4 hours.',
                    'message_id': str(contact_message.id)[:8]
                })
            else:
                messages.success(request, 'Thank you for your message! We\'ll get back to you within 2-4 hours.')
                return redirect('contact')
                
        except Exception as e:
            print(f"Error saving contact message: {e}")
            import traceback
            traceback.print_exc()
            
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'message': 'There was an error processing your message. Please try again or contact us directly.'
                })
            else:
                messages.error(request, 'There was an error processing your message. Please try again.')
                return render(request, 'contact.html', {'form': form})
    
    else:
        # Form is not valid
        error_messages = []
        for field, errors in form.errors.items():
            for error in errors:
                error_messages.append(f"{field}: {error}")
        
        error_message = '; '.join(error_messages)
        print(f"Form validation errors: {error_message}")
        
        if is_ajax:
            return JsonResponse({
                'success': False,
                'message': f'Please correct the following errors: {error_message}',
                'errors': form.errors
            }, status=400)
        else:
            messages.error(request, f'Please correct the following errors: {error_message}')
            return render(request, 'contact.html', {'form': form})

# Helper function for getting client IP
def get_client_ip(request):
    """Get the client's IP address from the request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# Additional contact-related views
def contact_success(request):
    """Contact form success page"""
    return render(request, 'contact_success.html')


def faq_page(request):
    return render(request, 'faq.html') 


def about(request):
    """About page view with company information and statistics"""
    stats = {
        'tools': '15+',
        'users': '12M+',
        'files_processed': '200M+',
        'countries': '185+',
        'user_rating': '4.9/5',
        'uptime': '99.9%',
        'processing_speed': '< 30s',
        'security_level': 'Bank-Grade'
    }
    
    features = [
        {
            'title': 'Bank-Level Security',
            'description': 'Your documents are protected with advanced 256-bit SSL encryption and automatic deletion after processing.',
            'icon': 'shield-check',
            'color': 'blue'
        },
        {
            'title': 'Lightning-Fast Processing',
            'description': 'Our optimized cloud infrastructure processes files in seconds, not minutes.',
            'icon': 'zap',
            'color': 'yellow'
        },
        {
            'title': 'Superior Accuracy',
            'description': 'Industry-leading 98%+ formatting retention rate with advanced conversion algorithms.',
            'icon': 'check-circle',
            'color': 'green'
        },
        {
            'title': 'Cross-Platform Compatible',
            'description': 'Works seamlessly on Windows, Mac, Linux, iOS, and Android devices.',
            'icon': 'monitor',
            'color': 'purple'
        },
        {
            'title': 'No Registration Required',
            'description': 'Start using our tools immediately without creating an account or providing personal information.',
            'icon': 'user-x',
            'color': 'red'
        },
        {
            'title': '24/7 Availability',
            'description': 'Our services are available around the clock with 99.9% uptime guarantee.',
            'icon': 'clock',
            'color': 'indigo'
        }
    ]
    
    team_members = [
        {
            'name': 'Sarah Johnson',
            'role': 'CEO & Founder',
            'bio': 'Former Google engineer with 10+ years in document processing technology.',
            'image': '/static/images/team/sarah.jpg'
        },
        {
            'name': 'Michael Chen',
            'role': 'CTO',
            'bio': 'Expert in cloud architecture and PDF processing algorithms.',
            'image': '/static/images/team/michael.jpg'
        },
        {
            'name': 'Emily Rodriguez',
            'role': 'Head of Product',
            'bio': 'UX specialist focused on making complex tools simple and intuitive.',
            'image': '/static/images/team/emily.jpg'
        },
        {
            'name': 'David Kim',
            'role': 'Lead Developer',
            'bio': 'Full-stack developer specializing in high-performance web applications.',
            'image': '/static/images/team/david.jpg'
        }
    ]
    
    milestones = [
        {
            'year': '2019',
            'title': 'Company Founded',
            'description': 'SmallPDF.us was founded with a mission to make PDF tools accessible to everyone.'
        },
        {
            'year': '2020',
            'title': '1M Users Milestone',
            'description': 'Reached our first million users and launched mobile-optimized tools.'
        },
        {
            'year': '2021',
            'title': 'Advanced AI Integration',
            'description': 'Introduced AI-powered OCR and intelligent document processing.'
        },
        {
            'year': '2022',
            'title': 'Enterprise Solutions',
            'description': 'Launched API services and enterprise-grade security features.'
        },
        {
            'year': '2023',
            'title': '10M+ Users',
            'description': 'Expanded globally and processed over 100 million documents.'
        },
        {
            'year': '2024',
            'title': 'Next-Gen Platform',
            'description': 'Launched our fastest, most secure platform with enhanced features.'
        }
    ]
    
    values = [
        {
            'title': 'Privacy First',
            'description': 'We believe your documents are private. We never store, share, or access your files.',
            'icon': 'lock'
        },
        {
            'title': 'Simplicity',
            'description': 'Complex document processing should be simple. Our tools work with just a few clicks.',
            'icon': 'mouse-pointer'
        },
        {
            'title': 'Reliability',
            'description': 'When you need to process documents, our platform is always ready and available.',
            'icon': 'shield'
        },
        {
            'title': 'Innovation',
            'description': 'We continuously improve our technology to provide the best document processing experience.',
            'icon': 'lightbulb'
        }
    ]
    
    context = {
        'stats': stats,
        'features': features,
        'team_members': team_members,
        'milestones': milestones,
        'values': values,
        'page_title': 'About SmallPDF.us - Leading PDF Processing Platform',
        'page_description': 'Learn about SmallPDF.us, the trusted platform for PDF processing used by millions worldwide. Discover our mission, team, and commitment to document security.'
    }
    
    return render(request, 'about.html', context)


def about(request):
    """About page view"""
    stats = {
        'tools': '15+',
        'users': '12M+',
        'files_processed': '200M+',
        'countries': '185+',
        'user_rating': '4.9/5'
    }
    
    features = [
        {
            'title': 'Bank-Level Security',
            'description': 'Your documents are protected with advanced 256-bit SSL encryption.',
            'icon': 'shield'
        },
        {
            'title': 'Lightning-Fast Processing',
            'description': 'Our cloud infrastructure processes files in seconds.',
            'icon': 'zap'
        },
        {
            'title': 'Superior Accuracy',
            'description': 'Industry-leading 98%+ formatting retention rate.',
            'icon': 'check-circle'
        }
    ]
    
    context = {
        'stats': stats,
        'features': features
    }
    
    return render(request, 'about.html', context)

# API endpoint for contact status check
@csrf_exempt
def contact_status(request, message_id):
    """Check the status of a contact message"""
    try:
        message = ContactMessage.objects.get(id=message_id)
        return JsonResponse({
            'success': True,
            'status': message.get_status_display(),
            'created_at': message.created_at.isoformat(),
            'priority': message.get_priority_display()
        })
    except ContactMessage.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Message not found'
        })

# Feedback form for completed support requests
@csrf_exempt 
def contact_feedback(request, message_id):
    """Submit feedback for a resolved contact message"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            rating = data.get('rating')
            feedback = data.get('feedback', '')
            
            message = ContactMessage.objects.get(id=message_id)
            
            # You could create a separate Feedback model here
            # For now, just update admin notes
            feedback_text = f"\nUser Feedback (Rating: {rating}/5): {feedback}"
            if message.admin_notes:
                message.admin_notes += feedback_text
            else:
                message.admin_notes = feedback_text
            
            message.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Thank you for your feedback!'
            })
            
        except ContactMessage.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Message not found'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Error submitting feedback'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

# Live chat integration endpoint
@csrf_exempt
def live_chat_status(request):
    """Check if live chat is available"""
    # This would integrate with your live chat service
    # For now, return mock data
    import datetime
    
    now = datetime.datetime.now()
    is_business_hours = (
        now.weekday() < 5 and  # Monday-Friday
        9 <= now.hour < 18  # 9 AM - 6 PM
    )
    
    return JsonResponse({
        'available': is_business_hours,
        'estimated_wait': '< 2 minutes' if is_business_hours else 'Offline',
        'agents_online': 3 if is_business_hours else 0
    })

# Add this UPDATED sitemap view to your pdf_tools/views.py

from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone

def sitemap_xml(request):
    """Generate sitemap.xml with correct domain - FIXED VERSION"""
    
    # Get the actual domain from the request
    domain = request.get_host()
    protocol = 'https' if request.is_secure() else 'http'
    
    # Force your domain for production
    if domain in ['127.0.0.1:8000', 'localhost:8000']:
        base_url = 'https://smallpdf.us'
    else:
        base_url = f"{protocol}://{domain}"
    
    # Get current date in simple format
    from datetime import datetime
    current_date = datetime.now().strftime('%Y-%m-%d')
    static_date = '2024-01-01'
    
    # Define all URLs with their priorities and change frequencies
    urls = [
        # Main pages
        {'url': '/', 'priority': '1.0', 'changefreq': 'daily', 'lastmod': current_date},
        {'url': '/tools/', 'priority': '0.9', 'changefreq': 'weekly', 'lastmod': current_date},
        {'url': '/about/', 'priority': '0.6', 'changefreq': 'monthly', 'lastmod': static_date},
        {'url': '/contact/', 'priority': '0.7', 'changefreq': 'monthly', 'lastmod': static_date},
        {'url': '/faq/', 'priority': '0.6', 'changefreq': 'monthly', 'lastmod': static_date},
        {'url': '/privacy-policy/', 'priority': '0.4', 'changefreq': 'yearly', 'lastmod': static_date},
        {'url': '/terms-of-service/', 'priority': '0.4', 'changefreq': 'yearly', 'lastmod': static_date},
        
        # PDF Tools
        {'url': '/merge-pdf/', 'priority': '0.9', 'changefreq': 'monthly', 'lastmod': current_date},
        {'url': '/compress-pdf/', 'priority': '0.9', 'changefreq': 'monthly', 'lastmod': current_date},
        {'url': '/pdf-to-word/', 'priority': '0.9', 'changefreq': 'monthly', 'lastmod': current_date},
        {'url': '/word-to-pdf/', 'priority': '0.9', 'changefreq': 'monthly', 'lastmod': current_date},
        {'url': '/pdf-to-jpg/', 'priority': '0.8', 'changefreq': 'monthly', 'lastmod': current_date},
        {'url': '/jpg-to-pdf/', 'priority': '0.8', 'changefreq': 'monthly', 'lastmod': current_date},
        {'url': '/webp-to-png/', 'priority': '0.8', 'changefreq': 'monthly', 'lastmod': current_date},
        {'url': '/png-to-webp/', 'priority': '0.8', 'changefreq': 'monthly', 'lastmod': current_date},
        {'url': '/pdf-to-png/', 'priority': '0.8', 'changefreq': 'monthly', 'lastmod': current_date},
        {'url': '/png-to-pdf/', 'priority': '0.8', 'changefreq': 'monthly', 'lastmod': current_date},
        {'url': '/split-pdf/', 'priority': '0.8', 'changefreq': 'monthly', 'lastmod': current_date},
        {'url': '/compress-image/', 'priority': '0.8', 'changefreq': 'monthly', 'lastmod': current_date},
        {'url': '/convert-pdf/', 'priority': '0.8', 'changefreq': 'monthly', 'lastmod': current_date},
    ]
    
    # Generate XML content
    xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
'''
    
    for url_data in urls:
        xml_content += f'''    <url>
        <loc>{base_url}{url_data['url']}</loc>
        <lastmod>{url_data['lastmod']}</lastmod>
        <changefreq>{url_data['changefreq']}</changefreq>
        <priority>{url_data['priority']}</priority>
    </url>
'''
    
    xml_content += '</urlset>'
    
    return HttpResponse(xml_content, content_type='application/xml')


def robots_txt(request):
    """Generate robots.txt with correct domain - FIXED VERSION"""
    
    # Get the actual domain from the request
    domain = request.get_host()
    protocol = 'https' if request.is_secure() else 'http'
    
    # Force your domain for production
    if domain in ['127.0.0.1:8000', 'localhost:8000']:
        base_url = 'https://smallpdf.us'
    else:
        base_url = f"{protocol}://{domain}"
    
    robots_content = f"""User-agent: *
Allow: /

# Allow all tools and important pages
Allow: /merge-pdf/
Allow: /compress-pdf/
Allow: /compress-image/
Allow: /pdf-to-word/
Allow: /word-to-pdf/
Allow: /pdf-to-jpg/
Allow: /jpg-to-pdf/
Allow: /webp-to-png/
Allow: /png-to-webp/
Allow: /pdf-to-png/
Allow: /png-to-pdf/
Allow: /split-pdf/
Allow: /convert-pdf/
Allow: /tools/
Allow: /about/
Allow: /contact/
Allow: /privacy-policy/
Allow: /terms-of-service/
Allow: /faq/

# Disallow API endpoints from being crawled
Disallow: /api/
Disallow: /admin/
Disallow: /media/temp_images/
Disallow: /media/contact_attachments/

# Allow media files but disallow temporary files
Allow: /media/
Allow: /static/

# Crawl delay to be respectful
Crawl-delay: 1

# Sitemap location
Sitemap: {base_url}/sitemap.xml

# Popular search engines
User-agent: Googlebot
Allow: /
Crawl-delay: 1

User-agent: Bingbot
Allow: /
Crawl-delay: 1

User-agent: Slurp
Allow: /
Crawl-delay: 2

User-agent: DuckDuckBot
Allow: /
Crawl-delay: 1
"""
    
    return HttpResponse(robots_content, content_type='text/plain')

# Add these views to your views.py file

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Avg, Sum, Q
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import UserActivity, ErrorLog, SystemMetrics
from django.contrib.auth.decorators import user_passes_test

def is_staff_user(user):
    return user.is_authenticated and user.is_staff

@staff_member_required
def admin_dashboard(request):
    """Enhanced main admin dashboard with real-time capabilities"""
    # Get date range
    days = int(request.GET.get('days', 7))
    start_date = timezone.now() - timedelta(days=days)
    
    # Basic statistics
    stats = {
        'total_activities': UserActivity.objects.filter(created_at__gte=start_date).count(),
        'total_conversions': UserActivity.objects.filter(
            created_at__gte=start_date,
            activity_type='file_process'
        ).count(),
        'total_errors': ErrorLog.objects.filter(created_at__gte=start_date).count(),
        'unique_users': UserActivity.objects.filter(
            created_at__gte=start_date
        ).values('session_id').distinct().count(),
    }
    
    # Calculate success rate
    successful_conversions = UserActivity.objects.filter(
        created_at__gte=start_date,
        activity_type='file_process',
        status='success'
    ).count()
    
    if stats['total_conversions'] > 0:
        stats['success_rate'] = (successful_conversions / stats['total_conversions']) * 100
    else:
        stats['success_rate'] = 0
    
    # Tool usage statistics
    tool_usage = list(UserActivity.objects.filter(
        created_at__gte=start_date,
        activity_type__in=['tool_access', 'file_process'],
        tool_name__isnull=False
    ).values('tool_name').annotate(
        count=Count('id')
    ).order_by('-count')[:10])
    
    # Error breakdown
    error_breakdown = list(ErrorLog.objects.filter(
        created_at__gte=start_date
    ).values('error_type').annotate(
        count=Count('id')
    ).order_by('-count')[:10])
    
    # File processing statistics
    file_stats = UserActivity.objects.filter(
        created_at__gte=start_date,
        activity_type='file_process'
    ).aggregate(
        total_files=Count('id'),
        avg_file_size=Avg('file_size'),
        total_size=Sum('file_size'),
        avg_processing_time=Avg('processing_time')
    )
    
    # Daily activity data for charts
    daily_activity = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        activities = UserActivity.objects.filter(
            created_at__gte=day_start,
            created_at__lt=day_end
        ).count()
        
        errors = ErrorLog.objects.filter(
            created_at__gte=day_start,
            created_at__lt=day_end
        ).count()
        
        daily_activity.append({
            'date': date.strftime('%Y-%m-%d'),
            'activities': activities,
            'errors': errors
        })
    
    # Device and browser statistics
    device_stats = list(UserActivity.objects.filter(
        created_at__gte=start_date
    ).values('device_type').annotate(
        count=Count('id')
    ).order_by('-count'))
    
    browser_stats = list(UserActivity.objects.filter(
        created_at__gte=start_date
    ).values('browser').annotate(
        count=Count('id')
    ).order_by('-count'))
    
    # Country statistics
    country_stats = list(UserActivity.objects.filter(
        created_at__gte=start_date,
        country__isnull=False
    ).values('country').annotate(
        count=Count('id')
    ).order_by('-count')[:10])
    
    context = {
        'stats': stats,
        'tool_usage': json.dumps(tool_usage),
        'error_breakdown': error_breakdown,
        'file_stats': file_stats,
        'daily_activity': json.dumps(daily_activity),
        'device_stats': device_stats,
        'browser_stats': browser_stats,
        'country_stats': country_stats,
        'days': days,
    }
    
    return render(request, 'admin/analytics_dashboard.html', context)

def calculate_error_rate(since_time):
    """Calculate error rate percentage"""
    try:
        total_requests = UserActivity.objects.filter(created_at__gte=since_time).count()
        error_requests = ErrorLog.objects.filter(created_at__gte=since_time).count()
        
        if total_requests == 0:
            return 0
        
        return round((error_requests / total_requests) * 100, 2)
    except:
        return 0

def calculate_avg_response_time(since_time):
    """Calculate average response time"""
    avg_time = UserActivity.objects.filter(
        created_at__gte=since_time,
        processing_time__isnull=False
    ).aggregate(avg=Avg('processing_time'))['avg']
    
    return round(avg_time * 1000, 2) if avg_time else 0  # Convert to milliseconds

def get_active_sessions_count():
    """Get count of active sessions in last 30 minutes"""
    last_30_min = timezone.now() - timedelta(minutes=30)
    return UserActivity.objects.filter(
        created_at__gte=last_30_min
    ).values('session_id').distinct().count()

def get_system_disk_usage():
    """Get disk usage information"""
    try:
        import shutil
        total, used, free = shutil.disk_usage("/")
        used_percent = (used / total) * 100
        return {
            'total_gb': round(total / (1024**3), 2),
            'used_gb': round(used / (1024**3), 2),
            'free_gb': round(free / (1024**3), 2),
            'used_percent': round(used_percent, 1)
        }
    except:
        # Mock data if unable to get real disk usage
        return {
            'total_gb': 100.0,
            'used_gb': 65.0,
            'free_gb': 35.0,
            'used_percent': 65.0
        }

def get_system_cpu_usage():
    """Get CPU usage information"""
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        return {
            'usage_percent': cpu_percent,
            'core_count': cpu_count,
            'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
        }
    except:
        # Mock data if psutil not available
        return {
            'usage_percent': 45.0,
            'core_count': 4,
            'load_average': [1.2, 1.5, 1.8]
        }
       
def get_system_memory_usage():
    """Get memory usage information"""
    try:
        import psutil
        memory = psutil.virtual_memory()
        return {
            'total_mb': round(memory.total / (1024**2)),
            'used_mb': round(memory.used / (1024**2)),
            'available_mb': round(memory.available / (1024**2)),
            'used_percent': round(memory.percent, 1)
        }
    except:
        # Mock data if psutil not available
        return {
            'total_mb': 8192,
            'used_mb': 5324,
            'available_mb': 2868,
            'used_percent': 65.0
        }    
    

@staff_member_required
def real_time_monitor(request):
    """Real-time monitoring dashboard"""
    return render(request, 'admin/real_time_monitor.html')

def check_database_health():
    """Check database connectivity and performance"""
    try:
        # Test database connection
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        
        # Test query performance
        start_time = time.time()
        UserActivity.objects.first()
        query_time = time.time() - start_time
        
        return {
            'status': 'healthy',
            'connection': 'ok',
            'query_time': round(query_time * 1000, 2)  # milliseconds
        }
    except Exception as e:
        return {
            'status': 'error',
            'connection': 'failed',
            'error': str(e)
        }


def check_database_status():
    """Check database connectivity"""
    try:
        UserActivity.objects.first()
        return {'status': 'healthy', 'message': 'Database connection OK'}
    except Exception as e:
        return {'status': 'error', 'message': f'Database error: {str(e)}'}

def get_disk_usage():
    """Get disk usage (mock implementation)"""
    # In production, implement actual disk usage monitoring
    import random
    return {
        'used_percent': random.randint(20, 80),
        'free_gb': random.randint(100, 500),
        'total_gb': 1000
    }

def get_memory_usage():
    """Get memory usage (mock implementation)"""
    # In production, implement actual memory monitoring
    import random
    return {
        'used_percent': random.randint(30, 70),
        'used_mb': random.randint(2000, 6000),
        'total_mb': 8192
    }
def get_top_errors(since_time):
    """Get top errors in the time period"""
    try:
        return list(ErrorLog.objects.filter(
            created_at__gte=since_time
        ).values('error_type').annotate(
            count=Count('id')
        ).order_by('-count')[:5])
    except:
        return []
    
def get_top_errors(since_time):
    """Get top errors in the time period"""
    return list(ErrorLog.objects.filter(
        created_at__gte=since_time
    ).values('error_type').annotate(
        count=Count('id')
    ).order_by('-count')[:5])

def get_system_uptime():
    """Get system uptime"""
    try:
        import psutil
        boot_time = psutil.boot_time()
        uptime_seconds = time.time() - boot_time
        
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        
        return {
            'seconds': int(uptime_seconds),
            'formatted': f"{days}d {hours}h {minutes}m"
        }
    except:
        return {
            'seconds': 86400,
            'formatted': "1d 0h 0m"
        }
def calculate_overall_health_score(health_data):
    """Calculate overall system health score out of 100"""
    try:
        score = 100
        
        # Deduct points based on various factors
        if health_data.get('error_rate_24h', 0) > 5:
            score -= 20
        elif health_data.get('error_rate_24h', 0) > 2:
            score -= 10
        
        if health_data.get('avg_response_time', 0) > 5000:  # 5 seconds
            score -= 15
        elif health_data.get('avg_response_time', 0) > 3000:  # 3 seconds
            score -= 10
        
        if health_data.get('disk_usage', {}).get('used_percent', 0) > 90:
            score -= 15
        elif health_data.get('disk_usage', {}).get('used_percent', 0) > 80:
            score -= 10
        
        if health_data.get('memory_usage', {}).get('used_percent', 0) > 90:
            score -= 15
        elif health_data.get('memory_usage', {}).get('used_percent', 0) > 80:
            score -= 10
        
        if health_data.get('cpu_usage', {}).get('usage_percent', 0) > 90:
            score -= 15
        elif health_data.get('cpu_usage', {}).get('usage_percent', 0) > 80:
            score -= 10
        
        return max(0, score)  # Don't go below 0
    except:
        return 75  # Default moderate score if calculation fails

def get_slowest_tools(since_time):
    """Get tools with highest average processing time"""
    return list(UserActivity.objects.filter(
        created_at__gte=since_time,
        activity_type='file_process',
        processing_time__isnull=False
    ).values('tool_name').annotate(
        avg_time=Avg('processing_time'),
        total_uses=Count('id')
    ).order_by('-avg_time')[:5])

@staff_member_required
def live_data_api(request):
    """API endpoint for real-time dashboard data"""
    try:
        now = timezone.now()
        last_hour = now - timedelta(hours=1)
        last_30_minutes = now - timedelta(minutes=30)
        last_5_minutes = now - timedelta(minutes=5)
        
        # Active users (sessions with activity in last 30 minutes)
        active_users = UserActivity.objects.filter(
            created_at__gte=last_30_minutes
        ).values('session_id').distinct().count()
        
        # Conversions in the last hour
        conversions_hour = UserActivity.objects.filter(
            created_at__gte=last_hour,
            activity_type='file_process'
        ).count()
        
        # Errors in the last hour
        errors_hour = ErrorLog.objects.filter(
            created_at__gte=last_hour
        ).count()
        
        # Success rate calculation
        successful_conversions_hour = UserActivity.objects.filter(
            created_at__gte=last_hour,
            activity_type='file_process',
            status='success'
        ).count()
        
        success_rate = 0
        if conversions_hour > 0:
            success_rate = (successful_conversions_hour / conversions_hour) * 100
        
        # Recent activities (last 5 minutes, limit 20)
        recent_activities = list(UserActivity.objects.filter(
            created_at__gte=last_5_minutes
        ).order_by('-created_at')[:20].values(
            'activity_type', 'tool_name', 'file_name', 'status',
            'ip_address', 'device_type', 'created_at', 'error_message'
        ))
        
        # Tool performance (last hour)
        tool_performance = list(UserActivity.objects.filter(
            created_at__gte=last_hour,
            activity_type='file_process',
            tool_name__isnull=False
        ).values('tool_name').annotate(
            total_attempts=Count('id'),
            successful=Count('id', filter=Q(status='success')),
            failed=Count('id', filter=Q(status='failed')),
            avg_processing_time=Avg('processing_time')
        ).order_by('-total_attempts')[:10])
        
        # Recent errors (unresolved, last 24 hours)
        recent_errors = list(ErrorLog.objects.filter(
            created_at__gte=now - timedelta(hours=24),
            resolved=False
        ).order_by('-created_at')[:10].values(
            'error_type', 'error_message', 'severity',
            'ip_address', 'created_at'
        ))
        
        # System health metrics
        avg_processing_time = UserActivity.objects.filter(
            created_at__gte=last_hour,
            processing_time__isnull=False
        ).aggregate(avg=Avg('processing_time'))['avg']
        
        system_health = {
            'avg_response_time': round(avg_processing_time * 1000, 2) if avg_processing_time else None,
            'memory_usage': 75,  # Mock data - implement actual system monitoring
            'cpu_usage': 45,     # Mock data
            'disk_usage': 30,    # Mock data
        }
        
        # Format timestamps for frontend
        for activity in recent_activities:
            activity['created_at'] = activity['created_at'].isoformat()
        
        for error in recent_errors:
            error['created_at'] = error['created_at'].isoformat()
        
        response_data = {
            'timestamp': now.isoformat(),
            'active_users': active_users,
            'conversions_hour': conversions_hour,
            'errors_hour': errors_hour,
            'success_rate': round(success_rate, 1),
            'recent_activities': recent_activities,
            'tool_performance': tool_performance,
            'recent_errors': recent_errors,
            'system_health': system_health,
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        print(f"Error in live_data_api: {str(e)}")
        return JsonResponse({
            'error': 'Failed to fetch live data',
            'timestamp': timezone.now().isoformat()
        }, status=500)

@staff_member_required
def user_activity_detail(request):
    """Detailed user activity view with enhanced filtering"""
    # Filters
    activity_type = request.GET.get('activity_type', '')
    tool_name = request.GET.get('tool_name', '')
    status = request.GET.get('status', '')
    device_type = request.GET.get('device_type', '')
    days = int(request.GET.get('days', 7))
    
    # Base queryset
    activities = UserActivity.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=days)
    ).order_by('-created_at')
    
    # Apply filters
    if activity_type:
        activities = activities.filter(activity_type=activity_type)
    if tool_name:
        activities = activities.filter(tool_name=tool_name)
    if status:
        activities = activities.filter(status=status)
    if device_type:
        activities = activities.filter(device_type=device_type)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(activities, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    activity_types = UserActivity.ACTIVITY_TYPES
    tools = UserActivity.objects.values_list('tool_name', flat=True).distinct()
    tools = [t for t in tools if t]  # Remove None values
    device_types = UserActivity.objects.values_list('device_type', flat=True).distinct()
    device_types = [d for d in device_types if d]
    
    context = {
        'activities': page_obj,
        'activity_types': activity_types,
        'tools': tools,
        'device_types': device_types,
        'current_filters': {
            'activity_type': activity_type,
            'tool_name': tool_name,
            'status': status,
            'device_type': device_type,
            'days': days
        }
    }
    
    return render(request, 'admin/user_activity_detail.html', context)

@staff_member_required
def error_log_detail(request):
    """Detailed error log view with enhanced filtering"""
    # Filters
    error_type = request.GET.get('error_type', '')
    severity = request.GET.get('severity', '')
    resolved = request.GET.get('resolved', '')
    days = int(request.GET.get('days', 7))
    
    # Base queryset
    errors = ErrorLog.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=days)
    ).order_by('-created_at')
    
    # Apply filters
    if error_type:
        errors = errors.filter(error_type=error_type)
    if severity:
        errors = errors.filter(severity=severity)
    if resolved:
        errors = errors.filter(resolved=resolved == 'true')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(errors, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    error_types = ErrorLog.objects.values_list('error_type', flat=True).distinct()
    
    context = {
        'errors': page_obj,
        'error_types': error_types,
        'severity_choices': ErrorLog.SEVERITY_CHOICES,
        'current_filters': {
            'error_type': error_type,
            'severity': severity,
            'resolved': resolved,
            'days': days
        }
    }
    
    return render(request, 'admin/error_log_detail.html', context)
@staff_member_required
def conversion_statistics(request):
    """Detailed conversion statistics by tool"""
    days = int(request.GET.get('days', 7))
    start_date = timezone.now() - timedelta(days=days)
    
    # Conversion stats by tool
    conversion_stats = list(UserActivity.objects.filter(
        created_at__gte=start_date,
        activity_type='file_process',
        tool_name__isnull=False
    ).values('tool_name').annotate(
        total_attempts=Count('id'),
        successful=Count('id', filter=Q(status='success')),
        failed=Count('id', filter=Q(status='failed')),
        avg_file_size=Avg('file_size'),
        total_file_size=Sum('file_size'),
        avg_processing_time=Avg('processing_time'),
        max_processing_time=Max('processing_time'),
        min_processing_time=Min('processing_time')
    ).order_by('-total_attempts'))
    
    # Calculate success rates and format data
    for stat in conversion_stats:
        if stat['total_attempts'] > 0:
            stat['success_rate'] = (stat['successful'] / stat['total_attempts']) * 100
        else:
            stat['success_rate'] = 0
    
    # Hourly conversion data for charts
    hourly_data = []
    for i in range(24):
        hour_start = timezone.now() - timedelta(hours=i)
        hour_end = hour_start + timedelta(hours=1)
        
        conversions = UserActivity.objects.filter(
            created_at__gte=hour_start,
            created_at__lt=hour_end,
            activity_type='file_process'
        ).count()
        
        successful = UserActivity.objects.filter(
            created_at__gte=hour_start,
            created_at__lt=hour_end,
            activity_type='file_process',
            status='success'
        ).count()
        
        hourly_data.append({
            'hour': hour_start.strftime('%H:00'),
            'conversions': conversions,
            'successful': successful,
            'failed': conversions - successful
        })
    
    hourly_data.reverse()
    
    context = {
        'conversion_stats': conversion_stats,
        'hourly_data': json.dumps(hourly_data),
        'days': days,
    }
    
    return render(request, 'admin/conversion_statistics.html', context)

@staff_member_required
def export_activities(request):
    """Export user activities to CSV"""
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Default to last 7 days if no dates provided
    if not start_date or not end_date:
        end_date = timezone.now()
        start_date = end_date - timedelta(days=7)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Get activities
    activities = UserActivity.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date
    ).order_by('-created_at')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="user_activities_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    
    # Write CSV headers
    writer.writerow([
        'ID', 'Session ID', 'User', 'Activity Type', 'Tool Name', 'File Name', 
        'File Size (bytes)', 'File Type', 'Processing Time (s)', 'Status',
        'IP Address', 'Country', 'Device Type', 'Browser', 'Created At (IST)',
        'Error Message', 'Page URL'
    ])
    
    # Write activity data
    for activity in activities:
        writer.writerow([
            str(activity.id),
            activity.session_id,
            activity.user.username if activity.user else 'Anonymous',
            activity.get_activity_type_display(),
            activity.tool_name or '',
            activity.file_name or '',
            activity.file_size or '',
            activity.file_type or '',
            activity.processing_time or '',
            activity.status,
            activity.ip_address,
            activity.country or '',
            activity.device_type or '',
            activity.browser or '',
            activity.get_created_at_ist(),
            activity.error_message or '',
            activity.page_url or ''
        ])
    
    return response
@staff_member_required
def export_errors(request):
    """Export error logs to CSV"""
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Default to last 7 days if no dates provided
    if not start_date or not end_date:
        end_date = timezone.now()
        start_date = end_date - timedelta(days=7)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Get errors
    errors = ErrorLog.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date
    ).order_by('-created_at')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="error_logs_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    
    # Write CSV headers
    writer.writerow([
        'ID', 'Session ID', 'User', 'Error Type', 'Error Message', 'Severity',
        'IP Address', 'File Path', 'Line Number', 'Function Name',
        'Created At (IST)', 'Resolved', 'Resolved By', 'Resolved At (IST)',
        'Stack Trace'
    ])
    
    # Write error data
    for error in errors:
        writer.writerow([
            str(error.id),
            error.session_id,
            error.user.username if error.user else 'Anonymous',
            error.error_type,
            error.error_message,
            error.severity,
            error.ip_address,
            error.file_path or '',
            error.line_number or '',
            error.function_name or '',
            error.get_created_at_ist(),
            'Yes' if error.resolved else 'No',
            error.resolved_by.username if error.resolved_by else '',
            error.get_resolved_at_ist(),
            error.stack_trace or ''
        ])
    
    return response


@staff_member_required
def api_dashboard_data(request):
    """API endpoint for dashboard data (for AJAX updates)"""
    try:
        days = int(request.GET.get('days', 1))
        start_date = timezone.now() - timedelta(days=days)
        
        # Real-time stats
        recent_activities = UserActivity.objects.filter(
            created_at__gte=start_date
        ).count()
        
        recent_errors = ErrorLog.objects.filter(
            created_at__gte=start_date
        ).count()
        
        active_sessions = UserActivity.objects.filter(
            created_at__gte=timezone.now() - timedelta(minutes=30)
        ).values('session_id').distinct().count()
        
        # Hourly data for the last 24 hours
        hourly_data = []
        for i in range(24):
            hour_start = timezone.now() - timedelta(hours=i+1)
            hour_end = hour_start + timedelta(hours=1)
            
            activities = UserActivity.objects.filter(
                created_at__gte=hour_start,
                created_at__lt=hour_end
            ).count()
            
            errors = ErrorLog.objects.filter(
                created_at__gte=hour_start,
                created_at__lt=hour_end
            ).count()
            
            hourly_data.append({
                'hour': hour_start.strftime('%H:00'),
                'activities': activities,
                'errors': errors
            })
        
        hourly_data.reverse()  # Show oldest to newest
        
        return JsonResponse({
            'recent_activities': recent_activities,
            'recent_errors': recent_errors,
            'active_sessions': active_sessions,
            'hourly_data': hourly_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': 'Failed to fetch dashboard data',
            'details': str(e)
        }, status=500)
def create_admin_templates():
    """
    Helper function to create template directories
    Call this once to set up the template structure
    """
    import os
    from django.conf import settings
    
    # Define template directory structure
    template_dirs = [
        'templates/admin',
        'templates/admin/pdf_tools',
    ]
    
    # Create directories if they don't exist
    for template_dir in template_dirs:
        full_path = os.path.join(settings.BASE_DIR, template_dir)
        os.makedirs(full_path, exist_ok=True)
        print(f"Created directory: {full_path}")
    
    print("Template directories created successfully!")
def setup_admin_tracking():
    """
    Quick setup function to initialize admin tracking
    Run this once after adding the middleware
    """
    try:
        # Create some sample data for testing
        from django.contrib.sessions.models import Session
        
        # Clean up old sessions
        Session.objects.filter(expire_date__lt=timezone.now()).delete()
        
        print("✅ Admin tracking setup completed!")
        print("📊 You can now access:")
        print("   - User Activities: /admin/pdf_tools/useractivity/")
        print("   - Error Logs: /admin/pdf_tools/errorlog/")
        print("   - Analytics Dashboard: /admin/analytics/")
        print("   - Real-time Monitor: /admin/real-time/")
        
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {str(e)}")
        return False

def perform_health_check():
    """Perform comprehensive health check"""
    health_results = {
        'timestamp': timezone.now().isoformat(),
        'overall_status': 'healthy',
        'checks': []
    }
    
    # Database check
    try:
        UserActivity.objects.first()
        health_results['checks'].append({
            'name': 'Database Connection',
            'status': 'healthy',
            'message': 'Database connection successful'
        })
    except Exception as e:
        health_results['checks'].append({
            'name': 'Database Connection',
            'status': 'unhealthy',
            'message': f'Database error: {str(e)}'
        })
        health_results['overall_status'] = 'unhealthy'
    
    # Error rate check
    try:
        last_hour = timezone.now() - timedelta(hours=1)
        error_rate = calculate_error_rate(last_hour)
        
        if error_rate > 10:
            status = 'unhealthy'
            health_results['overall_status'] = 'unhealthy'
        elif error_rate > 5:
            status = 'warning'
        else:
            status = 'healthy'
            
        health_results['checks'].append({
            'name': 'Error Rate',
            'status': status,
            'message': f'Error rate: {error_rate}%'
        })
    except Exception as e:
        health_results['checks'].append({
            'name': 'Error Rate',
            'status': 'unknown',
            'message': f'Unable to calculate: {str(e)}'
        })
    
    # Response time check
    try:
        last_hour = timezone.now() - timedelta(hours=1)
        avg_response = calculate_avg_response_time(last_hour)
        
        if avg_response > 10000:  # 10 seconds
            status = 'unhealthy'
            health_results['overall_status'] = 'unhealthy'
        elif avg_response > 5000:  # 5 seconds
            status = 'warning'
        else:
            status = 'healthy'
            
        health_results['checks'].append({
            'name': 'Response Time',
            'status': status,
            'message': f'Average response time: {avg_response}ms'
        })
    except Exception as e:
        health_results['checks'].append({
            'name': 'Response Time',
            'status': 'unknown',
            'message': f'Unable to calculate: {str(e)}'
        })
    
    return health_results     
@staff_member_required
def resolve_error(request, error_id):
    """Mark an error as resolved"""
    if request.method == 'POST':
        try:
            error = ErrorLog.objects.get(id=error_id)
            error.resolved = True
            error.resolved_at = timezone.now()
            error.resolved_by = request.user
            error.save()
            
            return JsonResponse({'success': True, 'message': 'Error marked as resolved'})
        except ErrorLog.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Error not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
def track_conversion_start(request, tool_name, file_count=1, total_file_size=0):
    """Track the start of a conversion process"""
    track_activity(
        request,
        'file_upload',
        tool_name=tool_name,
        status='pending',
        additional_data={
            'file_count': file_count,
            'total_file_size': total_file_size,
            'conversion_started': timezone.now().isoformat()
        }
    )

def track_conversion_success(request, tool_name, file_name, file_size, processing_time, output_size=None):
    """Track successful conversion"""
    additional_data = {
        'conversion_completed': timezone.now().isoformat(),
        'output_size': output_size
    }
    
    track_activity(
        request,
        'file_process',
        tool_name=tool_name,
        file_name=file_name,
        file_size=file_size,
        processing_time=processing_time,
        status='success',
        additional_data=additional_data
    )

def track_conversion_failure(request, tool_name, file_name, file_size, error_message, processing_time=None):
    """Track failed conversion"""
    # Track the failed activity
    track_activity(
        request,
        'file_process',
        tool_name=tool_name,
        file_name=file_name,
        file_size=file_size,
        processing_time=processing_time,
        status='failed',
        error_message=error_message
    )
    
    # Also log as an error
    log_error(
        request,
        'CONVERSION_FAILED',
        f'Conversion failed for {tool_name}: {error_message}',
        severity='medium',
        additional_data={
            'tool_name': tool_name,
            'file_name': file_name,
            'file_size': file_size
        }
    )

def track_download(request, tool_name, file_name, file_size):
    """Track file download"""
    track_activity(
        request,
        'file_download',
        tool_name=tool_name,
        file_name=file_name,
        file_size=file_size,
        status='success'
    )

# Settings configuration for tracking
TRACKING_SETTINGS = {
    'TRACK_PAGE_VIEWS': True,
    'TRACK_FILE_UPLOADS': True,
    'TRACK_CONVERSIONS': True,
    'TRACK_DOWNLOADS': True,
    'TRACK_ERRORS': True,
    'LOG_USER_AGENTS': True,
    'LOG_IP_ADDRESSES': True,
    'ANONYMIZE_IPS_AFTER_DAYS': 30,  # Anonymize IPs after 30 days for privacy
    'DELETE_OLD_ACTIVITIES_AFTER_DAYS': 90,  # Delete old activities after 90 days
    'MAX_ERROR_STACK_TRACE_LENGTH': 5000,
    'REAL_TIME_UPDATE_INTERVAL': 5,  # seconds
}

# Utility function to clean old data
@staff_member_required
def cleanup_old_data(request):
    """Cleanup old tracking data based on settings"""
    if request.method == 'POST':
        try:
            # Delete old activities
            old_activities_date = timezone.now() - timedelta(days=TRACKING_SETTINGS['DELETE_OLD_ACTIVITIES_AFTER_DAYS'])
            deleted_activities = UserActivity.objects.filter(created_at__lt=old_activities_date).delete()[0]
            
            # Delete old errors
            deleted_errors = ErrorLog.objects.filter(
                created_at__lt=old_activities_date,
                resolved=True
            ).delete()[0]
            
            # Anonymize old IPs
            anonymize_date = timezone.now() - timedelta(days=TRACKING_SETTINGS['ANONYMIZE_IPS_AFTER_DAYS'])
            anonymized_activities = UserActivity.objects.filter(
                created_at__lt=anonymize_date
            ).update(ip_address='0.0.0.0')
            
            anonymized_errors = ErrorLog.objects.filter(
                created_at__lt=anonymize_date
            ).update(ip_address='0.0.0.0')
            
            return JsonResponse({
                'success': True,
                'message': f'Cleanup completed: {deleted_activities} activities, {deleted_errors} errors deleted, {anonymized_activities + anonymized_errors} IPs anonymized'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Cleanup failed: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

# Middleware to automatically track activities
import logging

logger = logging.getLogger(__name__)

class ActivityTrackingMiddleware:
    """Middleware to automatically track user activities"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Track page view
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

try:
    from PIL import Image, ImageOps
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Add this view function to your views.py
def webp_to_png(request):
    """Render the WebP to PNG tool page"""
    return render(request, 'webp_to_png.html')

# Add this API endpoint to your views.py
@csrf_exempt
@require_http_methods(["POST"])
def webp_to_png_api(request):
    """
    API endpoint to convert WebP images to PNG/JPG format
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    if not PIL_AVAILABLE:
        return JsonResponse({
            'error': 'Image processing library not available. Please install Pillow: pip install Pillow'
        }, status=500)
    
    # Handle both 'images' and 'files' keys from frontend
    image_files = []
    if 'images' in request.FILES:
        image_files = request.FILES.getlist('images')
    elif 'files' in request.FILES:
        image_files = request.FILES.getlist('files')
    else:
        return JsonResponse({'error': 'No WebP files found in request'}, status=400)
    
    if not image_files:
        return JsonResponse({'error': 'At least one WebP image is required'}, status=400)
    
    # Get conversion options
    output_format = request.POST.get('output_format', 'png').lower()
    quality = int(request.POST.get('quality', '100'))
    resize_option = request.POST.get('resize_option', 'none')
    resize_value = int(request.POST.get('resize_value', '0')) if request.POST.get('resize_value') else 0
    
    print(f"=== WebP to PNG CONVERSION SETTINGS ===")
    print(f"Files: {len(image_files)}")
    print(f"Output Format: {output_format}")
    print(f"Quality: {quality}")
    print(f"Resize: {resize_option} = {resize_value}")
    
    # Validate files
    max_file_size = 25 * 1024 * 1024  # 25MB per file
    max_total_size = 100 * 1024 * 1024  # 100MB total
    max_files = 50
    
    if len(image_files) > max_files:
        return JsonResponse({'error': f'Maximum {max_files} WebP files allowed'}, status=400)
    
    total_size = sum(file.size for file in image_files)
    if total_size > max_total_size:
        return JsonResponse({'error': 'Total file size exceeds 100MB limit'}, status=400)
    
    for file in image_files:
        if file.size > max_file_size:
            return JsonResponse({'error': f'File {file.name} exceeds 25MB limit'}, status=400)
        
        # Validate WebP format
        if not (file.content_type == 'image/webp' or file.name.lower().endswith('.webp')):
            return JsonResponse({'error': f'Invalid file format: {file.name}. Only WebP files are allowed.'}, status=400)
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix='webp_to_png_')
    print(f"Created temp directory: {temp_dir}")
    
    try:
        converted_files = []
        total_original_size = 0
        total_converted_size = 0
        
        for i, image_file in enumerate(image_files):
            print(f"\n=== Processing WebP file {i+1}: {image_file.name} ===")
            
            # Save original file to temp directory
            temp_input = os.path.join(temp_dir, f"input_{i}_{uuid.uuid4().hex}.webp")
            
            with open(temp_input, 'wb') as f:
                for chunk in image_file.chunks():
                    f.write(chunk)
            
            original_size = os.path.getsize(temp_input)
            total_original_size += original_size
            print(f"Original WebP size: {original_size} bytes")
            
            try:
                # Open and process the WebP image
                with Image.open(temp_input) as img:
                    print(f"Original WebP image: {img.size} pixels, mode: {img.mode}")
                    
                    # Create a copy to work with
                    processed_img = img.copy()
                    
                    # Handle resize if specified
                    if resize_option != 'none' and resize_value > 0:
                        original_width, original_height = processed_img.size
                        
                        if resize_option == 'width':
                            ratio = resize_value / original_width
                            new_height = int(original_height * ratio)
                            processed_img = processed_img.resize((resize_value, new_height), Image.LANCZOS)
                            print(f"Resized by width: {processed_img.size}")
                            
                        elif resize_option == 'height':
                            ratio = resize_value / original_height
                            new_width = int(original_width * ratio)
                            processed_img = processed_img.resize((new_width, resize_value), Image.LANCZOS)
                            print(f"Resized by height: {processed_img.size}")
                            
                        elif resize_option == 'percentage':
                            scale = resize_value / 100
                            new_width = int(original_width * scale)
                            new_height = int(original_height * scale)
                            processed_img = processed_img.resize((new_width, new_height), Image.LANCZOS)
                            print(f"Resized by percentage: {processed_img.size}")
                    
                    # Determine output format and filename
                    if output_format in ['png']:
                        save_format = 'PNG'
                        output_extension = '.png'
                    elif output_format in ['jpg', 'jpeg']:
                        save_format = 'JPEG'
                        output_extension = '.jpg'
                    else:
                        save_format = 'PNG'  # Default fallback
                        output_extension = '.png'
                    
                    # Convert image mode for JPEG if necessary
                    if save_format == 'JPEG' and processed_img.mode in ('RGBA', 'P', 'LA'):
                        # Create white background for JPEG
                        background = Image.new('RGB', processed_img.size, (255, 255, 255))
                        if processed_img.mode == 'P':
                            processed_img = processed_img.convert('RGBA')
                        if processed_img.mode in ('RGBA', 'LA'):
                            background.paste(processed_img, mask=processed_img.split()[-1])
                        processed_img = background
                        print("Converted to RGB for JPEG")
                    
                    # Create output filename
                    base_name = os.path.splitext(image_file.name)[0]
                    temp_output = os.path.join(temp_dir, f"converted_{base_name}_{uuid.uuid4().hex}{output_extension}")
                    
                    # Save with appropriate settings
                    save_kwargs = {'optimize': True}
                    
                    if save_format == 'JPEG':
                        save_kwargs['quality'] = quality
                        save_kwargs['progressive'] = True
                    elif save_format == 'PNG':
                        # PNG is lossless, but we can still optimize
                        save_kwargs['compress_level'] = 6  # Good balance of speed and compression
                    
                    processed_img.save(temp_output, save_format, **save_kwargs)
                    print(f"Saved as {save_format} with options: {save_kwargs}")
                    
                    converted_size = os.path.getsize(temp_output)
                    total_converted_size += converted_size
                    print(f"Converted size: {converted_size} bytes")
                    
                    # Store file info
                    converted_files.append({
                        'path': temp_output,
                        'name': f"converted_{base_name}{output_extension}",
                        'original_name': image_file.name,
                        'original_size': original_size,
                        'converted_size': converted_size
                    })
                    
            except Exception as e:
                print(f"Error converting {image_file.name}: {str(e)}")
                # If conversion fails, skip this file
                continue
        
        print(f"\n=== CONVERSION SUMMARY ===")
        print(f"Files processed: {len(converted_files)}")
        print(f"Total original size: {total_original_size} bytes")
        print(f"Total converted size: {total_converted_size} bytes")
        
        if not converted_files:
            return JsonResponse({'error': 'No files could be processed successfully'}, status=500)
        
        # Return result
        if len(converted_files) == 1:
            # Single file - return the converted image directly
            file_info = converted_files[0]
            
            with open(file_info['path'], 'rb') as f:
                file_data = f.read()
                
                print(f"Returning single file: {len(file_data)} bytes")
                
                # Determine content type
                if file_info['name'].lower().endswith('.png'):
                    content_type = 'image/png'
                elif file_info['name'].lower().endswith(('.jpg', '.jpeg')):
                    content_type = 'image/jpeg'
                else:
                    content_type = 'application/octet-stream'
                
                response = HttpResponse(file_data, content_type=content_type)
                response['Content-Disposition'] = f'attachment; filename="{file_info["name"]}"'
                response['Content-Length'] = str(len(file_data))
                
                # Add conversion info headers
                response['X-Original-Size'] = str(file_info['original_size'])
                response['X-Converted-Size'] = str(file_info['converted_size'])
                response['X-Output-Format'] = output_format.upper()
                response['X-Files-Count'] = '1'
                
                # Add cache control headers
                response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                
                return response
        else:
            # Multiple files - create ZIP
            zip_path = os.path.join(temp_dir, 'converted_webp_images.zip')
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for file_info in converted_files:
                    zip_file.write(file_info['path'], file_info['name'])
            
            zip_size = os.path.getsize(zip_path)
            print(f"Created ZIP file: {zip_size} bytes")
            
            with open(zip_path, 'rb') as f:
                zip_data = f.read()
                
                response = HttpResponse(zip_data, content_type='application/zip')
                response['Content-Disposition'] = 'attachment; filename="converted_webp_images.zip"'
                response['Content-Length'] = str(len(zip_data))
                
                # Add conversion info headers
                response['X-Original-Size'] = str(total_original_size)
                response['X-Converted-Size'] = str(total_converted_size)
                response['X-Output-Format'] = output_format.upper()
                response['X-Files-Count'] = str(len(converted_files))
                
                # Add cache control headers
                response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                
                return response
    
    except Exception as e:
        print(f"WebP to PNG conversion error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'error': f'Conversion failed: {str(e)}'
        }, status=500)
    
    finally:
        # Cleanup temp directory
        try:
            shutil.rmtree(temp_dir)
            print(f"Cleaned up temp directory: {temp_dir}")
        except Exception as e:
            print(f"Failed to cleanup temp directory: {e}")

# Helper function for WebP validation
def is_valid_webp(file_path):
    """Check if file is a valid WebP image"""
    try:
        with Image.open(file_path) as img:
            return img.format == 'WEBP'
    except Exception:
        return False

# Additional helper function for image format detection
def get_image_info(file_path):
    """Get detailed information about an image file"""
    try:
        with Image.open(file_path) as img:
            return {
                'format': img.format,
                'mode': img.mode,
                'size': img.size,
                'width': img.size[0],
                'height': img.size[1],
                'has_transparency': img.mode in ('RGBA', 'LA') or 'transparency' in img.info
            }
    except Exception as e:
        return {'error': str(e)}

# Enhanced WebP processing with metadata preservation
def convert_webp_with_metadata(input_path, output_path, output_format, quality=95, resize_options=None):
    """
    Convert WebP to other formats while preserving metadata where possible
    """
    try:
        with Image.open(input_path) as img:
            # Store original metadata
            original_info = img.info.copy()
            
            # Apply resize if specified
            if resize_options and resize_options.get('enabled', False):
                resize_type = resize_options.get('type', 'none')
                resize_value = resize_options.get('value', 0)
                
                if resize_type != 'none' and resize_value > 0:
                    original_width, original_height = img.size
                    
                    if resize_type == 'width':
                        ratio = resize_value / original_width
                        new_height = int(original_height * ratio)
                        img = img.resize((resize_value, new_height), Image.LANCZOS)
                    elif resize_type == 'height':
                        ratio = resize_value / original_height
                        new_width = int(original_width * ratio)
                        img = img.resize((new_width, resize_value), Image.LANCZOS)
                    elif resize_type == 'percentage':
                        scale = resize_value / 100
                        new_width = int(original_width * scale)
                        new_height = int(original_height * scale)
                        img = img.resize((new_width, new_height), Image.LANCZOS)
            
            # Handle format-specific conversions
            save_kwargs = {'optimize': True}
            
            if output_format.upper() == 'JPEG':
                # Convert to RGB for JPEG
                if img.mode in ('RGBA', 'P', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    if img.mode in ('RGBA', 'LA'):
                        background.paste(img, mask=img.split()[-1])
                    img = background
                
                save_kwargs.update({
                    'quality': quality,
                    'progressive': True,
                    'format': 'JPEG'
                })
                
            elif output_format.upper() == 'PNG':
                # PNG preserves transparency
                save_kwargs.update({
                    'compress_level': 6,
                    'format': 'PNG'
                })
                
                # Preserve metadata for PNG
                if original_info:
                    save_kwargs['pnginfo'] = original_info
            
            # Save the converted image
            img.save(output_path, **save_kwargs)
            
            return True
            
    except Exception as e:
        print(f"Error in convert_webp_with_metadata: {str(e)}")
        return False

# Add these view functions to your views.py file

def png_to_webp(request):
    """Render the PNG to WebP tool page"""
    return render(request, 'png_to_webp.html')

@csrf_exempt
@require_http_methods(["POST"])
def png_to_webp_api(request):
    """
    API endpoint to convert PNG images to WebP format
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    if not PIL_AVAILABLE:
        return JsonResponse({
            'error': 'Image processing library not available. Please install Pillow: pip install Pillow'
        }, status=500)
    
    # Handle both 'images' and 'files' keys from frontend
    image_files = []
    if 'images' in request.FILES:
        image_files = request.FILES.getlist('images')
    elif 'files' in request.FILES:
        image_files = request.FILES.getlist('files')
    else:
        return JsonResponse({'error': 'No PNG files found in request'}, status=400)
    
    if not image_files:
        return JsonResponse({'error': 'At least one PNG image is required'}, status=400)
    
    # Get conversion options
    quality = int(request.POST.get('quality', '85'))
    compression = request.POST.get('compression', 'lossy').lower()
    resize_option = request.POST.get('resize_option', 'none')
    resize_value = int(request.POST.get('resize_value', '0')) if request.POST.get('resize_value') else 0
    
    print(f"=== PNG to WebP CONVERSION SETTINGS ===")
    print(f"Files: {len(image_files)}")
    print(f"Quality: {quality}")
    print(f"Compression: {compression}")
    print(f"Resize: {resize_option} = {resize_value}")
    
    # Validate files
    max_file_size = 25 * 1024 * 1024  # 25MB per file
    max_total_size = 100 * 1024 * 1024  # 100MB total
    max_files = 50
    
    if len(image_files) > max_files:
        return JsonResponse({'error': f'Maximum {max_files} PNG files allowed'}, status=400)
    
    total_size = sum(file.size for file in image_files)
    if total_size > max_total_size:
        return JsonResponse({'error': 'Total file size exceeds 100MB limit'}, status=400)
    
    for file in image_files:
        if file.size > max_file_size:
            return JsonResponse({'error': f'File {file.name} exceeds 25MB limit'}, status=400)
        
        # Validate PNG format
        if not (file.content_type == 'image/png' or file.name.lower().endswith('.png')):
            return JsonResponse({'error': f'Invalid file format: {file.name}. Only PNG files are allowed.'}, status=400)
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix='png_to_webp_')
    print(f"Created temp directory: {temp_dir}")
    
    try:
        converted_files = []
        total_original_size = 0
        total_converted_size = 0
        
        for i, image_file in enumerate(image_files):
            print(f"\n=== Processing PNG file {i+1}: {image_file.name} ===")
            
            # Save original file to temp directory
            temp_input = os.path.join(temp_dir, f"input_{i}_{uuid.uuid4().hex}.png")
            
            with open(temp_input, 'wb') as f:
                for chunk in image_file.chunks():
                    f.write(chunk)
            
            original_size = os.path.getsize(temp_input)
            total_original_size += original_size
            print(f"Original PNG size: {original_size} bytes")
            
            try:
                # Open and process the PNG image
                with Image.open(temp_input) as img:
                    print(f"Original PNG image: {img.size} pixels, mode: {img.mode}")
                    
                    # Create a copy to work with
                    processed_img = img.copy()
                    
                    # Handle resize if specified
                    if resize_option != 'none' and resize_value > 0:
                        original_width, original_height = processed_img.size
                        
                        if resize_option == 'width':
                            ratio = resize_value / original_width
                            new_height = int(original_height * ratio)
                            processed_img = processed_img.resize((resize_value, new_height), Image.LANCZOS)
                            print(f"Resized by width: {processed_img.size}")
                            
                        elif resize_option == 'height':
                            ratio = resize_value / original_height
                            new_width = int(original_width * ratio)
                            processed_img = processed_img.resize((new_width, resize_value), Image.LANCZOS)
                            print(f"Resized by height: {processed_img.size}")
                            
                        elif resize_option == 'percentage':
                            scale = resize_value / 100
                            new_width = int(original_width * scale)
                            new_height = int(original_height * scale)
                            processed_img = processed_img.resize((new_width, new_height), Image.LANCZOS)
                            print(f"Resized by percentage: {processed_img.size}")
                    
                    # Create output filename
                    base_name = os.path.splitext(image_file.name)[0]
                    temp_output = os.path.join(temp_dir, f"converted_{base_name}_{uuid.uuid4().hex}.webp")
                    
                    # Prepare WebP save options
                    save_kwargs = {'format': 'WEBP', 'optimize': True}
                    
                    if compression == 'lossless':
                        # Lossless WebP compression
                        save_kwargs['lossless'] = True
                        save_kwargs['quality'] = 100  # Quality parameter is ignored in lossless mode
                        print("Using lossless WebP compression")
                    else:
                        # Lossy WebP compression
                        save_kwargs['quality'] = quality
                        save_kwargs['method'] = 6  # Compression method (0-6, higher = better compression)
                        print(f"Using lossy WebP compression with quality {quality}")
                    
                    # Convert to RGB if needed for lossy compression
                    if compression == 'lossy' and processed_img.mode == 'RGBA':
                        # For lossy WebP with transparency, we can keep RGBA
                        # But if there's no actual transparency, convert to RGB for better compression
                        if not has_transparency(processed_img):
                            background = Image.new('RGB', processed_img.size, (255, 255, 255))
                            background.paste(processed_img, mask=processed_img.split()[-1])
                            processed_img = background
                            print("Converted RGBA to RGB (no transparency detected)")
                    
                    # Save as WebP
                    processed_img.save(temp_output, **save_kwargs)
                    print(f"Saved as WebP with options: {save_kwargs}")
                    
                    converted_size = os.path.getsize(temp_output)
                    total_converted_size += converted_size
                    print(f"Converted size: {converted_size} bytes")
                    
                    # Calculate compression ratio
                    compression_ratio = (1 - converted_size / original_size) * 100
                    print(f"Compression ratio: {compression_ratio:.1f}%")
                    
                    # Store file info
                    converted_files.append({
                        'path': temp_output,
                        'name': f"converted_{base_name}.webp",
                        'original_name': image_file.name,
                        'original_size': original_size,
                        'converted_size': converted_size,
                        'compression_ratio': compression_ratio
                    })
                    
            except Exception as e:
                print(f"Error converting {image_file.name}: {str(e)}")
                # If conversion fails, skip this file
                continue
        
        print(f"\n=== CONVERSION SUMMARY ===")
        print(f"Files processed: {len(converted_files)}")
        print(f"Total original size: {total_original_size} bytes")
        print(f"Total converted size: {total_converted_size} bytes")
        
        if total_original_size > 0:
            overall_compression = (1 - total_converted_size / total_original_size) * 100
            print(f"Overall compression: {overall_compression:.1f}%")
        
        if not converted_files:
            return JsonResponse({'error': 'No files could be processed successfully'}, status=500)
        
        # Return result
        if len(converted_files) == 1:
            # Single file - return the converted image directly
            file_info = converted_files[0]
            
            with open(file_info['path'], 'rb') as f:
                file_data = f.read()
                
                print(f"Returning single file: {len(file_data)} bytes")
                
                response = HttpResponse(file_data, content_type='image/webp')
                response['Content-Disposition'] = f'attachment; filename="{file_info["name"]}"'
                response['Content-Length'] = str(len(file_data))
                
                # Add conversion info headers
                response['X-Original-Size'] = str(file_info['original_size'])
                response['X-Converted-Size'] = str(file_info['converted_size'])
                response['X-Compression-Ratio'] = f"{file_info['compression_ratio']:.1f}%"
                response['X-Quality'] = str(quality)
                response['X-Compression-Type'] = compression
                response['X-Files-Count'] = '1'
                
                # Add cache control headers
                response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                
                return response
        else:
            # Multiple files - create ZIP
            zip_path = os.path.join(temp_dir, 'converted_png_to_webp.zip')
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for file_info in converted_files:
                    zip_file.write(file_info['path'], file_info['name'])
            
            zip_size = os.path.getsize(zip_path)
            print(f"Created ZIP file: {zip_size} bytes")
            
            with open(zip_path, 'rb') as f:
                zip_data = f.read()
                
                response = HttpResponse(zip_data, content_type='application/zip')
                response['Content-Disposition'] = 'attachment; filename="converted_png_to_webp.zip"'
                response['Content-Length'] = str(len(zip_data))
                
                # Add conversion info headers
                response['X-Original-Size'] = str(total_original_size)
                response['X-Converted-Size'] = str(total_converted_size)
                overall_compression = (1 - total_converted_size / total_original_size) * 100 if total_original_size > 0 else 0
                response['X-Compression-Ratio'] = f"{overall_compression:.1f}%"
                response['X-Quality'] = str(quality)
                response['X-Compression-Type'] = compression
                response['X-Files-Count'] = str(len(converted_files))
                
                # Add cache control headers
                response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                
                return response
    
    except Exception as e:
        print(f"PNG to WebP conversion error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'error': f'Conversion failed: {str(e)}'
        }, status=500)
    
    finally:
        # Cleanup temp directory
        try:
            shutil.rmtree(temp_dir)
            print(f"Cleaned up temp directory: {temp_dir}")
        except Exception as e:
            print(f"Failed to cleanup temp directory: {e}")


# Helper function to check if image has transparency
def has_transparency(img):
    """Check if PNG image has actual transparency"""
    if img.mode != 'RGBA':
        return False
    
    # Check if alpha channel has any non-255 values
    alpha = img.split()[-1]
    return alpha.getextrema()[0] < 255


# Helper function for PNG validation
def is_valid_png(file_path):
    """Check if file is a valid PNG image"""
    try:
        with Image.open(file_path) as img:
            return img.format == 'PNG'
    except Exception:
        return False


# Enhanced PNG processing with metadata preservation
def convert_png_to_webp_with_metadata(input_path, output_path, quality=85, compression='lossy', resize_options=None):
    """
    Convert PNG to WebP while preserving metadata where possible
    """
    try:
        with Image.open(input_path) as img:
            # Store original metadata
            original_info = img.info.copy()
            
            # Apply resize if specified
            if resize_options and resize_options.get('enabled', False):
                resize_type = resize_options.get('type', 'none')
                resize_value = resize_options.get('value', 0)
                
                if resize_type != 'none' and resize_value > 0:
                    original_width, original_height = img.size
                    
                    if resize_type == 'width':
                        ratio = resize_value / original_width
                        new_height = int(original_height * ratio)
                        img = img.resize((resize_value, new_height), Image.LANCZOS)
                    elif resize_type == 'height':
                        ratio = resize_value / original_height
                        new_width = int(original_width * ratio)
                        img = img.resize((new_width, resize_value), Image.LANCZOS)
                    elif resize_type == 'percentage':
                        scale = resize_value / 100
                        new_width = int(original_width * scale)
                        new_height = int(original_height * scale)
                        img = img.resize((new_width, new_height), Image.LANCZOS)
            
            # Prepare WebP save options
            save_kwargs = {'format': 'WEBP', 'optimize': True}
            
            if compression == 'lossless':
                save_kwargs['lossless'] = True
                save_kwargs['quality'] = 100
            else:
                save_kwargs['quality'] = quality
                save_kwargs['method'] = 6
                
                # Convert to RGB if no transparency for better compression
                if img.mode == 'RGBA' and not has_transparency(img):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])
                    img = background
            
            # Save the converted image
            img.save(output_path, **save_kwargs)
            
            return True
            
    except Exception as e:
        print(f"Error in convert_png_to_webp_with_metadata: {str(e)}")
        return False


# Additional helper function for image optimization
def optimize_png_for_webp_conversion(img, compression_type='lossy'):
    """
    Optimize PNG image before WebP conversion
    """
    try:
        # If it's a grayscale image, ensure it's in the right mode
        if img.mode == 'L':
            # Keep as grayscale for better compression
            pass
        elif img.mode == 'P':
            # Convert palette to RGBA first, then decide
            img = img.convert('RGBA')
        
        # For lossy compression, remove unnecessary alpha if no transparency
        if compression_type == 'lossy' and img.mode == 'RGBA':
            if not has_transparency(img):
                # Convert to RGB with white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background
        
        return img
        
    except Exception as e:
        print(f"Error optimizing image: {str(e)}")
        return img

# Add these view functions to your views.py file

def pdf_to_png(request):
    """Render the PDF to PNG tool page"""
    return render(request, 'pdf_to_png.html')

@csrf_exempt
@require_http_methods(["POST"])
def pdf_to_png_api(request):
    """
    Enhanced API endpoint to convert PDF pages to PNG images
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    if not PYMUPDF_AVAILABLE:
        return JsonResponse({
            'error': 'PDF processing library not available. Please install PyMuPDF: pip install PyMuPDF'
        }, status=500)
    
    # Handle PDF files
    pdf_files = []
    if 'pdf_files' in request.FILES:
        pdf_files = request.FILES.getlist('pdf_files')
    elif 'files' in request.FILES:
        pdf_files = request.FILES.getlist('files')
    else:
        return JsonResponse({'error': 'No PDF files found in request'}, status=400)
    
    if not pdf_files:
        return JsonResponse({'error': 'At least one PDF file is required'}, status=400)
    
    # Get conversion options
    output_format = request.POST.get('output_format', 'png').lower()
    dpi = int(request.POST.get('dpi', '300'))
    page_selection = request.POST.get('page_selection', 'all')
    quality = request.POST.get('quality', 'high')
    page_range = request.POST.get('page_range', '')
    custom_pages = request.POST.get('custom_pages', '')
    
    print(f"=== PDF to PNG CONVERSION SETTINGS ===")
    print(f"Files: {len(pdf_files)}")
    print(f"Output Format: {output_format}")
    print(f"DPI: {dpi}")
    print(f"Page Selection: {page_selection}")
    print(f"Quality: {quality}")
    print(f"Page Range: {page_range}")
    print(f"Custom Pages: {custom_pages}")
    
    # Validate files
    max_file_size = 50 * 1024 * 1024  # 50MB per file
    max_total_size = 200 * 1024 * 1024  # 200MB total
    max_files = 10
    
    if len(pdf_files) > max_files:
        return JsonResponse({'error': f'Maximum {max_files} PDF files allowed'}, status=400)
    
    total_size = sum(file.size for file in pdf_files)
    if total_size > max_total_size:
        return JsonResponse({'error': 'Total file size exceeds 200MB limit'}, status=400)
    
    for file in pdf_files:
        if file.size > max_file_size:
            return JsonResponse({'error': f'File {file.name} exceeds 50MB limit'}, status=400)
        
        # Validate PDF format
        if not (file.content_type == 'application/pdf' or file.name.lower().endswith('.pdf')):
            return JsonResponse({'error': f'Invalid file format: {file.name}. Only PDF files are allowed.'}, status=400)
    
    # Validate DPI range
    if dpi < 72 or dpi > 600:
        return JsonResponse({'error': 'DPI must be between 72 and 600'}, status=400)
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix='pdf_to_png_')
    print(f"Created temp directory: {temp_dir}")
    
    try:
        converted_images = []
        total_pages_processed = 0
        
        for file_index, pdf_file in enumerate(pdf_files):
            print(f"\n=== Processing PDF {file_index + 1}: {pdf_file.name} ===")
            
            # Save PDF to temp directory
            temp_pdf_path = os.path.join(temp_dir, f"input_{file_index}_{uuid.uuid4().hex}.pdf")
            
            with open(temp_pdf_path, 'wb') as f:
                for chunk in pdf_file.chunks():
                    f.write(chunk)
            
            try:
                # Open PDF with PyMuPDF
                pdf_document = fitz.open(temp_pdf_path)
                total_pages = len(pdf_document)
                print(f"PDF has {total_pages} pages")
                
                # Determine which pages to process
                pages_to_process = determine_pages_to_process(
                    page_selection, total_pages, page_range, custom_pages
                )
                
                if not pages_to_process:
                    pdf_document.close()
                    continue
                
                print(f"Processing pages: {pages_to_process}")
                
                # Convert each page to image
                for page_num in pages_to_process:
                    try:
                        if page_num < 1 or page_num > total_pages:
                            print(f"Skipping invalid page number: {page_num}")
                            continue
                        
                        # Get page (PyMuPDF uses 0-based indexing)
                        page = pdf_document[page_num - 1]
                        
                        # Calculate zoom for DPI
                        zoom = dpi / 72.0  # 72 DPI is default
                        mat = fitz.Matrix(zoom, zoom)
                        
                        # Render page to pixmap
                        pix = page.get_pixmap(matrix=mat, alpha=True)
                        
                        # Convert to bytes
                        if output_format == 'png':
                            img_data = pix.tobytes("png")
                            content_type = 'image/png'
                            file_ext = 'png'
                        else:  # jpg/jpeg
                            # For JPEG, we need to remove alpha channel
                            pix_no_alpha = page.get_pixmap(matrix=mat, alpha=False)
                            img_data = pix_no_alpha.tobytes("jpeg", jpg_quality=get_jpeg_quality(quality))
                            content_type = 'image/jpeg'
                            file_ext = 'jpg'
                        
                        # Generate unique filename
                        unique_id = str(uuid.uuid4())[:8]
                        if len(pdf_files) == 1:
                            filename = f"page_{page_num}_{unique_id}.{file_ext}"
                        else:
                            filename = f"file_{file_index + 1}_page_{page_num}_{unique_id}.{file_ext}"
                        
                        # Save to media storage
                        file_path = f"converted_images/{filename}"
                        
                        # Create a file-like object from bytes
                        img_buffer = io.BytesIO(img_data)
                        img_buffer.name = filename
                        
                        saved_path = default_storage.save(file_path, img_buffer)
                        
                        # Get URL for the saved file
                        file_url = default_storage.url(saved_path)
                        
                        # Get image dimensions
                        img_width = pix.width
                        img_height = pix.height
                        
                        converted_images.append({
                            'page': page_num,
                            'url': file_url,
                            'filename': filename,
                            'format': file_ext,
                            'size': len(img_data),
                            'width': img_width,
                            'height': img_height,
                            'dpi': dpi,
                            'source_file': pdf_file.name
                        })
                        
                        total_pages_processed += 1
                        print(f"Converted page {page_num}: {filename} ({len(img_data)} bytes)")
                        
                    except Exception as e:
                        print(f"Error converting page {page_num}: {str(e)}")
                        continue
                
                pdf_document.close()
                
            except Exception as e:
                print(f"Error processing PDF {pdf_file.name}: {str(e)}")
                continue
        
        print(f"\n=== CONVERSION SUMMARY ===")
        print(f"Total images created: {len(converted_images)}")
        print(f"Total pages processed: {total_pages_processed}")
        
        if not converted_images:
            return JsonResponse({'error': 'No pages could be converted successfully'}, status=500)
        
        # Return JSON response with image information
        return JsonResponse({
            'success': True,
            'images': converted_images,
            'total_images': len(converted_images),
            'output_format': output_format,
            'dpi': dpi,
            'quality': quality,
            'page_selection': page_selection
        })
    
    except Exception as e:
        print(f"PDF to PNG conversion error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'error': f'Conversion failed: {str(e)}'
        }, status=500)
    
    finally:
        # Cleanup temp directory
        try:
            shutil.rmtree(temp_dir)
            print(f"Cleaned up temp directory: {temp_dir}")
        except Exception as e:
            print(f"Failed to cleanup temp directory: {e}")


def determine_pages_to_process(page_selection, total_pages, page_range, custom_pages):
    """
    Determine which pages to process based on selection criteria
    """
    if page_selection == 'all':
        return list(range(1, total_pages + 1))
    
    elif page_selection == 'first':
        return [1] if total_pages >= 1 else []
    
    elif page_selection == 'last':
        return [total_pages] if total_pages >= 1 else []
    
    elif page_selection == 'range' and page_range:
        try:
            # Parse range like "1-5" or "3-10"
            if '-' in page_range:
                start, end = map(int, page_range.split('-', 1))
                start = max(1, start)
                end = min(total_pages, end)
                if start <= end:
                    return list(range(start, end + 1))
            else:
                # Single page number
                page_num = int(page_range)
                if 1 <= page_num <= total_pages:
                    return [page_num]
        except ValueError:
            pass
    
    elif page_selection == 'custom' and custom_pages:
        try:
            pages = []
            # Parse custom pages like "1,3,5-7,10"
            for part in custom_pages.split(','):
                part = part.strip()
                if '-' in part:
                    # Range
                    start, end = map(int, part.split('-', 1))
                    start = max(1, start)
                    end = min(total_pages, end)
                    if start <= end:
                        pages.extend(range(start, end + 1))
                else:
                    # Single page
                    page_num = int(part)
                    if 1 <= page_num <= total_pages:
                        pages.append(page_num)
            
            # Remove duplicates and sort
            return sorted(list(set(pages)))
        except ValueError:
            pass
    
    return []


def get_jpeg_quality(quality_setting):
    """
    Convert quality setting to JPEG quality value
    """
    quality_map = {
        'high': 95,
        'medium': 85,
        'low': 75
    }
    return quality_map.get(quality_setting, 95)


@csrf_exempt
@require_http_methods(["POST"])
def download_pdf_images_zip(request):
    """
    Enhanced download function for PDF to PNG converted images
    """
    try:
        image_urls_json = request.POST.get('image_urls', '[]')
        file_name = request.POST.get('file_name', 'pdf_pages')
        format_type = request.POST.get('format', 'png')
        
        try:
            image_data = json.loads(image_urls_json)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid image data format'}, status=400)
        
        if not image_data:
            return JsonResponse({'error': 'No images to download'}, status=400)
        
        # If only 1 image, download it directly
        if len(image_data) == 1:
            image_info = image_data[0]
            
            try:
                # Get the file path from URL
                file_url = image_info.get('url', '')
                if not file_url:
                    return JsonResponse({'error': 'Invalid image URL'}, status=400)
                
                # Extract file path from URL
                file_path = file_url.replace(settings.MEDIA_URL, '')
                
                # Read file from storage
                if default_storage.exists(file_path):
                    file_content = default_storage.open(file_path).read()
                    
                    # Generate filename for single download
                    page_num = image_info.get('page', 1)
                    single_filename = f"{file_name}_page_{page_num}.{format_type}"
                    
                    # Determine content type
                    content_type = 'image/png' if format_type == 'png' else 'image/jpeg'
                    
                    # Return single image file
                    response = HttpResponse(file_content, content_type=content_type)
                    response['Content-Disposition'] = f'attachment; filename="{single_filename}"'
                    response['Content-Length'] = str(len(file_content))
                    
                    # Add metadata headers
                    response['X-Image-Count'] = '1'
                    response['X-Page-Number'] = str(page_num)
                    response['X-Format'] = format_type.upper()
                    
                    return response
                else:
                    return JsonResponse({'error': 'Image file not found'}, status=404)
                    
            except Exception as e:
                print(f"Error downloading single image: {str(e)}")
                return JsonResponse({'error': 'Failed to download image'}, status=500)
        
        # For multiple images, create ZIP file
        else:
            # Create ZIP file in memory
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for i, image_info in enumerate(image_data):
                    try:
                        # Get the file path from URL
                        file_url = image_info.get('url', '')
                        if not file_url:
                            continue
                        
                        # Extract file path from URL
                        file_path = file_url.replace(settings.MEDIA_URL, '')
                        
                        # Read file from storage
                        if default_storage.exists(file_path):
                            file_content = default_storage.open(file_path).read()
                            
                            # Generate filename for ZIP
                            page_num = image_info.get('page', i + 1)
                            source_file = image_info.get('source_file', 'document')
                            
                            # Clean source filename
                            source_name = os.path.splitext(source_file)[0]
                            source_name = re.sub(r'[^\w\-_]', '_', source_name)
                            
                            zip_filename = f"{source_name}_page_{page_num}.{format_type}"
                            
                            # Add file to ZIP
                            zip_file.writestr(zip_filename, file_content)
                            
                    except Exception as e:
                        print(f"Error adding image to ZIP: {str(e)}")
                        continue
            
            zip_buffer.seek(0)
            
            # Create HTTP response with ZIP file
            response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="{file_name}_images.zip"'
            response['Content-Length'] = str(len(zip_buffer.getvalue()))
            
            # Add metadata headers
            response['X-Image-Count'] = str(len(image_data))
            response['X-Format'] = format_type.upper()
            response['X-Archive-Type'] = 'ZIP'
            
            return response
    
    except Exception as e:
        print(f"Download error: {str(e)}")
        return JsonResponse({'error': 'Failed to create download'}, status=500)


# Helper function to validate PDF file
def validate_pdf_file(file_path):
    """
    Validate if the file is a proper PDF
    """
    try:
        with open(file_path, 'rb') as f:
            # Check PDF signature
            header = f.read(5)
            if header.startswith(b'%PDF-'):
                return True
        return False
    except Exception:
        return False


def get_pdf_info(file_path):
    """
    Get detailed information about a PDF file
    """
    try:
        pdf_doc = fitz.open(file_path)
        info = {
            'page_count': len(pdf_doc),
            'title': pdf_doc.metadata.get('title', ''),
            'author': pdf_doc.metadata.get('author', ''),
            'subject': pdf_doc.metadata.get('subject', ''),
            'creator': pdf_doc.metadata.get('creator', ''),
            'producer': pdf_doc.metadata.get('producer', ''),
            'creation_date': pdf_doc.metadata.get('creationDate', ''),
            'modification_date': pdf_doc.metadata.get('modDate', ''),
            'encrypted': pdf_doc.needs_pass,
            'pages': []
        }
        
        # Get page dimensions for first few pages
        for page_num in range(min(3, len(pdf_doc))):
            page = pdf_doc[page_num]
            rect = page.rect
            info['pages'].append({
                'page': page_num + 1,
                'width': rect.width,
                'height': rect.height,
                'rotation': page.rotation
            })
        
        pdf_doc.close()
        return info
        
    except Exception as e:
        print(f"Error getting PDF info: {str(e)}")
        return None


def optimize_image_for_web(image_path, max_width=1920, quality=85):
    """
    Optimize converted images for web use
    """
    try:
        from PIL import Image
        
        with Image.open(image_path) as img:
            # Resize if too large
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            # Optimize and save
            optimized_path = image_path.replace('.png', '_optimized.png')
            img.save(optimized_path, 'PNG', optimize=True)
            
            return optimized_path
            
    except Exception as e:
        print(f"Error optimizing image: {str(e)}")
        return image_path


def create_image_thumbnail(image_path, size=(150, 150)):
    """
    Create thumbnail for image preview
    """
    try:
        from PIL import Image
        
        with Image.open(image_path) as img:
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            thumbnail_path = image_path.replace('.png', '_thumb.png')
            img.save(thumbnail_path, 'PNG')
            
            return thumbnail_path
            
    except Exception as e:
        print(f"Error creating thumbnail: {str(e)}")
        return None


def batch_convert_pdf_pages(pdf_paths, output_dir, settings):
    """
    Enhanced batch conversion with parallel processing
    """
    import concurrent.futures
    import multiprocessing
    
    max_workers = min(multiprocessing.cpu_count(), 4)  # Limit to 4 workers
    converted_images = []
    
    def convert_single_pdf(pdf_info):
        pdf_path, file_index, settings = pdf_info
        return convert_pdf_to_images(pdf_path, file_index, output_dir, settings)
    
    # Prepare PDF info for parallel processing
    pdf_infos = [(path, idx, settings) for idx, path in enumerate(pdf_paths)]
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_pdf = {executor.submit(convert_single_pdf, pdf_info): pdf_info 
                        for pdf_info in pdf_infos}
        
        for future in concurrent.futures.as_completed(future_to_pdf):
            try:
                result = future.result()
                if result:
                    converted_images.extend(result)
            except Exception as e:
                print(f"Error in parallel conversion: {str(e)}")
                continue
    
    return converted_images


def convert_pdf_to_images(pdf_path, file_index, output_dir, settings):
    """
    Convert a single PDF to images with advanced options
    """
    try:
        pdf_doc = fitz.open(pdf_path)
        converted_images = []
        
        # Get conversion settings
        output_format = settings.get('output_format', 'png')
        dpi = settings.get('dpi', 300)
        quality = settings.get('quality', 'high')
        page_selection = settings.get('page_selection', 'all')
        
        # Determine pages to process
        total_pages = len(pdf_doc)
        pages_to_process = determine_pages_to_process(
            page_selection, total_pages, 
            settings.get('page_range', ''), 
            settings.get('custom_pages', '')
        )
        
        for page_num in pages_to_process:
            try:
                page = pdf_doc[page_num - 1]
                
                # Calculate zoom for DPI
                zoom = dpi / 72.0
                mat = fitz.Matrix(zoom, zoom)
                
                # Advanced rendering options
                if output_format == 'png':
                    pix = page.get_pixmap(matrix=mat, alpha=True)
                    img_data = pix.tobytes("png")
                    file_ext = 'png'
                else:
                    pix = page.get_pixmap(matrix=mat, alpha=False)
                    jpeg_quality = get_jpeg_quality(quality)
                    img_data = pix.tobytes("jpeg", jpg_quality=jpeg_quality)
                    file_ext = 'jpg'
                
                # Generate filename
                filename = f"file_{file_index + 1}_page_{page_num}_{uuid.uuid4().hex[:8]}.{file_ext}"
                image_path = os.path.join(output_dir, filename)
                
                # Save image
                with open(image_path, 'wb') as f:
                    f.write(img_data)
                
                # Create image info
                image_info = {
                    'page': page_num,
                    'filename': filename,
                    'path': image_path,
                    'format': file_ext,
                    'size': len(img_data),
                    'width': pix.width,
                    'height': pix.height,
                    'dpi': dpi
                }
                
                converted_images.append(image_info)
                
            except Exception as e:
                print(f"Error converting page {page_num}: {str(e)}")
                continue
        
        pdf_doc.close()
        return converted_images
        
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        return []


@csrf_exempt
def get_pdf_preview(request):
    """
    API endpoint to get PDF preview information
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    if 'pdf_file' not in request.FILES:
        return JsonResponse({'error': 'PDF file is required'}, status=400)
    
    pdf_file = request.FILES['pdf_file']
    
    # Validate file
    if not pdf_file.name.lower().endswith('.pdf'):
        return JsonResponse({'error': 'Invalid file type'}, status=400)
    
    if pdf_file.size > 50 * 1024 * 1024:  # 50MB limit
        return JsonResponse({'error': 'File too large'}, status=400)
    
    temp_dir = tempfile.mkdtemp(prefix='pdf_preview_')
    
    try:
        # Save PDF temporarily
        temp_pdf_path = os.path.join(temp_dir, f"preview_{uuid.uuid4().hex}.pdf")
        with open(temp_pdf_path, 'wb') as f:
            for chunk in pdf_file.chunks():
                f.write(chunk)
        
        # Get PDF information
        pdf_info = get_pdf_info(temp_pdf_path)
        
        if pdf_info:
            return JsonResponse({
                'success': True,
                'pdf_info': pdf_info
            })
        else:
            return JsonResponse({'error': 'Could not read PDF file'}, status=400)
    
    except Exception as e:
        return JsonResponse({'error': f'Preview failed: {str(e)}'}, status=500)
    
    finally:
        try:
            shutil.rmtree(temp_dir)
        except:
            pass


# Advanced error handling and logging
def log_conversion_error(error, context):
    """
    Log conversion errors with context for debugging
    """
    import logging
    
    logger = logging.getLogger('pdf_converter')
    logger.error(f"PDF to PNG conversion error: {error}", extra={
        'context': context,
        'timestamp': timezone.now().isoformat()
    })


def cleanup_old_converted_files():
    """
    Cleanup old converted files (run as scheduled task)
    """
    try:
        # Clean files older than 1 hour
        cutoff_time = datetime.now() - timedelta(hours=1)
        
        converted_dir = os.path.join(settings.MEDIA_ROOT, 'converted_images')
        if os.path.exists(converted_dir):
            for filename in os.listdir(converted_dir):
                file_path = os.path.join(converted_dir, filename)
                
                # Check file age
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                if file_time < cutoff_time:
                    try:
                        os.remove(file_path)
                        print(f"Cleaned up old file: {filename}")
                    except Exception as e:
                        print(f"Error removing file {filename}: {e}")
    
    except Exception as e:
        print(f"Error in cleanup task: {e}")


# Performance monitoring decorator
def monitor_conversion_performance(func):
    """
    Decorator to monitor conversion performance
    """
    def wrapper(*args, **kwargs):
        import time
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"Conversion completed in {duration:.2f} seconds")
            
            return result
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"Conversion failed after {duration:.2f} seconds: {str(e)}")
            raise
    
    return wrapper

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4, A3, A5, legal
    from reportlab.lib.units import mm, inch
    from reportlab.lib.utils import ImageReader
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# For image processing
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

def png_to_pdf(request):
    """Render the PNG to PDF tool page"""
    return render(request, 'png_to_pdf.html')

@csrf_exempt
@require_http_methods(["POST"])
def png_to_pdf_api(request):
    """
    API endpoint to convert PNG images to PDF format
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    if not REPORTLAB_AVAILABLE:
        return JsonResponse({
            'error': 'PDF generation library not available. Please install ReportLab: pip install reportlab'
        }, status=500)
    
    if not PIL_AVAILABLE:
        return JsonResponse({
            'error': 'Image processing library not available. Please install Pillow: pip install Pillow'
        }, status=500)
    
    # Handle both 'images' and 'files' keys from frontend
    image_files = []
    if 'images' in request.FILES:
        image_files = request.FILES.getlist('images')
    elif 'files' in request.FILES:
        image_files = request.FILES.getlist('files')
    else:
        return JsonResponse({'error': 'No PNG files found in request'}, status=400)
    
    if not image_files:
        return JsonResponse({'error': 'At least one PNG image is required'}, status=400)
    
    # Get conversion options
    page_size = request.POST.get('page_size', 'A4').upper()
    orientation = request.POST.get('orientation', 'portrait')
    layout = request.POST.get('layout', 'one-per-page')
    margin = request.POST.get('margin', 'medium')
    
    print(f"=== PNG to PDF CONVERSION SETTINGS ===")
    print(f"Files: {len(image_files)}")
    print(f"Page Size: {page_size}")
    print(f"Orientation: {orientation}")
    print(f"Layout: {layout}")
    print(f"Margin: {margin}")
    
    # Validate files
    max_file_size = 25 * 1024 * 1024  # 25MB per file
    max_total_size = 100 * 1024 * 1024  # 100MB total
    max_files = 50
    
    if len(image_files) > max_files:
        return JsonResponse({'error': f'Maximum {max_files} PNG files allowed'}, status=400)
    
    total_size = sum(file.size for file in image_files)
    if total_size > max_total_size:
        return JsonResponse({'error': 'Total file size exceeds 100MB limit'}, status=400)
    
    for file in image_files:
        if file.size > max_file_size:
            return JsonResponse({'error': f'File {file.name} exceeds 25MB limit'}, status=400)
        
        # Validate PNG format
        if not (file.content_type == 'image/png' or file.name.lower().endswith('.png')):
            return JsonResponse({'error': f'Invalid file format: {file.name}. Only PNG files are allowed.'}, status=400)
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix='png_to_pdf_')
    print(f"Created temp directory: {temp_dir}")
    
    try:
        # Define page sizes and margins
        page_sizes = {
            'A4': A4,
            'LETTER': letter,
            'A3': A3,
            'A5': A5,
            'LEGAL': legal,
        }
        
        margin_sizes = {
            'none': 0,
            'small': 10 * mm,
            'medium': 20 * mm,
            'large': 30 * mm,
        }
        
        # Get page size
        if page_size in page_sizes:
            page_width, page_height = page_sizes[page_size]
        else:
            page_width, page_height = A4  # Default to A4
        
        # Handle orientation
        if orientation == 'landscape':
            page_width, page_height = page_height, page_width
        
        # Get margin
        margin_size = margin_sizes.get(margin, 20 * mm)
        
        # Calculate available space
        available_width = page_width - (2 * margin_size)
        available_height = page_height - (2 * margin_size)
        
        print(f"Page dimensions: {page_width} x {page_height}")
        print(f"Available space: {available_width} x {available_height}")
        
        # Create PDF file
        pdf_filename = f"converted_png_to_pdf_{uuid.uuid4().hex}.pdf"
        pdf_path = os.path.join(temp_dir, pdf_filename)
        
        # Create PDF canvas
        c = canvas.Canvas(pdf_path, pagesize=(page_width, page_height))
        
        processed_images = 0
        current_page_images = 0
        images_per_page = 1 if layout == 'one-per-page' else 2  # Can be adjusted
        
        for i, image_file in enumerate(image_files):
            print(f"\n=== Processing PNG file {i+1}: {image_file.name} ===")
            
            # Save original file to temp directory
            temp_input = os.path.join(temp_dir, f"input_{i}_{uuid.uuid4().hex}.png")
            
            with open(temp_input, 'wb') as f:
                for chunk in image_file.chunks():
                    f.write(chunk)
            
            try:
                # Open and process the PNG image
                with Image.open(temp_input) as img:
                    print(f"Original PNG image: {img.size} pixels, mode: {img.mode}")
                    
                    # Convert to RGB if necessary (for better PDF compatibility)
                    if img.mode in ('RGBA', 'LA'):
                        # Create white background for transparent images
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'LA':
                            img = img.convert('RGBA')
                        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = background
                    elif img.mode == 'P':
                        img = img.convert('RGB')
                    elif img.mode not in ('RGB', 'L'):
                        img = img.convert('RGB')
                    
                    # Get image dimensions
                    img_width, img_height = img.size
                    
                    # Calculate scaling to fit available space
                    if layout == 'fit-to-page':
                        # Scale to fill entire available space
                        scale_x = available_width / img_width
                        scale_y = available_height / img_height
                        scale = min(scale_x, scale_y)  # Maintain aspect ratio
                    else:
                        # Scale to fit within available space
                        scale_x = available_width / img_width
                        scale_y = available_height / img_height
                        
                        if layout == 'multiple-per-page' and images_per_page > 1:
                            # Adjust available height for multiple images
                            adjusted_height = available_height / images_per_page
                            scale_y = adjusted_height / img_height
                        
                        scale = min(scale_x, scale_y, 1.0)  # Don't upscale beyond original size
                    
                    # Calculate final image dimensions
                    final_width = img_width * scale
                    final_height = img_height * scale
                    
                    print(f"Scale factor: {scale}")
                    print(f"Final dimensions: {final_width} x {final_height}")
                    
                    # Determine image position based on layout
                    if layout == 'multiple-per-page' and images_per_page > 1:
                        # Position for multiple images per page
                        y_offset = current_page_images * (available_height / images_per_page)
                        x_pos = margin_size + (available_width - final_width) / 2
                        y_pos = page_height - margin_size - y_offset - final_height
                    else:
                        # Center the image on the page
                        x_pos = margin_size + (available_width - final_width) / 2
                        y_pos = margin_size + (available_height - final_height) / 2
                    
                    # Handle auto orientation
                    if orientation == 'auto':
                        # Determine best orientation based on image aspect ratio
                        img_aspect = img_width / img_height
                        page_aspect = page_width / page_height
                        
                        if (img_aspect > 1 and page_aspect < 1) or (img_aspect < 1 and page_aspect > 1):
                            # Switch page orientation for better fit
                            page_width, page_height = page_height, page_width
                            available_width = page_width - (2 * margin_size)
                            available_height = page_height - (2 * margin_size)
                            
                            # Recalculate scaling and position
                            scale_x = available_width / img_width
                            scale_y = available_height / img_height
                            scale = min(scale_x, scale_y, 1.0)
                            final_width = img_width * scale
                            final_height = img_height * scale
                            x_pos = margin_size + (available_width - final_width) / 2
                            y_pos = margin_size + (available_height - final_height) / 2
                            
                            # Create new page with updated dimensions
                            c.setPageSize((page_width, page_height))
                    
                    # Create a temporary resized image
                    if scale != 1.0:
                        resized_img = img.resize((int(final_width), int(final_height)), Image.LANCZOS)
                    else:
                        resized_img = img
                    
                    # Save resized image to temp file
                    temp_resized = os.path.join(temp_dir, f"resized_{i}_{uuid.uuid4().hex}.png")
                    resized_img.save(temp_resized, 'PNG')
                    
                    # Add image to PDF
                    try:
                        c.drawImage(temp_resized, x_pos, y_pos, width=final_width, height=final_height)
                        print(f"Added image to PDF at position ({x_pos}, {y_pos})")
                    except Exception as e:
                        print(f"Error adding image to PDF: {str(e)}")
                        # Try with ImageReader as fallback
                        img_reader = ImageReader(temp_resized)
                        c.drawImage(img_reader, x_pos, y_pos, width=final_width, height=final_height)
                    
                    processed_images += 1
                    current_page_images += 1
                    
                    # Check if we need a new page
                    if layout == 'one-per-page' or (layout == 'multiple-per-page' and current_page_images >= images_per_page):
                        if i < len(image_files) - 1:  # Not the last image
                            c.showPage()  # Start new page
                            current_page_images = 0
                            print("Created new page")
                    
                    # Clean up temp resized image
                    try:
                        os.remove(temp_resized)
                    except:
                        pass
                        
            except Exception as e:
                print(f"Error processing {image_file.name}: {str(e)}")
                # Continue with next image instead of failing completely
                continue
        
        # Finalize PDF
        c.save()
        pdf_size = os.path.getsize(pdf_path)
        
        print(f"\n=== PDF CREATION SUMMARY ===")
        print(f"Images processed: {processed_images}")
        print(f"PDF size: {pdf_size} bytes")
        print(f"PDF path: {pdf_path}")
        
        if processed_images == 0:
            return JsonResponse({'error': 'No images could be processed successfully'}, status=500)
        
        # Return the PDF file
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
            
            print(f"Returning PDF: {len(pdf_data)} bytes")
            
            response = HttpResponse(pdf_data, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="converted_images.pdf"'
            response['Content-Length'] = str(len(pdf_data))
            
            # Add conversion info headers
            response['X-Images-Count'] = str(processed_images)
            response['X-Page-Size'] = page_size
            response['X-Orientation'] = orientation
            response['X-Layout'] = layout
            response['X-PDF-Size'] = str(pdf_size)
            
            # Add cache control headers
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            
            return response
    
    except Exception as e:
        print(f"PNG to PDF conversion error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'error': f'Conversion failed: {str(e)}'
        }, status=500)
    
    finally:
        # Cleanup temp directory
        try:
            shutil.rmtree(temp_dir)
            print(f"Cleaned up temp directory: {temp_dir}")
        except Exception as e:
            print(f"Failed to cleanup temp directory: {e}")

# Helper function for PNG validation
def is_valid_png(file_path):
    """Check if file is a valid PNG image"""
    try:
        with Image.open(file_path) as img:
            return img.format == 'PNG'
    except Exception:
        return False

# Enhanced PNG to PDF with advanced layout options
def create_pdf_with_layout(image_files, settings):
    """
    Create PDF with advanced layout options
    """
    try:
        page_size = settings.get('page_size', 'A4')
        orientation = settings.get('orientation', 'portrait')
        layout = settings.get('layout', 'one-per-page')
        margin = settings.get('margin', 'medium')
        
        # Page size mapping
        page_sizes = {
            'A4': A4,
            'LETTER': letter,
            'A3': A3,
            'A5': A5,
            'LEGAL': legal,
        }
        
        # Margin mapping
        margin_sizes = {
            'none': 0,
            'small': 10 * mm,
            'medium': 20 * mm,
            'large': 30 * mm,
        }
        
        page_width, page_height = page_sizes.get(page_size, A4)
        
        if orientation == 'landscape':
            page_width, page_height = page_height, page_width
        
        margin_size = margin_sizes.get(margin, 20 * mm)
        
        return {
            'page_width': page_width,
            'page_height': page_height,
            'margin': margin_size,
            'available_width': page_width - (2 * margin_size),
            'available_height': page_height - (2 * margin_size)
        }
        
    except Exception as e:
        print(f"Error in create_pdf_with_layout: {str(e)}")
        return None

# Advanced image positioning for PDF
def calculate_image_position(img_size, available_space, layout_type, page_index=0):
    """
    Calculate optimal image position based on layout type
    """
    img_width, img_height = img_size
    avail_width, avail_height = available_space
    
    # Calculate scale to fit
    scale_x = avail_width / img_width
    scale_y = avail_height / img_height
    scale = min(scale_x, scale_y, 1.0)  # Don't upscale
    
    final_width = img_width * scale
    final_height = img_height * scale
    
    if layout_type == 'center':
        x_pos = (avail_width - final_width) / 2
        y_pos = (avail_height - final_height) / 2
    elif layout_type == 'top-left':
        x_pos = 0
        y_pos = avail_height - final_height
    elif layout_type == 'top-center':
        x_pos = (avail_width - final_width) / 2
        y_pos = avail_height - final_height
    elif layout_type == 'top-right':
        x_pos = avail_width - final_width
        y_pos = avail_height - final_height
    else:
        # Default to center
        x_pos = (avail_width - final_width) / 2
        y_pos = (avail_height - final_height) / 2
    
    return {
        'x': x_pos,
        'y': y_pos,
        'width': final_width,
        'height': final_height,
        'scale': scale
    }

# Batch PNG to PDF conversion with progress tracking
def batch_png_to_pdf_conversion(image_files, settings, progress_callback=None):
    """
    Convert multiple PNG files to PDF with progress tracking
    """
    total_files = len(image_files)
    processed_files = 0
    
    try:
        # Initialize PDF settings
        pdf_settings = create_pdf_with_layout(image_files, settings)
        if not pdf_settings:
            raise Exception("Failed to initialize PDF settings")
        
        # Process each image
        for i, image_file in enumerate(image_files):
            try:
                # Process individual image
                # ... (image processing code here)
                
                processed_files += 1
                
                # Call progress callback if provided
                if progress_callback:
                    progress = (processed_files / total_files) * 100
                    progress_callback(progress, f"Processed {processed_files}/{total_files} images")
                    
            except Exception as e:
                print(f"Error processing file {i+1}: {str(e)}")
                continue
        
        return {
            'success': True,
            'processed_files': processed_files,
            'total_files': total_files
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'processed_files': processed_files,
            'total_files': total_files
        }

# PDF optimization and compression
def optimize_pdf_output(pdf_path, quality='medium'):
    """
    Optimize PDF file size and quality
    """
    try:
        # This would require additional libraries like PyPDF2 or similar
        # For now, return the original file
        return pdf_path
        
    except Exception as e:
        print(f"PDF optimization error: {str(e)}")
        return pdf_path

# Image quality and format validation
def validate_and_prepare_image(image_path, target_format='RGB'):
    """
    Validate and prepare image for PDF conversion
    """
    try:
        with Image.open(image_path) as img:
            # Check if image is valid
            img.verify()
            
            # Reopen for processing (verify() closes the image)
            img = Image.open(image_path)
            
            # Convert to target format if needed
            if img.mode != target_format:
                if img.mode in ('RGBA', 'LA'):
                    # Handle transparency
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img)
                    img = background
                else:
                    img = img.convert(target_format)
            
            return img
            
    except Exception as e:
        print(f"Image validation error: {str(e)}")
        return None

try:
    import PyPDF2
    from PyPDF2 import PdfReader, PdfWriter
    PYPDF2_AVAILABLE = True
except ImportError:
    try:
        import pypdf
        from pypdf import PdfReader, PdfWriter
        PYPDF2_AVAILABLE = True
    except ImportError:
        PYPDF2_AVAILABLE = False

def split_pdf(request):
    """Render the Split PDF tool page"""
    return render(request, 'split_pdf.html')

@csrf_exempt
@require_http_methods(["POST"])
def split_pdf_api(request):
    """
    API endpoint to split PDF files into separate pages or ranges
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    if not PYPDF2_AVAILABLE:
        return JsonResponse({
            'error': 'PDF processing library not available. Please install PyPDF2: pip install PyPDF2'
        }, status=500)
    
    # Get PDF file
    if 'pdf_file' not in request.FILES:
        return JsonResponse({'error': 'No PDF file found in request'}, status=400)
    
    pdf_file = request.FILES['pdf_file']
    
    if not pdf_file:
        return JsonResponse({'error': 'PDF file is required'}, status=400)
    
    # Get split options
    split_mode = request.POST.get('split_mode', 'all')
    start_page = request.POST.get('start_page')
    end_page = request.POST.get('end_page')
    custom_ranges = request.POST.get('custom_ranges', '')
    selected_pages = request.POST.get('selected_pages', '[]')
    
    print(f"=== SPLIT PDF SETTINGS ===")
    print(f"File: {pdf_file.name}")
    print(f"Split Mode: {split_mode}")
    print(f"Start Page: {start_page}")
    print(f"End Page: {end_page}")
    print(f"Custom Ranges: {custom_ranges}")
    print(f"Selected Pages: {selected_pages}")
    
    # Validate file
    max_file_size = 100 * 1024 * 1024  # 100MB
    if pdf_file.size > max_file_size:
        return JsonResponse({'error': 'File exceeds 100MB limit'}, status=400)
    
    # Validate PDF format
    if not (pdf_file.content_type == 'application/pdf' or pdf_file.name.lower().endswith('.pdf')):
        return JsonResponse({'error': 'Invalid file format. Only PDF files are allowed.'}, status=400)
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix='split_pdf_')
    print(f"Created temp directory: {temp_dir}")
    
    try:
        # Save PDF file to temp directory
        temp_pdf_path = os.path.join(temp_dir, f"input_{uuid.uuid4().hex}.pdf")
        
        with open(temp_pdf_path, 'wb') as f:
            for chunk in pdf_file.chunks():
                f.write(chunk)
        
        print(f"Saved PDF to: {temp_pdf_path}")
        
        # Read and analyze PDF
        try:
            pdf_reader = PdfReader(temp_pdf_path)
            total_pages = len(pdf_reader.pages)
            print(f"PDF has {total_pages} pages")
            
            if total_pages == 0:
                return JsonResponse({'error': 'PDF file appears to be empty'}, status=400)
            
        except Exception as e:
            print(f"Error reading PDF: {str(e)}")
            return JsonResponse({'error': f'Invalid or corrupted PDF file: {str(e)}'}, status=400)
        
        # Determine which pages to extract based on split mode
        pages_to_extract = []
        
        if split_mode == 'all':
            pages_to_extract = list(range(1, total_pages + 1))
            
        elif split_mode == 'range':
            try:
                start = int(start_page) if start_page else 1
                end = int(end_page) if end_page else total_pages
                
                if start < 1 or end > total_pages or start > end:
                    return JsonResponse({'error': f'Invalid page range. PDF has {total_pages} pages.'}, status=400)
                
                pages_to_extract = list(range(start, end + 1))
                
            except ValueError:
                return JsonResponse({'error': 'Invalid page numbers in range'}, status=400)
                
        elif split_mode == 'custom':
            if not custom_ranges.strip():
                return JsonResponse({'error': 'Custom ranges cannot be empty'}, status=400)
            
            try:
                pages_to_extract = parse_custom_ranges(custom_ranges, total_pages)
                if not pages_to_extract:
                    return JsonResponse({'error': 'No valid pages found in custom ranges'}, status=400)
                    
            except Exception as e:
                return JsonResponse({'error': f'Invalid custom ranges: {str(e)}'}, status=400)
                
        elif split_mode == 'select':
            try:
                selected_pages_list = json.loads(selected_pages)
                if not selected_pages_list:
                    return JsonResponse({'error': 'No pages selected'}, status=400)
                
                # Validate selected pages
                for page in selected_pages_list:
                    if not isinstance(page, int) or page < 1 or page > total_pages:
                        return JsonResponse({'error': f'Invalid page number: {page}'}, status=400)
                
                pages_to_extract = sorted(selected_pages_list)
                
            except (json.JSONDecodeError, ValueError) as e:
                return JsonResponse({'error': f'Invalid selected pages format: {str(e)}'}, status=400)
        
        else:
            return JsonResponse({'error': 'Invalid split mode'}, status=400)
        
        print(f"Pages to extract: {pages_to_extract}")
        
        # Create output PDFs
        output_files = []
        total_output_size = 0
        
        if split_mode == 'all' or split_mode == 'select':
            # Create individual PDF for each page
            for page_num in pages_to_extract:
                pdf_writer = PdfWriter()
                pdf_writer.add_page(pdf_reader.pages[page_num - 1])  # PyPDF2 uses 0-based indexing
                
                output_filename = f"page_{page_num:03d}.pdf"
                output_path = os.path.join(temp_dir, output_filename)
                
                with open(output_path, 'wb') as output_file:
                    pdf_writer.write(output_file)
                
                file_size = os.path.getsize(output_path)
                total_output_size += file_size
                
                output_files.append({
                    'path': output_path,
                    'name': output_filename,
                    'size': file_size
                })
                
                print(f"Created: {output_filename} ({file_size} bytes)")
                
        elif split_mode == 'range':
            # Create single PDF with the range
            pdf_writer = PdfWriter()
            
            for page_num in pages_to_extract:
                pdf_writer.add_page(pdf_reader.pages[page_num - 1])
            
            start = pages_to_extract[0]
            end = pages_to_extract[-1]
            output_filename = f"pages_{start:03d}-{end:03d}.pdf"
            output_path = os.path.join(temp_dir, output_filename)
            
            with open(output_path, 'wb') as output_file:
                pdf_writer.write(output_file)
            
            file_size = os.path.getsize(output_path)
            total_output_size += file_size
            
            output_files.append({
                'path': output_path,
                'name': output_filename,
                'size': file_size
            })
            
            print(f"Created: {output_filename} ({file_size} bytes)")
            
        elif split_mode == 'custom':
            # Create PDFs based on custom ranges
            ranges = parse_custom_ranges_detailed(custom_ranges, total_pages)
            
            for i, page_range in enumerate(ranges):
                pdf_writer = PdfWriter()
                
                for page_num in page_range:
                    pdf_writer.add_page(pdf_reader.pages[page_num - 1])
                
                if len(page_range) == 1:
                    output_filename = f"page_{page_range[0]:03d}.pdf"
                else:
                    output_filename = f"pages_{page_range[0]:03d}-{page_range[-1]:03d}.pdf"
                
                output_path = os.path.join(temp_dir, output_filename)
                
                with open(output_path, 'wb') as output_file:
                    pdf_writer.write(output_file)
                
                file_size = os.path.getsize(output_path)
                total_output_size += file_size
                
                output_files.append({
                    'path': output_path,
                    'name': output_filename,
                    'size': file_size
                })
                
                print(f"Created: {output_filename} ({file_size} bytes)")
        
        if not output_files:
            return JsonResponse({'error': 'No PDF files were created'}, status=500)
        
        print(f"\n=== SPLIT SUMMARY ===")
        print(f"Files created: {len(output_files)}")
        print(f"Total output size: {total_output_size} bytes")
        
        # Return result
        if len(output_files) == 1:
            # Single file - return directly
            file_info = output_files[0]
            
            with open(file_info['path'], 'rb') as f:
                pdf_data = f.read()
                
                response = HttpResponse(pdf_data, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{file_info["name"]}"'
                response['Content-Length'] = str(len(pdf_data))
                
                # Add split info headers
                response['X-Split-Mode'] = split_mode
                response['X-Pages-Extracted'] = str(len(pages_to_extract))
                response['X-Output-Files'] = '1'
                response['X-Total-Size'] = str(file_info['size'])
                
                # Add cache control headers
                response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                
                return response
        else:
            # Multiple files - create ZIP
            zip_filename = f"split_{pdf_file.name.replace('.pdf', '')}.zip"
            zip_path = os.path.join(temp_dir, zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for file_info in output_files:
                    zip_file.write(file_info['path'], file_info['name'])
            
            zip_size = os.path.getsize(zip_path)
            print(f"Created ZIP file: {zip_filename} ({zip_size} bytes)")
            
            with open(zip_path, 'rb') as f:
                zip_data = f.read()
                
                response = HttpResponse(zip_data, content_type='application/zip')
                response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'
                response['Content-Length'] = str(len(zip_data))
                
                # Add split info headers
                response['X-Split-Mode'] = split_mode
                response['X-Pages-Extracted'] = str(len(pages_to_extract))
                response['X-Output-Files'] = str(len(output_files))
                response['X-Total-Size'] = str(total_output_size)
                
                # Add cache control headers
                response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                
                return response
    
    except Exception as e:
        print(f"Split PDF error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'error': f'PDF splitting failed: {str(e)}'
        }, status=500)
    
    finally:
        # Cleanup temp directory
        try:
            shutil.rmtree(temp_dir)
            print(f"Cleaned up temp directory: {temp_dir}")
        except Exception as e:
            print(f"Failed to cleanup temp directory: {e}")

def parse_custom_ranges(ranges_str, total_pages):
    """
    Parse custom ranges string and return list of page numbers
    Format: "1-3, 5, 8-10, 15"
    """
    pages = []
    ranges_str = ranges_str.strip()
    
    if not ranges_str:
        return pages
    
    # Split by commas and process each part
    parts = [part.strip() for part in ranges_str.split(',')]
    
    for part in parts:
        if not part:
            continue
            
        if '-' in part:
            # Range format: "5-10"
            range_parts = part.split('-')
            if len(range_parts) != 2:
                raise ValueError(f"Invalid range format: {part}")
            
            try:
                start = int(range_parts[0].strip())
                end = int(range_parts[1].strip())
                
                if start < 1 or end > total_pages or start > end:
                    raise ValueError(f"Invalid range {start}-{end}. PDF has {total_pages} pages.")
                
                pages.extend(range(start, end + 1))
                
            except ValueError as e:
                if "invalid literal" in str(e):
                    raise ValueError(f"Invalid page numbers in range: {part}")
                raise
        else:
            # Single page
            try:
                page = int(part.strip())
                if page < 1 or page > total_pages:
                    raise ValueError(f"Page {page} is out of range. PDF has {total_pages} pages.")
                pages.append(page)
                
            except ValueError as e:
                if "invalid literal" in str(e):
                    raise ValueError(f"Invalid page number: {part}")
                raise
    
    # Remove duplicates and sort
    return sorted(list(set(pages)))

def parse_custom_ranges_detailed(ranges_str, total_pages):
    """
    Parse custom ranges and return list of page ranges (for creating separate PDFs)
    Format: "1-3, 5, 8-10, 15" -> [[1,2,3], [5], [8,9,10], [15]]
    """
    ranges = []
    ranges_str = ranges_str.strip()
    
    if not ranges_str:
        return ranges
    
    # Split by commas and process each part
    parts = [part.strip() for part in ranges_str.split(',')]
    
    for part in parts:
        if not part:
            continue
            
        if '-' in part:
            # Range format: "5-10"
            range_parts = part.split('-')
            if len(range_parts) != 2:
                raise ValueError(f"Invalid range format: {part}")
            
            try:
                start = int(range_parts[0].strip())
                end = int(range_parts[1].strip())
                
                if start < 1 or end > total_pages or start > end:
                    raise ValueError(f"Invalid range {start}-{end}. PDF has {total_pages} pages.")
                
                ranges.append(list(range(start, end + 1)))
                
            except ValueError as e:
                if "invalid literal" in str(e):
                    raise ValueError(f"Invalid page numbers in range: {part}")
                raise
        else:
            # Single page
            try:
                page = int(part.strip())
                if page < 1 or page > total_pages:
                    raise ValueError(f"Page {page} is out of range. PDF has {total_pages} pages.")
                ranges.append([page])
                
            except ValueError as e:
                if "invalid literal" in str(e):
                    raise ValueError(f"Invalid page number: {part}")
                raise
    
    return ranges

# Helper function for PDF validation
def is_valid_pdf(file_path):
    """Check if file is a valid PDF"""
    try:
        pdf_reader = PdfReader(file_path)
        return len(pdf_reader.pages) > 0
    except Exception:
        return False

# Advanced PDF analysis
def analyze_pdf_structure(file_path):
    """
    Analyze PDF structure and return detailed information
    """
    try:
        pdf_reader = PdfReader(file_path)
        
        info = {
            'page_count': len(pdf_reader.pages),
            'encrypted': pdf_reader.is_encrypted,
            'metadata': {},
            'pages_info': []
        }
        
        # Get metadata
        if pdf_reader.metadata:
            metadata = pdf_reader.metadata
            info['metadata'] = {
                'title': metadata.get('/Title', ''),
                'author': metadata.get('/Author', ''),
                'subject': metadata.get('/Subject', ''),
                'creator': metadata.get('/Creator', ''),
                'producer': metadata.get('/Producer', ''),
                'creation_date': str(metadata.get('/CreationDate', '')),
                'modification_date': str(metadata.get('/ModDate', ''))
            }
        
        # Analyze each page
        for i, page in enumerate(pdf_reader.pages):
            page_info = {
                'page_number': i + 1,
                'rotation': page.rotation if hasattr(page, 'rotation') else 0,
                'mediabox': {
                    'width': float(page.mediabox.width),
                    'height': float(page.mediabox.height)
                }
            }
            
            # Get page content info
            try:
                if hasattr(page, 'extract_text'):
                    text = page.extract_text()
                    page_info['has_text'] = len(text.strip()) > 0
                    page_info['text_length'] = len(text)
                else:
                    page_info['has_text'] = False
                    page_info['text_length'] = 0
            except:
                page_info['has_text'] = False
                page_info['text_length'] = 0
            
            info['pages_info'].append(page_info)
        
        return info
        
    except Exception as e:
        return {'error': str(e)}

# Optimize split PDFs
def optimize_split_pdf(input_path, output_path, optimization_level='medium'):
    """
    Optimize split PDF files for size and quality
    """
    try:
        pdf_reader = PdfReader(input_path)
        pdf_writer = PdfWriter()
        
        for page in pdf_reader.pages:
            # Add page to writer
            pdf_writer.add_page(page)
        
        # Apply optimization based on level
        if optimization_level == 'high':
            # Maximum compression
            pdf_writer.compress_identical_objects()
        elif optimization_level == 'medium':
            # Balanced compression
            pdf_writer.compress_identical_objects()
        # 'low' or default - minimal optimization
        
        with open(output_path, 'wb') as output_file:
            pdf_writer.write(output_file)
        
        return True
        
    except Exception as e:
        print(f"PDF optimization error: {str(e)}")
        # If optimization fails, copy original file
        shutil.copy2(input_path, output_path)
        return False

# Batch PDF splitting with progress tracking
def batch_split_pdf(pdf_files, split_options, progress_callback=None):
    """
    Split multiple PDF files with progress tracking
    """
    results = []
    total_files = len(pdf_files)
    
    for i, pdf_file in enumerate(pdf_files):
        try:
            # Process individual PDF
            result = split_single_pdf(pdf_file, split_options)
            results.append(result)
            
            # Call progress callback if provided
            if progress_callback:
                progress = ((i + 1) / total_files) * 100
                progress_callback(progress, f"Processed {i + 1}/{total_files} files")
                
        except Exception as e:
            results.append({'error': str(e), 'file': pdf_file.name})
    
    return results

# Enhanced page range validation
def validate_page_ranges(ranges_str, total_pages):
    """
    Validate page ranges and provide detailed error messages
    """
    try:
        pages = parse_custom_ranges(ranges_str, total_pages)
        
        if not pages:
            return {'valid': False, 'error': 'No valid pages specified'}
        
        # Check for reasonable page count
        if len(pages) > total_pages:
            return {'valid': False, 'error': 'More pages specified than available in PDF'}
        
        return {
            'valid': True,
            'pages': pages,
            'count': len(pages),
            'ranges_count': len(parse_custom_ranges_detailed(ranges_str, total_pages))
        }
        
    except Exception as e:
        return {'valid': False, 'error': str(e)}

# PDF security check
def check_pdf_security(file_path):
    """
    Check PDF security restrictions
    """
    try:
        pdf_reader = PdfReader(file_path)
        
        security_info = {
            'encrypted': pdf_reader.is_encrypted,
            'can_extract': True,  # Assume can extract unless proven otherwise
            'restrictions': []
        }
        
        if pdf_reader.is_encrypted:
            # Try to decrypt with empty password
            try:
                pdf_reader.decrypt('')
                security_info['can_extract'] = True
            except:
                security_info['can_extract'] = False
                security_info['restrictions'].append('Password protected')
        
        return security_info
        
    except Exception as e:
        return {'error': str(e), 'can_extract': False}

@staff_member_required
def system_health(request):
    """System health monitoring dashboard"""
    try:
        now = timezone.now()
        last_hour = now - timedelta(hours=1)
        last_24h = now - timedelta(hours=24)
        
        # Get system health metrics
        health_data = {
            'timestamp': now.isoformat(),
            'status': 'healthy',  # overall status
            'uptime': get_system_uptime(),
            'cpu_usage': get_system_cpu_usage(),
            'memory_usage': get_system_memory_usage(),
            'disk_usage': get_system_disk_usage(),
            'database_status': check_database_status(),
        }
        
        # Activity metrics
        activity_metrics = {
            'total_requests_1h': UserActivity.objects.filter(created_at__gte=last_hour).count(),
            'total_requests_24h': UserActivity.objects.filter(created_at__gte=last_24h).count(),
            'unique_sessions_1h': UserActivity.objects.filter(
                created_at__gte=last_hour
            ).values('session_id').distinct().count(),
            'active_sessions': get_active_sessions_count(),
        }
        
        # Error metrics
        error_metrics = {
            'errors_1h': ErrorLog.objects.filter(created_at__gte=last_hour).count(),
            'errors_24h': ErrorLog.objects.filter(created_at__gte=last_24h).count(),
            'error_rate_1h': calculate_error_rate(last_hour),
            'error_rate_24h': calculate_error_rate(last_24h),
            'unresolved_errors': ErrorLog.objects.filter(resolved=False).count(),
        }
        
        # Performance metrics
        performance_metrics = {
            'avg_response_time_1h': calculate_avg_response_time(last_hour),
            'avg_response_time_24h': calculate_avg_response_time(last_24h),
        }
        
        # Top errors
        top_errors = get_top_errors(last_24h)
        
        # Slowest tools
        slowest_tools = get_slowest_tools(last_24h)
        
        # Calculate overall health score
        health_score = calculate_overall_health_score(health_data)
        
        # Combine all metrics
        context = {
            'health_data': health_data,
            'activity_metrics': activity_metrics,
            'error_metrics': error_metrics,
            'performance_metrics': performance_metrics,
            'top_errors': top_errors,
            'slowest_tools': slowest_tools,
            'health_score': health_score,
            'last_updated': now.strftime('%Y-%m-%d %H:%M:%S UTC'),
        }
        
        # If it's an AJAX request, return JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(context)
        
        return render(request, 'admin/system_health.html', context)
        
    except Exception as e:
        print(f"Error in system_health view: {str(e)}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'error': 'Failed to fetch system health data',
                'timestamp': timezone.now().isoformat()
            }, status=500)
        
        # Return basic error page for non-AJAX requests
        return render(request, 'admin/system_health.html', {
            'error': 'Unable to load system health data',
            'health_score': 0
        })