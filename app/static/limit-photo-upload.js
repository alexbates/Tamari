document.addEventListener("DOMContentLoaded", function() {
    const fileInput = document.getElementById('image');
    const errorDiv = document.getElementById('image-error');
    const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB in bytes

    fileInput.addEventListener('change', function() {
        const file = this.files[0];
        if (file && file.size > MAX_FILE_SIZE) {
            errorDiv.textContent = 'File size must be less than 10MB.';
            this.value = ''; // Clear the file input field
        } else {
            errorDiv.textContent = '';
        }
    });
});