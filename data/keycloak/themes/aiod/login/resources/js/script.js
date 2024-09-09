document.addEventListener('DOMContentLoaded', function() {
  const toggleButton = document.getElementById('kc-form-toggle');
  const kcFormWrapper = document.getElementById('kc-form-wrapper');

  function toggleVisibility() {
    kcFormWrapper.style.display = kcFormWrapper.style.display === 'block' ? 'none' : 'block';
    toggleButton.classList.toggle('up');
  }

        // Add event listener for the click event
        if (toggleButton) {
           toggleButton.addEventListener('click', toggleVisibility);
        }
        const inputError = document.getElementById('input-error');
        if (inputError) {
          // Call the function once when the content loads if the specific ID is present
          toggleVisibility();
        }
});

