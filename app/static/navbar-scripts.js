// Navbar account dropdown, shown when viewing on desktop
function toggleDropdown() {
	document.getElementById("myDropdown").classList.toggle("showdrop");
}
function closeDropdown() {
	document.getElementById("myDropdown").classList.remove("showdrop");
}
// Information "i" popup on recipe detail page, when viewing on desktop
function toggleInformation() {
	document.getElementById("informationDrop").classList.toggle("showinformation");
}
// Information "i" popup on recipe detail page, when viewing on mobile
function toggleInformationMobile() {
	document.getElementById("informationDropMobile").classList.toggle("showinformation");
}
// Display Settings in My Recipes
function toggleSettings() {
	document.getElementById("settingsDrop").classList.toggle("showsettings");
}
$(function(){
	var $curParent, Content;
	$(document).delegate(".ing","click", function(){
		if($(this).closest("s").length) {
			Content = $(this).parent("s").html();
			$curParent = $(this).closest("s");
			$(Content).insertAfter($curParent);
			$(this).closest("s").remove();
		}
		else {
			$(this).wrapAll("<s />");
		}
	});
});
$(function(){
	var $curParent, Content;
	$(document).delegate(".steps","click", function(){
		if($(this).closest("s").length) {
			Content = $(this).parent("s").html();
			$curParent = $(this).closest("s");
			$(Content).insertAfter($curParent);
			$(this).closest("s").remove();
		}
		else {
			$(this).wrapAll("<s />");
		}
	});
});
	
$("#search").on("input", function () {
	// Normalize query
	var q = $(this).val()
		.toLowerCase()
		.normalize('NFD').replace(/[\u0300-\u036f]/g, '')
		.replace(/[^a-z0-9]+/g, ' ')
		.replace(/\s+/g, ' ')
		.trim();
	var terms = q ? q.split(' ') : [];
	var count = 0;
	$('#recipecont a').each(function () {
		var cached = $(this).data('matchtext');
		if (!cached) {
			cached = $(this).text()
				.toLowerCase()
				.normalize('NFD').replace(/[\u0300-\u036f]/g, '')
				.replace(/[^a-z0-9]+/g, ' ')
				.replace(/\s+/g, ' ')
				.trim();
			$(this).data('matchtext', cached);
		}
		// All reccipes are shown if no search term entered
		var isMatch = (terms.length === 0) || terms.every(function (t) {
			return cached.indexOf(t) !== -1;
		});
		$(this).toggle(isMatch);
		if (isMatch) count++;
	});
});

if ('IntersectionObserver' in window) { // if IntersectionObserver support in browser
	document.addEventListener("DOMContentLoaded", function() {
		function handleIntersection(entries) {
			entries.map((entry) => {
				if (entry.isIntersecting) {
          			// Item has crossed our observation
          			// threshold - load src from data-src
          			entry.target.style.backgroundImage = "url('"+entry.target.dataset.bgimage+"')";
          			// Job done for this item - no need to watch it!
          			observer.unobserve(entry.target);
        		}
      		});
    	}
    	const headers = document.querySelectorAll('.recipe1');
    	const observer = new IntersectionObserver(
      		handleIntersection,
      		{ rootMargin: window.DYN_ROOT_MARGIN }
    	);
    	headers.forEach(header => observer.observe(header));
	});
} else { // else load all images at once
	const headers = document.querySelectorAll('.recipe1');
	headers.forEach(header => {
    	header.style.backgroundImage = "url('"+header.dataset.bgimage+"')";
  	});
}

