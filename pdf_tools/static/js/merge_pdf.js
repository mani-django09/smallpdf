// Complete JavaScript for the Merge PDF functionality
document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const uploadArea = document.getElementById('uploadArea');
    const previewArea = document.getElementById('previewArea');
    const resultsArea = document.getElementById('resultsArea');
    const pdfList = document.getElementById('pdfList');
    const fileInput = document.getElementById('fileInput');
    const addMoreBtn = document.getElementById('addMoreBtn');
    const clearBtn = document.getElementById('clearBtn');
    const mergeBtn = document.getElementById('mergeBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    const startNewBtn = document.getElementById('startNewBtn');
    const loadingOverlay = document.getElementById('loadingOverlay');
    
    // Store uploaded files
    let uploadedFiles = [];
    let mergedPdfUrl = null;
    
    // Enable drag and drop
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadArea.classList.add('upload-area-active');
    });
    
    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('upload-area-active');
    });
    
    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('upload-area-active');
        
        const files = e.dataTransfer.files;
        handleFiles(files);
    });
    
    // Handle file selection via input
    fileInput.addEventListener('change', function() {
        handleFiles(this.files);
    });
    
    // Add more files button
    addMoreBtn.addEventListener('click', function() {
        fileInput.click();
    });
    
    // Clear all files button
    clearBtn.addEventListener('click', function() {
        uploadedFiles = [];
        pdfList.innerHTML = '';
        previewArea.style.display = 'none';
        uploadArea.style.display = 'block';
    });
    
    // Merge button
    mergeBtn.addEventListener('click', function() {
        if (uploadedFiles.length < 2) {
            alert('Please upload at least 2 PDF files to merge.');
            return;
        }
        
        // Show loading overlay
        loadingOverlay.style.display = 'flex';
        
        // In a real implementation, you would send the files to your server or use a client-side library
        // Here we'll simulate the merging process with a timeout
        setTimeout(function() {
            // Hide loading overlay
            loadingOverlay.style.display = 'none';
            
            // In a real implementation, you'd get the URL to the merged PDF
            mergedPdfUrl = 'merged.pdf';
            
            // Show results area
            previewArea.style.display = 'none';
            resultsArea.style.display = 'block';
        }, 2000); // Simulate a 2-second process
    });
    
    // Download button
    downloadBtn.addEventListener('click', function() {
        // In a real implementation, this would create a download link to the actual file
        // For now, we'll just show a loading spinner briefly
        loadingOverlay.style.display = 'flex';
        
        setTimeout(function() {
            loadingOverlay.style.display = 'none';
            
            // In a real implementation, this would trigger the file download
            // For demonstration, we'll show an alert
            alert('Your merged PDF is downloading. In a real application, this would save the file to your device.');
            
            // In a real implementation, you might use something like:
            // const link = document.createElement('a');
            // link.href = mergedPdfUrl;
            // link.download = 'merged.pdf';
            // link.click();
        }, 1000);
    });
    
    // Start new button
    startNewBtn.addEventListener('click', function() {
        // Reset everything
        uploadedFiles = [];
        pdfList.innerHTML = '';
        mergedPdfUrl = null;
        
        // Show upload area again
        resultsArea.style.display = 'none';
        uploadArea.style.display = 'block';
    });
    
    // Handle uploaded files
    function handleFiles(files) {
        if (files.length === 0) return;
        
        // Show loading overlay
        loadingOverlay.style.display = 'flex';
        
        // Filter for PDF files only
        const validFiles = Array.from(files).filter(file => file.type === 'application/pdf');
        
        if (validFiles.length === 0) {
            loadingOverlay.style.display = 'none';
            alert('Please select PDF files only.');
            return;
        }
        
        // Add valid files to our collection
        uploadedFiles = uploadedFiles.concat(validFiles);
        
        // In a real implementation, you would generate actual thumbnails/previews
        // Here we'll simulate with a timeout
        setTimeout(function() {
            // Hide loading overlay
            loadingOverlay.style.display = 'none';
            
            // Update the UI with the files
            renderPreviews();
            
            // Show preview area, hide upload area
            uploadArea.style.display = 'none';
            previewArea.style.display = 'block';
        }, 1500);
    }
    
    // Render file previews in the UI
    function renderPreviews() {
        pdfList.innerHTML = '';
        
        uploadedFiles.forEach((file, index) => {
            const pdfItem = document.createElement('div');
            pdfItem.className = 'pdf-item';
            pdfItem.setAttribute('draggable', 'true');
            pdfItem.setAttribute('data-index', index);
            
            // Format file size nicely
            const fileSize = formatFileSize(file.size);
            
            // In a real implementation, you might generate actual thumbnails
            // For now, we'll use a PDF icon
            pdfItem.innerHTML = `
                <div class="pdf-item-preview">
                    <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14 2 14 8 20 8"></polyline>
                        <line x1="16" y1="13" x2="8" y2="13"></line>
                        <line x1="16" y1="17" x2="8" y2="17"></line>
                        <polyline points="10 9 9 9 8 9"></polyline>
                    </svg>
                </div>
                <div class="pdf-item-info">
                    <div class="pdf-item-name" title="${file.name}">${truncateFileName(file.name, 20)}</div>
                    <div class="pdf-item-size">${fileSize}</div>
                </div>
                <button class="pdf-item-remove" data-index="${index}">×</button>
            `;
            
            pdfList.appendChild(pdfItem);
        });
        
        // Add event listeners to remove buttons
        document.querySelectorAll('.pdf-item-remove').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                const index = parseInt(this.getAttribute('data-index'));
                uploadedFiles.splice(index, 1);
                renderPreviews();
                
                // If no files left, show upload area again
                if (uploadedFiles.length === 0) {
                    previewArea.style.display = 'none';
                    uploadArea.style.display = 'block';
                }
            });
        });
        
        // Enable drag and drop reordering in a real implementation
        // This would require additional event listeners for dragstart, dragover, dragend, etc.
    }
    
    // Helper to format file size nicely
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    // Helper to truncate long filenames
    function truncateFileName(name, maxLength) {
        if (name.length <= maxLength) return name;
        
        const extension = name.split('.').pop();
        const nameWithoutExt = name.substring(0, name.lastIndexOf('.'));
        
        const truncatedName = nameWithoutExt.substring(0, maxLength - extension.length - 3) + '...';
        return truncatedName + '.' + extension;
    }
    
    // FAQ functionality
    const faqItems = document.querySelectorAll('.faq-item');
    
    faqItems.forEach(item => {
        const question = item.querySelector('.faq-question');
        
        question.addEventListener('click', function() {
            const isActive = item.classList.contains('active');
            
            // Close all FAQs first
            faqItems.forEach(faq => {
                faq.classList.remove('active');
            });
            
            // If it wasn't active before, make it active
            if (!isActive) {
                item.classList.add('active');
            }
        });
    });
    
    // Open first FAQ by default
    if (faqItems.length > 0) {
        faqItems[0].classList.add('active');
    }
});