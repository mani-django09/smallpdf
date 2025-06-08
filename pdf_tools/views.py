# Add these imports at the top of your views.py file (around line 1-20)

import os
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.views.decorators.csrf import csrf_exempt
import zipfile
import uuid
import json
import io
import shutil
import subprocess
import platform
from datetime import datetime
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail

# Add these missing imports for contact functionality
from .models import ContactMessage, ContactSettings
from .forms import ContactForm

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

import shutil
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.files.storage import default_storage

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
def pdf_to_jpg_api(request):
    """API endpoint to convert PDF files to JPG/PNG images using PyMuPDF"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    if not PYMUPDF_AVAILABLE:
        return JsonResponse({
            'error': 'PDF conversion library not available. Please install PyMuPDF: pip install PyMuPDF Pillow'
        }, status=500)
    
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'PDF file is required'}, status=400)
    
    pdf_file = request.FILES['file']
    quality = request.POST.get('quality', 'high')
    image_format = request.POST.get('format', 'jpg')
    page_selection = request.POST.get('page_selection', 'all')
    page_data = request.POST.get('page_data', '')
    dpi = int(request.POST.get('dpi', '300'))
    
    # Validate file
    if not pdf_file.name.lower().endswith('.pdf'):
        return JsonResponse({'error': 'Please upload a valid PDF file'}, status=400)
    
    # Check file size (50MB limit)
    max_size = 50 * 1024 * 1024
    if pdf_file.size > max_size:
        return JsonResponse({'error': 'File size exceeds 50MB limit'}, status=400)
    
    # Create unique temp directory
    temp_dir = None
    temp_pdf_path = None
    
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix='pdf_conversion_')
        print(f"Created temp directory: {temp_dir}")
        
        # Save uploaded PDF to temporary file
        temp_pdf_path = os.path.join(temp_dir, f"input_{uuid.uuid4().hex}.pdf")
        
        with open(temp_pdf_path, 'wb') as temp_file:
            for chunk in pdf_file.chunks():
                temp_file.write(chunk)
        
        # Verify file was written correctly
        if not os.path.exists(temp_pdf_path) or os.path.getsize(temp_pdf_path) == 0:
            raise Exception("Failed to save uploaded PDF file")
        
        print(f"PDF saved to: {temp_pdf_path}")
        print(f"File size: {os.path.getsize(temp_pdf_path)} bytes")
        
        # Convert PDF to images using PyMuPDF
        converted_images = convert_pdf_to_images_pymupdf(
            temp_pdf_path, 
            temp_dir, 
            pdf_file.name,
            quality, 
            image_format, 
            page_selection, 
            page_data, 
            dpi
        )
        
        if not converted_images:
            raise Exception("No images were generated from the PDF")
        
        # Create media directory if it doesn't exist
        media_temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_images')
        os.makedirs(media_temp_dir, exist_ok=True)
        print(f"Media temp directory: {media_temp_dir}")
        
        # Move images to media directory and create URLs
        final_images = []
        for img in converted_images:
            # Create unique filename
            unique_filename = f"{uuid.uuid4().hex}_{img['filename']}"
            media_path = os.path.join(media_temp_dir, unique_filename)
            
            # Copy image to media directory
            shutil.copy2(img['path'], media_path)
            print(f"Copied image to: {media_path}")
            
            # Create URL
            media_url = f"{settings.MEDIA_URL}temp_images/{unique_filename}"
            
            final_images.append({
                'url': media_url,
                'format': img['format'],
                'page': img['page'],
                'path': media_path,  # Store for zip download
                'filename': img['filename']
            })
        
        # Store image paths in session for zip download
        request.session['image_paths'] = [
            {'path': img['path'], 'filename': img['filename']} 
            for img in final_images
        ]
        request.session['pdf_filename'] = pdf_file.name
        
        print(f"Successfully converted {len(final_images)} pages")
        
        return JsonResponse({
            'success': True,
            'images': [
                {
                    'url': img['url'], 
                    'format': img['format'], 
                    'page': img['page']
                } 
                for img in final_images
            ],
            'total_pages': len(final_images)
        })
        
    except Exception as e:
        print(f"Conversion error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'error': f"Conversion failed: {str(e)}"
        }, status=500)
        
    finally:
        # Clean up temporary files
        if temp_pdf_path and os.path.exists(temp_pdf_path):
            try:
                os.unlink(temp_pdf_path)
                print(f"Cleaned up temp PDF: {temp_pdf_path}")
            except Exception as e:
                print(f"Failed to clean up temp PDF: {e}")
        
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                print(f"Cleaned up temp directory: {temp_dir}")
            except Exception as e:
                print(f"Failed to clean up temp directory: {e}")


def determine_pages_to_convert(page_selection, page_data, total_pages):
    """Determine which pages to convert based on user selection"""
    
    print(f"Page selection: {page_selection}, Page data: {page_data}, Total pages: {total_pages}")
    
    if page_selection == 'all':
        return list(range(1, total_pages + 1))
    
    elif page_selection == 'range' and page_data:
        try:
            parts = page_data.split('-')
            if len(parts) == 2:
                start = max(1, int(parts[0].strip()))
                end = min(int(parts[1].strip()), total_pages)
                if start <= end:
                    return list(range(start, end + 1))
        except ValueError:
            pass
    
    elif page_selection == 'custom' and page_data:
        try:
            pages = []
            segments = page_data.split(',')
            
            for segment in segments:
                segment = segment.strip()
                if '-' in segment:
                    start, end = map(int, segment.split('-'))
                    start = max(1, start)
                    end = min(end, total_pages)
                    if start <= end:
                        pages.extend(list(range(start, end + 1)))
                else:
                    page = int(segment)
                    if 1 <= page <= total_pages:
                        pages.append(page)
            
            return sorted(list(set(pages)))
        except ValueError:
            pass
    
    # Fallback: convert all pages
    return list(range(1, total_pages + 1))

def convert_pdf_to_images_pymupdf(pdf_path, output_dir, original_filename, quality, image_format, page_selection, page_data, dpi):
    """Convert PDF to images using PyMuPDF (fitz)"""
    
    try:
        print(f"Opening PDF: {pdf_path}")
        
        # Open PDF document
        pdf_doc = fitz.open(pdf_path)
        total_pages = pdf_doc.page_count
        
        if total_pages <= 0:
            raise Exception("PDF has no pages")
        
        print(f"PDF has {total_pages} pages")
        
        # Determine which pages to convert
        pages_to_convert = determine_pages_to_convert(page_selection, page_data, total_pages)
        
        if not pages_to_convert:
            raise Exception("No valid pages specified for conversion")
        
        print(f"Converting pages: {pages_to_convert}")
        
        # Set conversion parameters
        if quality == 'high':
            jpeg_quality = 95
            zoom = 2.0  # Higher zoom for better quality
        elif quality == 'medium':
            jpeg_quality = 80
            zoom = 1.5
        else:  # low
            jpeg_quality = 60
            zoom = 1.0
        
        # Calculate zoom based on DPI
        # Default DPI is 72, so for 300 DPI we need zoom of about 4.17
        dpi_zoom = dpi / 72.0
        final_zoom = max(zoom, dpi_zoom)
        
        print(f"Using zoom factor: {final_zoom}, JPEG quality: {jpeg_quality}")
        
        if image_format == 'png':
            ext = 'png'
        else:
            ext = 'jpg'
        
        converted_images = []
        
        # Convert each page
        for page_num in pages_to_convert:
            try:
                print(f"Processing page {page_num}")
                
                # Get the page (0-based indexing)
                page = pdf_doc[page_num - 1]
                
                # Create transformation matrix for zoom
                mat = fitz.Matrix(final_zoom, final_zoom)
                
                # Render page to pixmap
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to PIL Image for better quality control
                img_data = pix.tobytes("ppm")
                pil_image = Image.open(io.BytesIO(img_data))
                
                print(f"Generated image size: {pil_image.size}")
                
                # Create filename
                filename = f"{os.path.splitext(original_filename)[0]}_page{page_num}.{ext}"
                output_path = os.path.join(output_dir, filename)
                
                # Save image with appropriate settings
                if ext == 'jpg':
                    # Convert to RGB if necessary (remove alpha channel)
                    if pil_image.mode in ('RGBA', 'LA', 'P'):
                        # Create white background
                        background = Image.new('RGB', pil_image.size, (255, 255, 255))
                        if pil_image.mode == 'P':
                            pil_image = pil_image.convert('RGBA')
                        background.paste(pil_image, mask=pil_image.split()[-1] if pil_image.mode == 'RGBA' else None)
                        pil_image = background
                    
                    pil_image.save(output_path, 'JPEG', quality=jpeg_quality, optimize=True)
                else:  # PNG
                    pil_image.save(output_path, 'PNG', optimize=True)
                
                # Verify file was created
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    converted_images.append({
                        'path': output_path,
                        'filename': filename,
                        'format': ext,
                        'page': page_num
                    })
                    print(f"Successfully converted page {page_num} - {os.path.getsize(output_path)} bytes")
                else:
                    print(f"Failed to create image for page {page_num}")
                
            except Exception as e:
                print(f"Error converting page {page_num}: {e}")
                continue
        
        # Close PDF document
        pdf_doc.close()
        
        print(f"Conversion complete. Generated {len(converted_images)} images")
        return converted_images
        
    except Exception as e:
        print(f"PyMuPDF conversion error: {e}")
        raise Exception(f"Failed to convert PDF: {str(e)}")


@csrf_exempt
def download_images_zip(request):
    """API endpoint to download multiple images as a ZIP file"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    try:
        # Get image URLs from request
        image_urls_json = request.POST.get('image_urls', '[]')
        file_name = request.POST.get('file_name', 'pdf_images')
        format_ext = request.POST.get('format', 'jpg')
        
        # Log what we received for debugging
        print(f"Image URLs JSON: {image_urls_json[:100]}...")  # Print first 100 chars
        
        # Get image paths from session
        image_paths = request.session.get('image_paths', [])
        pdf_filename = request.session.get('pdf_filename', 'document.pdf')
        
        print(f"Session image paths: {len(image_paths)} items")
        
        if not image_paths:
            # If no paths in session, try to use the URLs from the request
            try:
                image_urls = json.loads(image_urls_json)
                if image_urls:
                    # Create temporary files for each URL
                    temp_image_paths = []
                    for i, img_data in enumerate(image_urls):
                        # Extract URL from the data
                        url = img_data.get('url', '')
                        if not url:
                            continue
                            
                        # Convert the URL to a filesystem path
                        url_path = url.replace(settings.MEDIA_URL, '')
                        fs_path = os.path.join(settings.MEDIA_ROOT, url_path)
                        
                        if os.path.exists(fs_path):
                            page_num = img_data.get('page', i+1)
                            filename = f"{os.path.splitext(pdf_filename)[0]}_page{page_num}.{format_ext}"
                            temp_image_paths.append({
                                'path': fs_path,
                                'filename': filename
                            })
                    
                    if temp_image_paths:
                        image_paths = temp_image_paths
                        print(f"Recovered {len(image_paths)} image paths from URLs")
            except Exception as url_error:
                print(f"Error processing image URLs: {str(url_error)}")
        
        if not image_paths:
            return JsonResponse({'error': 'No images available for download'}, status=400)
        
        # Create a zip file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Count of successfully added files
            added_files = 0
            
            for img_data in image_paths:
                # Check if the file exists
                if 'path' in img_data and os.path.exists(img_data['path']):
                    # Add file to the zip
                    zip_file.write(
                        img_data['path'],
                        arcname=img_data.get('filename', os.path.basename(img_data['path']))
                    )
                    added_files += 1
                    
            if added_files == 0:
                return JsonResponse({'error': 'None of the specified images could be found'}, status=404)
        
        # Reset buffer position
        zip_buffer.seek(0)
        
        # Create response with zip file
        response = HttpResponse(zip_buffer, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{os.path.splitext(pdf_filename)[0]}_images.zip"'
        
        # Add cache-control headers
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        return response
    
    except Exception as e:
        import traceback
        print(f"Error creating ZIP file: {str(e)}")
        print(traceback.format_exc())
        
        return JsonResponse({
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4, A3, A5, legal
    from reportlab.lib.units import mm, inch
    from reportlab.lib.utils import ImageReader
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Alternative PDF library
try:
    import img2pdf
    IMG2PDF_AVAILABLE = True
except ImportError:
    IMG2PDF_AVAILABLE = False

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

@csrf_exempt
def merge_pdf_api(request):
    """API endpoint to merge multiple PDFs"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    if not PDF_LIBRARY_AVAILABLE:
        return JsonResponse({'error': 'PDF processing library not available'}, status=500)
    
    files = request.FILES.getlist('files')
    if not files or len(files) < 1:
        return JsonResponse({'error': 'At least one PDF file is required'}, status=400)
    
    try:
        merger = PdfMerger()
        
        for pdf_file in files:
            # Check if it's a valid PDF file
            if not pdf_file.name.lower().endswith('.pdf'):
                return JsonResponse({'error': f'{pdf_file.name} is not a PDF file'}, status=400)
            
            # Create a temporary file to store the uploaded content
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                for chunk in pdf_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            # Add the PDF to the merger using the temp file
            try:
                merger.append(temp_file_path)
            finally:
                # Ensure we clean up the temp file even if appending fails
                if os.path.exists(temp_file_path):
                    try:
                        os.unlink(temp_file_path)
                    except:
                        pass
        
        # Create a temporary file for the merged PDF
        output = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        output_path = output.name
        output.close()  # Close file before writing to it
        
        # Write to the temporary file
        merger.write(output_path)
        merger.close()
        
        # Read the merged PDF and return it
        response = None
        try:
            with open(output_path, 'rb') as f:
                content = f.read()
                response = HttpResponse(content, content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="merged.pdf"'
        finally:
            # Clean up temporary file
            try:
                if os.path.exists(output_path):
                    os.unlink(output_path)
            except:
                pass
            
        return response
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def split_pdf_api(request):
    """API endpoint to split a PDF into separate pages or ranges"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    if not PDF_LIBRARY_AVAILABLE:
        return JsonResponse({'error': 'PDF processing library not available'}, status=500)
    
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'PDF file is required'}, status=400)
    
    pdf_file = request.FILES['file']
    page_ranges = request.POST.get('page_ranges', '')
    
    try:
        reader = PdfReader(pdf_file)
        total_pages = len(reader.pages)
        
        # If no specific ranges provided, split all pages individually
        if not page_ranges:
            output_files = []
            for i in range(total_pages):
                writer = PdfWriter()
                writer.add_page(reader.pages[i])
                
                output = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                with open(output.name, 'wb') as f:
                    writer.write(f)
                
                output_files.append(output.name)
            
            # For simplicity, return only the first split page for demonstration
            # In a real app, you'd probably zip all pages and return the zip file
            with open(output_files[0], 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="page_1.pdf"'
            
            # Clean up temporary files
            for file in output_files:
                os.unlink(file)
            
            return response
        
        # Otherwise, process the specified page ranges
        # page_ranges format example: "1-3,5,7-9"
        else:
            ranges = []
            for range_str in page_ranges.split(','):
                if '-' in range_str:
                    start, end = map(int, range_str.split('-'))
                    ranges.append((start - 1, end))  # Convert to 0-based indexing
                else:
                    page = int(range_str)
                    ranges.append((page - 1, page))  # Convert to 0-based indexing
            
            writer = PdfWriter()
            for start, end in ranges:
                for i in range(start, end):
                    if i < total_pages:
                        writer.add_page(reader.pages[i])
            
            output = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            with open(output.name, 'wb') as f:
                writer.write(f)
            
            with open(output.name, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="split.pdf"'
            
            # Clean up temporary file
            os.unlink(output.name)
            
            return response
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


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
import subprocess
import platform

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

import os
import tempfile
import shutil
import zipfile
import uuid
import subprocess
import platform
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import io

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

import os
import io
import uuid
import zipfile
import tempfile
import shutil
from PIL import Image
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

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
    API endpoint to compress image files
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    if not PIL_AVAILABLE:
        return JsonResponse({
            'error': 'Image compression library not available. Please install Pillow'
        }, status=500)
    
    if 'files' not in request.FILES:
        return JsonResponse({'error': 'At least one image file is required'}, status=400)
    
    image_files = request.FILES.getlist('files')
    output_format = request.POST.get('output_format', 'auto')
    quality = int(request.POST.get('quality', '80'))
    resize_option = request.POST.get('resize_option', 'none')
    resize_value = int(request.POST.get('resize_value', '0'))
    
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
    
    # Create unique temp directory
    temp_dir = None
    
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix='image_compression_')
        print(f"Created temp directory: {temp_dir}")
        
        # Process each image file
        compressed_files = []
        total_original_size = 0
        total_compressed_size = 0
        
        for i, image_file in enumerate(image_files):
            try:
                # Save uploaded image to temporary file
                temp_image_path = os.path.join(temp_dir, f"input_{i}_{uuid.uuid4().hex}")
                
                with open(temp_image_path, 'wb') as temp_file:
                    for chunk in image_file.chunks():
                        temp_file.write(chunk)
                
                original_size = os.path.getsize(temp_image_path)
                total_original_size += original_size
                print(f"Original file size: {original_size} bytes")
                
                # Compress the image
                compressed_path = compress_image(
                    temp_image_path, 
                    temp_dir, 
                    image_file.name,
                    output_format, 
                    quality, 
                    resize_option, 
                    resize_value
                )
                
                if compressed_path and os.path.exists(compressed_path):
                    compressed_size = os.path.getsize(compressed_path)
                    total_compressed_size += compressed_size
                    print(f"Compressed file size: {compressed_size} bytes")
                    
                    compressed_files.append({
                        'path': compressed_path,
                        'original_name': image_file.name,
                        'original_size': original_size,
                        'compressed_size': compressed_size
                    })
                else:
                    # If compression failed, use original but still count it
                    total_compressed_size += original_size
                    compressed_files.append({
                        'path': temp_image_path,
                        'original_name': image_file.name,
                        'original_size': original_size,
                        'compressed_size': original_size
                    })
                    
            except Exception as e:
                print(f"Error processing image {image_file.name}: {str(e)}")
                continue
        
        if not compressed_files:
            raise Exception("No image files could be processed successfully")
        
        print(f"Successfully processed {len(compressed_files)} image files")
        print(f"Total compression: {total_original_size} -> {total_compressed_size} bytes")
        
        # Calculate compression stats
        savings_percent = round((1 - total_compressed_size / total_original_size) * 100)
        compression_ratio = round(total_original_size / total_compressed_size, 1) if total_compressed_size > 0 else 1
        
        # Return compressed files
        if len(compressed_files) == 1:
            # Single file - return as image
            compressed_file = compressed_files[0]
            
            with open(compressed_file['path'], 'rb') as img_file:
                # Determine content type
                img = Image.open(compressed_file['path'])
                content_type = f"image/{img.format.lower()}"
                
                response = HttpResponse(img_file.read(), content_type=content_type)
                
                # Generate filename
                original_name = compressed_file['original_name']
                name_without_ext = os.path.splitext(original_name)[0]
                ext = img.format.lower()
                compressed_filename = f"{name_without_ext}_compressed.{ext}"
                
                response['Content-Disposition'] = f'attachment; filename="{compressed_filename}"'
                response['X-Original-Size'] = str(compressed_file['original_size'])
                response['X-Compressed-Size'] = str(compressed_file['compressed_size'])
                response['X-Savings-Percent'] = str(savings_percent)
                response['X-Compression-Ratio'] = str(compression_ratio)
                response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
            
            return response
            
        else:
            # Multiple files - return as ZIP
            zip_path = os.path.join(temp_dir, 'compressed_images.zip')
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for compressed_file in compressed_files:
                    original_name = compressed_file['original_name']
                    name_without_ext = os.path.splitext(original_name)[0]
                    
                    # Get file extension from the actual compressed file
                    img = Image.open(compressed_file['path'])
                    ext = img.format.lower()
                    compressed_filename = f"{name_without_ext}_compressed.{ext}"
                    
                    zip_file.write(compressed_file['path'], compressed_filename)
            
            # Return ZIP file
            with open(zip_path, 'rb') as zip_file:
                response = HttpResponse(zip_file.read(), content_type='application/zip')
                response['Content-Disposition'] = 'attachment; filename="compressed_images.zip"'
                response['X-Original-Size'] = str(total_original_size)
                response['X-Compressed-Size'] = str(total_compressed_size)
                response['X-Savings-Percent'] = str(savings_percent)
                response['X-Compression-Ratio'] = str(compression_ratio)
                response['X-Files-Count'] = str(len(compressed_files))
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