if ('IntersectionObserver' in window) { // if IntersectionObserver support in browser
	document.addEventListener("DOMContentLoaded", function() {
		function handleIntersection(entries) {
			entries.map((entry) => {
				if (entry.isIntersecting) {
          			// Item has crossed our observation
          			// threshold - load src from data-src
          			entry.target.style.backgroundImage = "url('"+entry.target.dataset.bgimage+"')";
          			// Job done for this item - no need to watch it!
          			observer.unobserve(entry.target);
        		}
      		});
    	}
    	const headers = document.querySelectorAll('.r2top');
    	const observer = new IntersectionObserver(
      		handleIntersection,
      		{ rootMargin: window.DYN_ROOT_MARGIN }
    	);
    	headers.forEach(header => observer.observe(header));
	});
} else { // else load all images at once
	const headers = document.querySelectorAll('.r2top');
	headers.forEach(header => {
    	header.style.backgroundImage = "url('"+header.dataset.bgimage+"')";
  	});
}
	
if ('IntersectionObserver' in window) { // if IntersectionObserver support in browser
	document.addEventListener("DOMContentLoaded", function() {
		function handleIntersection(entries) {
			entries.map((entry) => {
				if (entry.isIntersecting) {
          			// Item has crossed our observation
          			// threshold - load src from data-src
          			entry.target.style.backgroundImage = "url('"+entry.target.dataset.bgimage+"')";
          			// Job done for this item - no need to watch it!
          			observer.unobserve(entry.target);
        		}
      		});
    	}
    	const headers = document.querySelectorAll('.r3inner');
    	const observer = new IntersectionObserver(
      		handleIntersection,
      		{ rootMargin: window.DYN_ROOT_MARGIN }
    	);
    	headers.forEach(header => observer.observe(header));
	});
} else { // else load all images at once
	const headers = document.querySelectorAll('.r3inner');
	headers.forEach(header => {
    	header.style.backgroundImage = "url('"+header.dataset.bgimage+"')";
  	});
}
	
// Add and Edit Recipe hidden div
function toggleNutrition(check) {
	// Find nutrition_checkbox element
    var checkbox = document.getElementById("nutrition_checkbox");
	// Set checkbox if passed argument is true or false
	if (check === true) {checkbox.checked = true;}
	if (check === false) {checkbox.checked = false;}
	// Find togglelabel and nutrition div
	var label = document.querySelector(".togglelabel");
    var div = document.getElementById("nutrition");
	// Set nutrition div display and label text
    if (checkbox.checked) {
		div.style.display = "block";
		label.innerText = "Delete Nutrition Info";
    } else {
    	div.style.display = "none";
		label.innerText = "Add Nutrition Info";
    }
}
	
// Dynamic loading of images on Explore Recipe Detail
document.addEventListener("DOMContentLoaded", function() {
	const mobileImageDiv = document.querySelector('.mobile-image');
	if (mobileImageDiv) {
		const imageUrl1 = mobileImageDiv.dataset.image;
		if (imageUrl1) {
			const img1 = new Image();
			// Required for sites that have measured to prevent unauthorized access to resources
			img1.crossOrigin = 'Anonymous';
			img1.onload = () => {
				mobileImageDiv.style.backgroundImage = `url(${img1.src})`;
			};
			img1.src = imageUrl1;
		}
	}
		
	const rImageDiv = document.getElementById('r-image');
	if (rImageDiv) {
		const imageUrl2 = rImageDiv.dataset.image;
		if (imageUrl2) {
			const img2 = new Image();
			// Required for sites that have measured to prevent unauthorized access to resources
			img2.crossOrigin = 'Anonymous';
			img2.onload = () => {
				rImageDiv.style.backgroundImage = `url(${img2.src})`;
			};
			img2.src = imageUrl2;
		}
	}
});
	
// CTRL+S keyboard shortcut to focus search box in My Recipes
$(document).ready(function() {
    if ($('#search').length) {
        $(document).keydown(function(e) {
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                $('#search').focus();
            }
        });
    }
});
	
// CTRL+S keyboard shortcut to focus search box in Explore
$(document).ready(function() {
    if ($('#exploresearch').length) {
        $(document).keydown(function(e) {
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                $('#exploresearch').focus();
            }
        });
    }
});
	
