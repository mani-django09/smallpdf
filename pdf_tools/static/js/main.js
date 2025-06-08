document.addEventListener('DOMContentLoaded', function() {
    // Search functionality
    const searchInput = document.querySelector('.search-input');
    const searchButton = document.querySelector('.search-button');
    
    if(searchInput && searchButton) {
        // Function to handle search
        const handleSearch = function() {
            const query = searchInput.value.toLowerCase().trim();
            let redirectURL = '#tools';
            
            // Determine destination based on search query
            if(query.includes('word')) {
                redirectURL = '/pdf-to-word/';
            } else if(query.includes('jpg') || query.includes('image')) {
                redirectURL = '/pdf-to-jpg/';
            } else if(query.includes('compress')) {
                redirectURL = '/compress-pdf/';
            } else if(query.includes('merge')) {
                redirectURL = '/merge-pdf/';
            } else if(query.includes('excel')) {
                redirectURL = '/pdf-to-excel/';
            } else {
                redirectURL = '/tools/';
            }
            
            window.location.href = redirectURL;
        };
        
        // Add click event to button
        searchButton.addEventListener('click', handleSearch);
        
        // Add enter key event to input
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                handleSearch();
            }
        });
    }
    
    // Initialize FAQ accordions
    const faqItems = document.querySelectorAll('.faq-item');
    faqItems.forEach(item => {
        const question = item.querySelector('.faq-question');
        question.addEventListener('click', () => {
            // Close all other items
            faqItems.forEach(otherItem => {
                if (otherItem !== item && otherItem.classList.contains('active')) {
                    otherItem.classList.remove('active');
                }
            });
            
            // Toggle current item
            item.classList.toggle('active');
        });
    });
    
    // Add animation to tool cards
    const toolCards = document.querySelectorAll('.tool-card');
    const observerOptions = {
        threshold: 0.2,
        rootMargin: '0px 0px -10% 0px'
    };
    
    const cardObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animated');
                cardObserver.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    toolCards.forEach(card => {
        cardObserver.observe(card);
    });
});