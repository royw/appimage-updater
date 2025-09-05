// Enhanced Home Navigation JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Make the header title clickable to return home
    const headerTitle = document.querySelector('.md-header__title');
    if (headerTitle && !headerTitle.querySelector('a')) {
        headerTitle.style.cursor = 'pointer';
        headerTitle.addEventListener('click', function() {
            window.location.href = '/';
        });
        
        // Add tooltip
        headerTitle.title = 'Click to return home';
    }
    
    // Make the logo clickable if it exists
    const logo = document.querySelector('.md-header__button.md-logo');
    if (logo && !logo.querySelector('a')) {
        logo.style.cursor = 'pointer';
        logo.addEventListener('click', function() {
            window.location.href = '/';
        });
        
        // Add tooltip
        logo.title = 'Click to return home';
    }
    
    // Enhance breadcrumb navigation
    const breadcrumbs = document.querySelector('.md-nav--primary');
    if (breadcrumbs) {
        const homeLink = breadcrumbs.querySelector('a[href="/"], a[href="./"], a[href="../"]');
        if (homeLink && !homeLink.textContent.includes('🏠')) {
            homeLink.innerHTML = '🏠 ' + homeLink.innerHTML;
        }
    }
});

// Add keyboard shortcut for home (Alt + H)
document.addEventListener('keydown', function(event) {
    if (event.altKey && event.key === 'h') {
        event.preventDefault();
        window.location.href = '/';
    }
});
