// Resume Management System - JavaScript utilities

document.addEventListener('DOMContentLoaded', function() {
    // File upload validation
    const fileInput = document.getElementById('resume_file');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                // Check file type
                if (file.type !== 'application/pdf') {
                    alert('Please select a PDF file only.');
                    e.target.value = '';
                    return;
                }
                
                // Check file size (5MB max)
                const maxSize = 5 * 1024 * 1024; // 5MB in bytes
                if (file.size > maxSize) {
                    alert('File size must not exceed 5MB.');
                    e.target.value = '';
                    return;
                }
                
                console.log('File validated:', file.name);
            }
        });
    }
    
    // Form submission confirmation for resume builder
    const builderForm = document.querySelector('.builder-form');
    if (builderForm) {
        builderForm.addEventListener('submit', function(e) {
            const fullName = document.getElementById('full_name').value.trim();
            const skills = document.getElementById('skills').value.trim();
            
            if (!fullName || !skills) {
                e.preventDefault();
                alert('Please fill in at least your name and skills.');
                return false;
            }
            
            // Show loading state
            const submitBtn = builderForm.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = '✨ Generating Resume... Please wait';
            }
        });
    }
    
    // Confirm delete actions
    const deleteButtons = document.querySelectorAll('[data-action="delete"]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this resume?')) {
                e.preventDefault();
                return false;
            }
        });
    });
    
    // Auto-hide messages after 5 seconds
    const messages = document.querySelectorAll('.alert');
    messages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => message.remove(), 300);
        }, 5000);
    });
});
