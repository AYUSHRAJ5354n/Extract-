document.addEventListener('DOMContentLoaded', function() {
    // Form submission handling with loading state
    const extractForm = document.getElementById('extractForm');
    const extractBtn = document.getElementById('extractBtn');
    const loadingSpinner = document.getElementById('loadingSpinner');
    
    if (extractForm) {
        extractForm.addEventListener('submit', function() {
            // Disable button and show spinner
            extractBtn.disabled = true;
            loadingSpinner.classList.remove('d-none');
            
            // Re-enable after 30 seconds max in case of timeout
            setTimeout(function() {
                extractBtn.disabled = false;
                loadingSpinner.classList.add('d-none');
            }, 30000);
        });
    }
    
    // Copy button functionality
    const copyButtons = document.querySelectorAll('.copy-btn');
    copyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const textToCopy = this.getAttribute('data-clipboard-text');
            
            // Create temporary element
            const tempInput = document.createElement('input');
            tempInput.value = textToCopy;
            document.body.appendChild(tempInput);
            
            // Select and copy
            tempInput.select();
            document.execCommand('copy');
            
            // Remove temporary element
            document.body.removeChild(tempInput);
            
            // Change button text temporarily
            const originalText = this.textContent;
            this.textContent = 'Copied!';
            
            setTimeout(() => {
                this.textContent = originalText;
            }, 2000);
        });
    });
});