// This code is for handling the horizontal scrolling of navbar on desktop
document.addEventListener('DOMContentLoaded', function() {
	const container = document.querySelector('.navleft');
	const navleft = document.querySelector('.navleft ul');
	const rightArrow = document.querySelector('.scroll-right');
	const leftArrow = document.querySelector('.scroll-left');

	function checkScroll() {
		if (!container || !navleft || !rightArrow || !leftArrow) return;

		const isScrollable = navleft.scrollWidth > container.clientWidth;
		const isScrolledToEnd = navleft.scrollLeft + navleft.clientWidth >= navleft.scrollWidth;
		const isScrolledToStart = navleft.scrollLeft === 0;

		rightArrow.style.display = isScrollable && !isScrolledToEnd ? 'block' : 'none';
		leftArrow.style.display = isScrollable && !isScrolledToStart ? 'block' : 'none';
	}

	if (rightArrow && leftArrow) {
		rightArrow.addEventListener('click', function() {
			if (navleft) {
				navleft.scrollBy({ left: 300, behavior: 'smooth' });
			}
		});

		leftArrow.addEventListener('click', function() {
			if (navleft) {
				navleft.scrollBy({ left: -300, behavior: 'smooth' });
			}
		});
	}

	if (navleft) {
        navleft.addEventListener('scroll', checkScroll);
    }
	window.addEventListener('resize', checkScroll);

	// Initial check with delay
	setTimeout(checkScroll, 100);  // 100ms delay

	// Additional check after a longer delay to catch any late-loading content
	setTimeout(checkScroll, 2000);  // 2 second delay
});
	
