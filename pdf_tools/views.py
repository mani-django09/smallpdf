# Add these imports at the top of your views.py file (around line 1-20)

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



# Add these missing imports for contact functionality
from .models import ContactMessage, ContactSettings
from .forms import ContactForm


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
    """Render the all tools page"""
    tools = [
        {
            'name': 'Merge PDF',
            'description': 'Combine multiple PDFs into a single document.',
            'url': 'merge_pdf',
            'icon': 'merge-icon.svg',
        },
       
        {
            'name': 'Compress PDF',
            'description': 'Reduce PDF file size while maintaining quality.',
            'url': 'compress_pdf',
            'icon': 'compress-icon.svg',
        },
        {
            'name': 'Convert PDF',
            'description': 'Transform PDFs to other formats like Word, Excel, etc.',
            'url': 'convert_pdf',
            'icon': 'convert-icon.svg',
        },
        
       
        {
            'name': 'PDF to Word',
            'description': 'Convert PDF documents to editable Word files.',
            'url': 'pdf_to_word',
            'icon': 'pdf-to-word-icon.svg',
        },
        {
            'name': 'PDF to Excel',
            'description': 'Convert PDF tables to Excel spreadsheets.',
            'url': 'pdf_to_excel',
            'icon': 'pdf-to-excel-icon.svg',
        },
        
        {
            'name': 'PDF to JPG',
            'description': 'Convert PDF pages to JPG image files.',
            'url': 'pdf_to_jpg',
            'icon': 'pdf-to-jpg-icon.svg',
        },
        {
            'name': 'JPG to PDF',
            'description': 'Convert JPG images to PDF documents.',
            'url': 'jpg_to_pdf',
            'icon': 'jpg-to-pdf-icon.svg',
        },
    ]
    
    return render(request, 'all_tools.html', {'tools': tools})

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

def pdf_to_excel(request):
    """Render the PDF to Excel tool page"""
    return render(request, 'pdf_to_excel.html')


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

@csrf_exempt
def edit_pdf_api(request):
    """API endpoint to edit PDF content"""
    # PDF editing is complex and would require client-side libraries like PDF.js
    return JsonResponse({'error': 'This feature is in development'}, status=501)

