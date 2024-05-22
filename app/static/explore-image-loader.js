document.addEventListener("DOMContentLoaded", function() {
	// Get all .r2top divs
	const r2topDivs = document.querySelectorAll('.r2top');

	// Function to replace the background image
	function replaceBackgroundImage(index) {
		if (index < r2topDivs.length) {
			const r2topDiv = r2topDivs[index];
			const newBgImage = r2topDiv.getAttribute('data-bgimage');

			// Create a new Image object
			const img = new Image();

			// Add an onload event listener
			img.onload = function() {
				// Update the background image only after the new image is loaded
				r2topDiv.style.backgroundImage = `url(${newBgImage})`;

				// Delay the next replacement
				setTimeout(() => {
					replaceBackgroundImage(index + 1);
				}, 500); // 0.5 second delay
			};

			// Add an onerror event listener
			img.onerror = function() {
				// If the image fails to load, move on to the next one
				setTimeout(() => {
				  replaceBackgroundImage(index + 1);
				}, 500); // 0.5 second delay
			};

			// Set the source of the Image object
			img.src = newBgImage;
		}
	}

	// Start the image replacement process
	replaceBackgroundImage(0);
});