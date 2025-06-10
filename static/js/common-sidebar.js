// Common Sidebar JavaScript for Bloom Application

// Function to set active nav item based on current page
function setActiveNavItem() {
    const currentPath = window.location.pathname;
    const navItems = document.querySelectorAll('.nav-item');
    const dropdownItems = document.querySelectorAll('.dropdown-item');
    
    // Remove active class from all items
    navItems.forEach(item => item.classList.remove('active'));
    dropdownItems.forEach(item => item.classList.remove('active'));
      // Map of paths to nav items
    const pathMap = {
        '/': 'dashboard',  // Root still maps to dashboard for fallback
        '/dashboard': 'dashboard',
        '/index': 'dashboard',
        '/yoga': 'yoga',
        '/nutrition': 'nutrition',
        '/mood': 'mood',
        '/consultation': 'consultation',
        '/chatbot': 'chatbot',
        '/settings': 'settings',
        '/Period-Tracker': 'period-tracker',
        '/recipe': 'nutrition', // Recipe pages should highlight nutrition
        '/personalised-yoga': 'yoga',
        '/personalised-remdy': 'nutrition'
    };
    
    // Find matching nav item and set as active
    const activeSection = pathMap[currentPath];
    if (activeSection) {
        const activeItem = document.querySelector(`[data-nav="${activeSection}"]`);
        if (activeItem) {
            activeItem.classList.add('active');
            
            // If nutrition page, also handle dropdown state based on URL parameters or section
            if (activeSection === 'nutrition') {
                handleNutritionDropdownState();
            }
            
            // If consultation page, also handle dropdown state based on URL parameters or section
            if (activeSection === 'consultation') {
                handleConsultationDropdownState();
            }
        }
    } else {
        // Default to dashboard if no match
        const dashboardItem = document.querySelector('[data-nav="dashboard"]');
        if (dashboardItem) {
            dashboardItem.classList.add('active');
        }
    }
}

// Function to handle nutrition dropdown state
function handleNutritionDropdownState() {
    const dropdownContainer = document.querySelector('.menu-item-with-dropdown');
    if (dropdownContainer && window.location.pathname === '/nutrition') {
        // Check if we're on nutrition page and should open dropdown
        const urlParams = new URLSearchParams(window.location.search);
        const section = urlParams.get('section') || 'water-tracker'; // default section
        
        // Open dropdown if on nutrition page
        dropdownContainer.classList.add('open');
        
        // Set active dropdown item
        const activeDropdownItem = document.querySelector(`[data-section="${section}"]`);
        if (activeDropdownItem) {
            activeDropdownItem.classList.add('active');
        }
    }
}

// Function to handle consultation dropdown state
function handleConsultationDropdownState() {
    const consultationDropdown = document.querySelector('.nav-item[data-nav="consultation"]').closest('.menu-item-with-dropdown');
    if (consultationDropdown && window.location.pathname === '/consultation') {
        // Check if we're on consultation page and should open dropdown
        const urlParams = new URLSearchParams(window.location.search);
        const category = urlParams.get('category') || 'all'; // default category
        
        // Open dropdown if on consultation page
        consultationDropdown.classList.add('open');
        
        // Set active dropdown item
        const activeDropdownItem = consultationDropdown.querySelector(`[data-section="${category}"]`);
        if (activeDropdownItem) {
            activeDropdownItem.classList.add('active');
        }
    }
}

// Function to toggle dropdown
function toggleDropdown(dropdown) {
    dropdown.classList.toggle('open');
}

// Mobile menu toggle function
function toggleMobileMenu() {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        sidebar.style.display = sidebar.style.display === 'none' ? 'flex' : 'none';
    }
}

// Function to handle responsive sidebar
function handleResponsiveSidebar() {
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar) return;
    
    if (window.innerWidth <= 480) {
        sidebar.style.display = 'none';
    } else {
        sidebar.style.display = 'flex';
    }
}

// Initialize sidebar functionality
document.addEventListener('DOMContentLoaded', function() {
    setActiveNavItem();
    handleResponsiveSidebar();
    
    // Add click handlers for nav items
    const navItems = document.querySelectorAll('.nav-item');    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            // Check if this is a nutrition dropdown
            const dropdownContainer = this.closest('.menu-item-with-dropdown');
            if (dropdownContainer) {
                // If we're on nutrition or consultation page, toggle dropdown instead of navigating
                if (window.location.pathname === '/nutrition' || window.location.pathname === '/consultation') {
                    e.preventDefault();
                    toggleDropdown(dropdownContainer);
                    return;
                }
            }
            
            const link = this.closest('.menu-link');
            if (link && link.href) {
                window.location.href = link.href;
            }
        });
    });
      // Add click handlers for dropdown items
    const dropdownItems = document.querySelectorAll('.dropdown-item');
    dropdownItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            // Remove active class from all dropdown items in the same dropdown
            const parentDropdown = this.closest('.dropdown-content');
            parentDropdown.querySelectorAll('.dropdown-item').forEach(di => di.classList.remove('active'));
            
            // Add active class to clicked item
            this.classList.add('active');
            
            // Get the section to show
            const section = this.getAttribute('data-section');
            
            // Check if this is nutrition or consultation dropdown
            const isNutritionDropdown = this.closest('.menu-item-with-dropdown').querySelector('[data-nav="nutrition"]');
            const isConsultationDropdown = this.closest('.menu-item-with-dropdown').querySelector('[data-nav="consultation"]');
            
            if (isNutritionDropdown) {
                // If we're on nutrition page, trigger section change
                if (window.location.pathname === '/nutrition' && window.nutritionApp) {
                    window.nutritionApp.showSection(section);
                } else {
                    // Navigate to nutrition page with section parameter
                    window.location.href = `/nutrition?section=${section}`;
                }
            } else if (isConsultationDropdown) {
                // If we're on consultation page, trigger category change
                if (window.location.pathname === '/consultation' && window.consultationApp) {
                    window.consultationApp.filterByCategory(section);
                } else {
                    // Navigate to consultation page with category parameter
                    window.location.href = `/consultation?category=${section}`;
                }
            }
        });
    });
    
    // Close dropdowns when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.menu-item-with-dropdown')) {
            const openDropdowns = document.querySelectorAll('.menu-item-with-dropdown.open');
            openDropdowns.forEach(dropdown => {
                dropdown.classList.remove('open');
            });
        }
    });
});

// Handle window resize
window.addEventListener('resize', handleResponsiveSidebar);

// Export functions for use in other scripts
window.BloomSidebar = {
    setActiveNavItem,
    toggleMobileMenu,
    handleResponsiveSidebar,
    toggleDropdown,
    handleNutritionDropdownState,
    handleConsultationDropdownState
};