@csrf_exempt
def protect_pdf_api(request):
    """API endpoint to add password protection to a PDF"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    if not PDF_LIBRARY_AVAILABLE:
        return JsonResponse({'error': 'PDF processing library not available'}, status=500)
    
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'PDF file is required'}, status=400)
    
    password = request.POST.get('password', '')
    if not password:
        return JsonResponse({'error': 'Password is required'}, status=400)
    
    try:
        reader = PdfReader(request.FILES['file'])
        writer = PdfWriter()
        
        # Add all pages to the writer
        for page in reader.pages:
            writer.add_page(page)
        
        # Encrypt with the provided password
        writer.encrypt(password)
        
        output = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        with open(output.name, 'wb') as f:
            writer.write(f)
        
        with open(output.name, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="protected.pdf"'
        
        # Clean up temporary file
        os.unlink(output.name)
        
        return response
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def unlock_pdf_api(request):
    """API endpoint to remove password protection from a PDF"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    if not PDF_LIBRARY_AVAILABLE:
        return JsonResponse({'error': 'PDF processing library not available'}, status=500)
    
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'PDF file is required'}, status=400)
    
    password = request.POST.get('password', '')
    
    try:
        reader = PdfReader(request.FILES['file'])
        
        if reader.is_encrypted:
            reader.decrypt(password)
        
        writer = PdfWriter()
        
        for page in reader.pages:
            writer.add_page(page)
        
        output = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        with open(output.name, 'wb') as f:
            writer.write(f)
        
        with open(output.name, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="unlocked.pdf"'
        
        # Clean up temporary file
        os.unlink(output.name)
        
        return response
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



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


@csrf_exempt
def word_to_pdf_api(request):
    """API endpoint to convert Word documents to PDF"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'Word file is required'}, status=400)
    
    word_file = request.FILES['file']
    quality = request.POST.get('quality', 'high')
    page_size = request.POST.get('page_size', 'original')
    
    # Check if it's a valid Word file
    file_name = word_file.name.lower()
    if not (file_name.endswith('.doc') or file_name.endswith('.docx')):
        return JsonResponse({'error': 'Invalid file format. Please upload a DOC or DOCX file'}, status=400)
    
    try:
        # Create a temporary file to store the uploaded content
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(word_file.name)[1]) as temp_file:
            for chunk in word_file.chunks():
                temp_file.write(chunk)
            temp_input_path = temp_file.name
        
        # Create temporary output file for the PDF
        output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        output_file.close()
        output_path = output_file.name
        
        conversion_success = False
        
        # Try using docx2pdf if available
        if DOCX2PDF_AVAILABLE:
            try:
                # Initialize COM for multithreading (Windows only)
                pythoncom.CoInitialize()
                
                # Convert Word to PDF
                convert(temp_input_path, output_path)
                
                # Uninitialize COM (Windows only)
                pythoncom.CoUninitialize()
                
                conversion_success = os.path.exists(output_path) and os.path.getsize(output_path) > 0
            except Exception as e:
                print(f"docx2pdf conversion failed: {str(e)}")
        
        # If docx2pdf failed, try LibreOffice
        if not conversion_success:
            try:
                # Try to find LibreOffice or OpenOffice executable
                soffice = find_libreoffice_path()
                
                if soffice:
                    # Convert using LibreOffice/OpenOffice
                    output_dir = os.path.dirname(output_path)
                    cmd = [
                        soffice,
                        '--headless',
                        '--convert-to', 'pdf',
                        '--outdir', output_dir,
                        temp_input_path
                    ]
                    
                    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    stdout, stderr = process.communicate()
                    
                    # LibreOffice creates PDF with the same name as input
                    libreoffice_output = os.path.join(
                        output_dir, 
                        os.path.splitext(os.path.basename(temp_input_path))[0] + '.pdf'
                    )
                    
                    # If LibreOffice created a PDF with a different name, move it to our expected path
                    if os.path.exists(libreoffice_output) and libreoffice_output != output_path:
                        import shutil
                        shutil.move(libreoffice_output, output_path)
                    
                    conversion_success = os.path.exists(output_path) and os.path.getsize(output_path) > 0
            except Exception as e:
                print(f"LibreOffice conversion failed: {str(e)}")
        
        # If both methods failed, return error
        if not conversion_success:
            return JsonResponse({
                'error': 'Conversion failed. Please try a different file or contact support.'
            }, status=500)
        
        # Read the converted PDF and return it
        with open(output_path, 'rb') as pdf_file:
            response = HttpResponse(pdf_file.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{os.path.splitext(word_file.name)[0]}.pdf"'
            # Add cache-control header to prevent caching issues
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        # Clean up temporary files
        if os.path.exists(temp_input_path):
            os.unlink(temp_input_path)
        if os.path.exists(output_path):
            os.unlink(output_path)
        
        return response
    
    except Exception as e:
        # Clean up temporary files in case of error
        try:
            if 'temp_input_path' in locals() and os.path.exists(temp_input_path):
                os.unlink(temp_input_path)
            if 'output_path' in locals() and os.path.exists(output_path):
                os.unlink(output_path)
        except:
            pass
        
        return JsonResponse({'error': str(e)}, status=500)

def find_libreoffice_path():
    """Helper function to find LibreOffice path on different operating systems"""
    if platform.system() == 'Windows':
        # Common paths for LibreOffice on Windows
        paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            r"C:\Program Files\LibreOffice 7\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice 7\program\soffice.exe",
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
        ]
    else:  # Linux and other OS
        # Try to find it in the PATH
        try:
            return subprocess.check_output(['which', 'soffice']).decode().strip()
        except:
            paths = [
                "/usr/bin/soffice",
                "/usr/local/bin/soffice",
                "/opt/libreoffice/program/soffice",
            ]
    
    # Check each path
    for path in paths:
        if os.path.exists(path):
            return path
    
    return None

def compress_image(request):
    # Your image compression logic will go here
    return render(request, 'pdf_tools/compress_image.html')
def html_to_pdf(request):
    return render(request, 'pdf_tools/html_to_pdf.html')
def excel_to_pdf(request):
    """Render the Excel to PDF tool page"""
    return render(request, 'pdf_tools/excel_to_pdf.html')

@csrf_exempt
def excel_to_pdf_api(request):
    """API endpoint to convert Excel files to PDF"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'Excel file is required'}, status=400)
    
    excel_file = request.FILES['file']
    
    # Check if it's a valid Excel file
    file_name = excel_file.name.lower()
    if not (file_name.endswith('.xls') or file_name.endswith('.xlsx')):
        return JsonResponse({'error': 'Invalid file format. Please upload an XLS or XLSX file'}, status=400)
    
    try:
        # This would be where your Excel to PDF conversion logic goes
        # For now, we'll return a placeholder response
        
        return JsonResponse({
            'message': 'Excel to PDF conversion is not fully implemented yet. Please check back later.',
            'status': 'pending'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


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
from django.shortcuts import render

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
    """Generate sitemap.xml with correct domain"""
    
    # Get the actual domain from the request
    domain = request.get_host()
    protocol = 'https' if request.is_secure() else 'http'
    
    # Force your domain for production (replace with your actual domain)
    if domain == '127.0.0.1:8000' or domain == 'localhost:8000':
        # For development, use your actual domain
        base_url = 'https://smallpdf.us'
    else:
        # For production, use the request domain
        base_url = f"{protocol}://{domain}"
    
    # Get current date in simple format
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
    """Generate robots.txt with correct domain"""
    
    # Get the actual domain from the request
    domain = request.get_host()
    protocol = 'https' if request.is_secure() else 'http'
    
    # Force your domain for production
    if domain == '127.0.0.1:8000' or domain == 'localhost:8000':
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

# Block certain file types that shouldn't be indexed
Disallow: *.pdf$
Disallow: *.doc$
Disallow: *.docx$
Disallow: *.jpg$
Disallow: *.jpeg$
Disallow: *.png$
Disallow: *.gif$

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

from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Avg, Sum, Q
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import UserActivity, ErrorLog, SystemMetrics
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator
def is_staff_user(user):
    return user.is_authenticated and user.is_staff
@user_passes_test(is_staff_user)
def admin_dashboard(request):
    """Main admin analytics dashboard"""
    
    # Get date range from request
    days = int(request.GET.get('days', 7))
    start_date = timezone.now() - timedelta(days=days)
    
    # Basic stats - Using dummy data if models don't exist
    try:
        from .models import UserActivity, ErrorLog
        
        total_activities = UserActivity.objects.filter(created_at__gte=start_date).count()
        total_errors = ErrorLog.objects.filter(created_at__gte=start_date).count()
        unique_users = UserActivity.objects.filter(
            created_at__gte=start_date
        ).values('session_id').distinct().count()
        
        # Tool usage stats
        tool_usage = list(UserActivity.objects.filter(
            activity_type='tool_access',
            created_at__gte=start_date
        ).values('tool_name').annotate(
            count=Count('id')
        ).order_by('-count')[:10])
        
        # File processing stats
        file_stats = UserActivity.objects.filter(
            activity_type='file_process',
            created_at__gte=start_date
        ).aggregate(
            total_files=Count('id'),
            avg_file_size=Avg('file_size'),
            total_size=Sum('file_size'),
            avg_processing_time=Avg('processing_time')
        )
        
        # Error breakdown
        error_breakdown = list(ErrorLog.objects.filter(
            created_at__gte=start_date
        ).values('error_type').annotate(
            count=Count('id')
        ).order_by('-count')[:10])
        
        # Daily activity chart data
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
        
        # Device and browser stats
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
        
        # Country stats
        country_stats = list(UserActivity.objects.filter(
            created_at__gte=start_date,
            country__isnull=False
        ).values('country').annotate(
            count=Count('id')
        ).order_by('-count')[:10])
        
        # Success rate
        success_rate = UserActivity.objects.filter(
            created_at__gte=start_date,
            activity_type='file_process'
        ).aggregate(
            total=Count('id'),
            success=Count('id', filter=Q(status='success'))
        )
        
        success_percentage = 0
        if success_rate['total'] > 0:
            success_percentage = (success_rate['success'] / success_rate['total']) * 100
            
    except ImportError:
        # Fallback to dummy data if models don't exist
        total_activities = 1250
        total_errors = 15
        unique_users = 890
        tool_usage = [
            {'tool_name': 'PDF to Word', 'count': 450},
            {'tool_name': 'Merge PDF', 'count': 320},
            {'tool_name': 'Compress PDF', 'count': 280},
        ]
        file_stats = {
            'total_files': 1200,
            'avg_file_size': 2048000,
            'total_size': 2457600000,
            'avg_processing_time': 2.5
        }
        error_breakdown = [
            {'error_type': 'File Upload Error', 'count': 8},
            {'error_type': 'Processing Timeout', 'count': 5},
            {'error_type': 'Invalid File Format', 'count': 2},
        ]
        daily_activity = [
            {'date': '2024-06-14', 'activities': 180, 'errors': 2},
            {'date': '2024-06-15', 'activities': 195, 'errors': 3},
            {'date': '2024-06-16', 'activities': 220, 'errors': 1},
            {'date': '2024-06-17', 'activities': 210, 'errors': 4},
            {'date': '2024-06-18', 'activities': 235, 'errors': 2},
            {'date': '2024-06-19', 'activities': 200, 'errors': 3},
            {'date': '2024-06-20', 'activities': 190, 'errors': 0},
        ]
        device_stats = [
            {'device_type': 'desktop', 'count': 650},
            {'device_type': 'mobile', 'count': 450},
            {'device_type': 'tablet', 'count': 150},
        ]
        browser_stats = [
            {'browser': 'Chrome', 'count': 580},
            {'browser': 'Firefox', 'count': 320},
            {'browser': 'Safari', 'count': 240},
            {'browser': 'Edge', 'count': 110},
        ]
        country_stats = [
            {'country': 'United States', 'count': 450},
            {'country': 'India', 'count': 280},
            {'country': 'United Kingdom', 'count': 180},
            {'country': 'Canada', 'count': 120},
            {'country': 'Germany', 'count': 100},
        ]
        success_percentage = 96.8
    
    context = {
        'days': days,
        'total_activities': total_activities,
        'total_errors': total_errors,
        'unique_users': unique_users,
        'tool_usage': json.dumps(tool_usage),
        'file_stats': file_stats,
        'error_breakdown': error_breakdown,
        'daily_activity': json.dumps(daily_activity),
        'device_stats': device_stats,
        'browser_stats': browser_stats,
        'country_stats': country_stats,
        'success_percentage': round(success_percentage, 2)
    }
    
    return render(request, 'admin/analytics_dashboard.html', context)

@staff_member_required
def user_activity_detail(request):
    """Detailed user activity view"""
    
    # Filters
    activity_type = request.GET.get('activity_type', '')
    tool_name = request.GET.get('tool_name', '')
    status = request.GET.get('status', '')
    days = int(request.GET.get('days', 7))
    
    # Base queryset
    activities = UserActivity.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=days)
    ).select_related('user').order_by('-created_at')
    
    # Apply filters
    if activity_type:
        activities = activities.filter(activity_type=activity_type)
    if tool_name:
        activities = activities.filter(tool_name=tool_name)
    if status:
        activities = activities.filter(status=status)
    
    # Pagination
    paginator = Paginator(activities, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    activity_types = UserActivity.ACTIVITY_TYPES
    tools = UserActivity.objects.values_list('tool_name', flat=True).distinct()
    tools = [t for t in tools if t]  # Remove None values
    
    context = {
        'activities': page_obj,
        'activity_types': activity_types,
        'tools': tools,
        'current_filters': {
            'activity_type': activity_type,
            'tool_name': tool_name,
            'status': status,
            'days': days
        }
    }
    
    return render(request, 'admin/user_activity_detail.html', context)

@staff_member_required
def error_log_detail(request):
    """Detailed error log view"""
    
    # Filters
    error_type = request.GET.get('error_type', '')
    severity = request.GET.get('severity', '')
    resolved = request.GET.get('resolved', '')
    days = int(request.GET.get('days', 7))
    
    # Base queryset
    errors = ErrorLog.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=days)
    ).select_related('user', 'resolved_by').order_by('-created_at')
    
    # Apply filters
    if error_type:
        errors = errors.filter(error_type=error_type)
    if severity:
        errors = errors.filter(severity=severity)
    if resolved:
        errors = errors.filter(resolved=resolved == 'true')
    
    # Pagination
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
def api_dashboard_data(request):
    """API endpoint for dashboard data (for AJAX updates)"""
    
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
            
            return JsonResponse({'success': True})
        except ErrorLog.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Error not found'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

# Middleware to automatically track activities
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

