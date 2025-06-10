// Common Sidebar JavaScript for Bloom Application

// Function to set active nav item based on current page
function setActiveNavItem() {
    const currentPath = window.location.pathname;
    const navItems = document.querySelectorAll('.nav-item');
    
    // Remove active class from all items
    navItems.forEach(item => item.classList.remove('active'));    // Map of paths to nav items
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
        }
    } else {
        // Default to dashboard if no match
        const dashboardItem = document.querySelector('[data-nav="dashboard"]');
        if (dashboardItem) {
            dashboardItem.classList.add('active');
        }
    }
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
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', function() {
            const link = this.closest('.menu-link');
            if (link && link.href) {
                window.location.href = link.href;
            }
        });
    });
});

// Handle window resize
window.addEventListener('resize', handleResponsiveSidebar);

// Export functions for use in other scripts
window.BloomSidebar = {
    setActiveNavItem,
    toggleMobileMenu,
    handleResponsiveSidebar
};
