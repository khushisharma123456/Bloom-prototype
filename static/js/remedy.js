// Remedy page interactive features
document.addEventListener('DOMContentLoaded', function() {
    // Add smooth scrolling for better UX
    document.documentElement.style.scrollBehavior = 'smooth';
    
    // Add interactive effects to remedy cards
    const remedyCards = document.querySelectorAll('.remedy-card');
    
    remedyCards.forEach(card => {
        // Add entrance animation delay
        const delay = Array.from(remedyCards).indexOf(card) * 100;
        card.style.animationDelay = `${delay}ms`;
        
        // Add hover effects for recipe sections
        const sections = card.querySelectorAll('.remedy-section');
        sections.forEach(section => {
            section.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-4px) scale(1.02)';
                this.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
            });
            
            section.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0) scale(1)';
            });
        });
    });
    
    // Add click functionality to action buttons
    const saveButtons = document.querySelectorAll('.save-btn');
    const shareButtons = document.querySelectorAll('.share-btn');
    
    saveButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            this.innerHTML = '<i class="fas fa-check"></i> Saved!';
            this.style.background = 'linear-gradient(135deg, #4CAF50 0%, #45a049 100%)';
            
            setTimeout(() => {
                this.innerHTML = '<i class="fas fa-bookmark"></i> Save Recipe';
                this.style.background = '';
            }, 2000);
        });
    });
    
    shareButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            if (navigator.share) {
                navigator.share({
                    title: document.querySelector('.remedy-title').textContent,
                    text: 'Check out this amazing natural remedy!',
                    url: window.location.href
                });
            } else {
                // Fallback for browsers that don't support Web Share API
                navigator.clipboard.writeText(window.location.href).then(() => {
                    this.innerHTML = '<i class="fas fa-check"></i> Link Copied!';
                    this.style.background = 'linear-gradient(135deg, #4CAF50 0%, #45a049 100%)';
                    
                    setTimeout(() => {
                        this.innerHTML = '<i class="fas fa-share-alt"></i> Share';
                        this.style.background = '';
                    }, 2000);
                });
            }
        });
    });
    
    // Add parallax effect to hero section
    const hero = document.querySelector('.remedy-hero');
    if (hero) {
        window.addEventListener('scroll', () => {
            const scrolled = window.pageYOffset;
            const rate = scrolled * -0.5;
            hero.style.transform = `translateY(${rate}px)`;
        });
    }
    
    // Add loading animation for images
    const images = document.querySelectorAll('.remedy-image');
    images.forEach(img => {
        img.addEventListener('load', function() {
            this.style.opacity = '0';
            this.style.transition = 'opacity 0.5s ease';
            setTimeout(() => {
                this.style.opacity = '1';
            }, 100);
        });
    });
    
    // Add step completion functionality
    const stepItems = document.querySelectorAll('.step-item');
    stepItems.forEach(step => {
        step.addEventListener('click', function() {
            this.classList.toggle('completed');
            if (this.classList.contains('completed')) {
                this.style.opacity = '0.7';
                this.style.textDecoration = 'line-through';
            } else {
                this.style.opacity = '1';
                this.style.textDecoration = 'none';
            }
        });
    });
    
    // Add ingredient checking functionality
    const ingredientItems = document.querySelectorAll('.ingredient-item');
    ingredientItems.forEach(ingredient => {
        ingredient.addEventListener('click', function() {
            const icon = this.querySelector('i');
            if (icon.classList.contains('fa-check-circle')) {
                icon.classList.remove('fa-check-circle');
                icon.classList.add('fa-times-circle');
                icon.style.color = '#e74c3c';
                this.style.opacity = '0.6';
            } else {
                icon.classList.remove('fa-times-circle');
                icon.classList.add('fa-check-circle');
                icon.style.color = '';
                this.style.opacity = '1';
            }
        });
    });
    
    // Add smooth reveal animation on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Observe remedy sections for scroll animations
    const sections = document.querySelectorAll('.remedy-section');
    sections.forEach(section => {
        section.style.opacity = '0';
        section.style.transform = 'translateY(20px)';
        section.style.transition = 'all 0.6s ease';
        observer.observe(section);
    });
});
