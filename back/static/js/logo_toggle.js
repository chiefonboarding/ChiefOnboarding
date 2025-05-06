// Wait until the document is fully loaded
window.addEventListener('load', function() {
    // Find the logo type radio buttons
    const logoTypeFile = document.getElementById('logo_type_file');
    const logoTypeUrl = document.getElementById('logo_type_url');
    
    if (!logoTypeFile || !logoTypeUrl) {
        console.error('Logo type radio buttons not found');
        return;
    }
    
    // Find the logo upload and URL input sections
    const logoFileUpload = document.querySelector('.logo-file-upload');
    const logoUrlInput = document.querySelector('.logo-url-input');
    
    if (!logoFileUpload || !logoUrlInput) {
        console.error('Logo sections not found');
        return;
    }
    
    function updateVisibleSection() {
        if (logoTypeFile.checked) {
            logoFileUpload.classList.remove('d-none');
            logoUrlInput.classList.add('d-none');
        } else if (logoTypeUrl.checked) {
            logoFileUpload.classList.add('d-none');
            logoUrlInput.classList.remove('d-none');
        }
    }
    
    // Run the update immediately
    updateVisibleSection();
    
    // Update when the selection changes
    logoTypeFile.addEventListener('change', updateVisibleSection);
    logoTypeUrl.addEventListener('change', updateVisibleSection);
});