// Handle the horizontal scrolling of page buttons
// These buttons All Recipes, Favorites, Categories, and Recents
document.addEventListener('DOMContentLoaded', function() {
	const containerRecip = document.querySelector('.recipenavleft');
	const navRecip       = document.querySelector('.recipenavleft-inner');
	const rightArrowRecip = document.querySelector('.scroll-right-recip');
	const leftArrowRecip  = document.querySelector('.scroll-left-recip');

	// Adjust how close to the edge we consider "end" or "start":
	const EDGE_THRESHOLD = 2;  // or 3, 5, etc.  

	function checkScrollRecip() {
		if (!containerRecip || !navRecip || !rightArrowRecip || !leftArrowRecip) return;

		const scrollLeftPlusWidth = navRecip.scrollLeft + navRecip.clientWidth;
		const maxScroll           = navRecip.scrollWidth;
			
		// If within a few pixels of maxScroll, treat as "scrolled to end."
		const isScrolledToEnd   = (scrollLeftPlusWidth >= (maxScroll - EDGE_THRESHOLD));
		const isScrolledToStart = (navRecip.scrollLeft <= EDGE_THRESHOLD);

		const isScrollable = (maxScroll > containerRecip.clientWidth);

		rightArrowRecip.style.display = (isScrollable && !isScrolledToEnd) ? 'block' : 'none';
		leftArrowRecip.style.display  = (isScrollable && !isScrolledToStart) ? 'block' : 'none';
	}

	// Clamp the scroll so we never overshoot:
	function scrollRight() {
		const maxLeft = navRecip.scrollWidth - navRecip.clientWidth;
		const newLeft = Math.min(navRecip.scrollLeft + 300, maxLeft);
		navRecip.scrollTo({ left: newLeft, behavior: 'smooth' });
	}

	function scrollLeft() {
		const newLeft = Math.max(navRecip.scrollLeft - 300, 0);
		navRecip.scrollTo({ left: newLeft, behavior: 'smooth' });
	}

	// Set up arrow events
	if (rightArrowRecip && leftArrowRecip) {
		rightArrowRecip.addEventListener('click', function() {
		if (navRecip) scrollRight();
		});
		leftArrowRecip.addEventListener('click', function() {
		if (navRecip) scrollLeft();
		});
	}

	// Re-check on scroll or resize
	if (navRecip) {
		navRecip.addEventListener('scroll', checkScrollRecip);
	}
	window.addEventListener('resize', checkScrollRecip);

	// Initial checks with delay
	setTimeout(checkScrollRecip, 100);
	setTimeout(checkScrollRecip, 2000);
});
// Auto scroll active page button into view
window.addEventListener('load', function() {
	const containerRecip = document.querySelector('.recipenavleft');
	const navRecip = document.querySelector('.recipenavleft-inner');
	const activeButton = document.querySelector('.recbtn-active');
	if (!containerRecip || !navRecip || !activeButton) return;
		
	// Get bounding rectangles for the visible container and the active button.
	const containerRect = containerRecip.getBoundingClientRect();
	const buttonRect = activeButton.getBoundingClientRect();
		
	// Check if the active button is fully visible within the container.
	const fullyVisible = buttonRect.left >= containerRect.left &&
						buttonRect.right <= containerRect.right;
		
	// Only if it's not fully visible, scroll it into view and (if movement happens) adjust by extra 140px.
	if (!fullyVisible) {
		const initialScroll = navRecip.scrollLeft;
		activeButton.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
			
		setTimeout(() => {
		const finalScroll = navRecip.scrollLeft;
		// If the scroll changed significantly (i.e. scrollIntoView moved the container),
		// add an extra 140px to the right.
		if (Math.abs(finalScroll - initialScroll) > 10) {
			navRecip.scrollLeft = finalScroll + 140;
		}
		}, 500); // Adjust this delay to match your smooth scrolling timing if needed.
	}
});
// If #endpoints exists, count number of <details> elements, update #endpoints span
$(document).ready(function() {
	if ($('#endpoints').length > 0) {
		var detailsCount = $('details').length;
		$('#endpoints').html(detailsCount + ' endpoints found.');
	}
});
// Advanced Search button on All Recipes, Favorites, and Recents
$(document).ready(function() {
	var searchBtn = document.getElementById('indexSearchBtn');
	if (searchBtn) {
		searchBtn.addEventListener('click', function() {
			// Get the text from the search box and trim whitespace.
			var searchTerm = document.getElementById('search').value.trim();
			// Build the URL and redirect.
			var url = '/my-recipes/search?query=' + encodeURIComponent(searchTerm).replace(/%20/g, '+');
			window.location.href = url;
		});
	} else {
		console.error("Element with id 'indexSearchBtn' not found!");
	}
});
// Add recipes to Meal Plan from Meal Planner page
// Only run if fields are present on the page
document.addEventListener('DOMContentLoaded', function() {
	const input = document.getElementById('mp-recipe-search');
	if (!input) return;

	const list   = document.getElementById('mp-search-results');
	const hidden = document.getElementById('mp-selected-hex-id');
	let recipes  = [];

	// Retrieve JSON from mealPlannerListAllRecipes route
	fetch("{{ url_for('mealplanner.mealPlannerListAllRecipes') }}", {
		credentials: 'same-origin'
	})
	.then(r => r.json())
	.then(data => { recipes = data.recipes; })
	.catch(() => { /* silent fail: list stays empty */ });

	// Filter search results
	input.addEventListener('input', () => {
		const q = input.value.trim().toLowerCase();
		list.innerHTML = '';
		if (!q) return;

		const matches = recipes
			.filter(r => r.title.toLowerCase().includes(q))
			.slice(0, 10);

		for (const r of matches) {
			const li = document.createElement('li');
			li.textContent      = r.title;
			li.dataset.hex      = r.hex_id;
			list.appendChild(li);
		}
	});

	// This processes the clicking of a result
	list.addEventListener('click', function(e) {
		if (e.target.tagName !== 'LI') return;
		input.value    = e.target.textContent;
		hidden.value   = e.target.dataset.hex;
		list.innerHTML = '';
	});

	// Hide results when clicking outside
	document.addEventListener('click', function(e) {
		if (!input.contains(e.target)) {
			list.innerHTML = '';
		}
	});

});