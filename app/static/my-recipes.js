document.addEventListener('DOMContentLoaded', function() {
	// Invalid category has no results area to initialize
	const results = document.getElementById('my-recipes-results');
	if (!results) return;
	const grid = results.querySelector('[data-recipe-grid]');
	const search = document.getElementById('search');
	const categoryCount = document.getElementById('recipecount');
	const sentinel = document.getElementById('recipe-page-end');
	const loader = document.getElementById('recipe-loader');
	const errorMessage = document.getElementById('recipeloaderror');
	const loadMore = document.getElementById('recipe-load-more');
	const empty = document.getElementById('norecipes');
	const noMatches = document.getElementById('norecipematches');
	// Make sure that the same recipe is only added once by tracking cards already shown
	const recipeIds = new Set();
	let cursor = null;
	let hasMore = true;
	let searchTimer = null;
	let controller = null;
	let restartOnRetry = false;
	let pageObserver = null;
	let photoObserver = null;
	// Copy the photo URL when it is ready to load
	function loadRecipePhoto(photo) {
		photo.style.backgroundImage = 'url(' + JSON.stringify(photo.dataset.bgimage) + ')';
	}
	// Fetch another batch as scroll down the page, load the photos after the cards approach the viewport
	if ('IntersectionObserver' in window) {
		pageObserver = new IntersectionObserver(function(entries) {
			if (errorMessage.hidden && entries.some(entry => entry.isIntersecting)) {
				loadRecipePage();
			}
		}, { rootMargin: window.DYN_ROOT_MARGIN });
		photoObserver = new IntersectionObserver(function(entries) {
			entries.forEach(function(entry) {
				if (entry.isIntersecting) {
					loadRecipePhoto(entry.target);
					photoObserver.unobserve(entry.target);
				}
			});
		}, { rootMargin: window.DYN_ROOT_MARGIN });
	}
	// Parse the cards before adding them to the grid
	function appendRecipes(html) {
		const template = document.createElement('template');
		template.innerHTML = html;
		const photos = [];
		template.content.querySelectorAll('[data-recipe-id]').forEach(function(card) {
			const recipeId = card.dataset.recipeId;
			if (recipeIds.has(recipeId)) {
				card.remove();
				return;
			}
			recipeIds.add(recipeId);
			const photo = card.querySelector('[data-bgimage]');
			if (photo) photos.push(photo);
		});
		// The observer watches the photos
		grid.appendChild(template.content);
		photos.forEach(function(photo) {
			if (photoObserver) photoObserver.observe(photo);
			else loadRecipePhoto(photo);
		});
	}
	// Cancel current request, stop watching old results, clear results so the next request starts at first batch
	function resetRecipes() {
		if (controller) controller.abort();
		if (pageObserver) pageObserver.unobserve(sentinel);
		if (photoObserver) photoObserver.disconnect();
		controller = null;
		cursor = null;
		hasMore = true;
		restartOnRetry = false;
		recipeIds.clear();
		grid.replaceChildren();
		grid.setAttribute('aria-busy', 'false');
		loader.hidden = true;
		errorMessage.hidden = true;
		loadMore.hidden = true;
		empty.hidden = true;
		noMatches.hidden = true;
	}
	async function loadRecipePage() {
		if (controller || searchTimer !== null || !hasMore || !results.getClientRects().length) return;
		const activeRequest = new AbortController();
		controller = activeRequest;
		const timeout = setTimeout(function() { activeRequest.abort(); }, 15000);
		const query = search.value.trim();
		if (pageObserver) pageObserver.unobserve(sentinel);
		grid.setAttribute('aria-busy', 'true');
		loader.hidden = false;
		errorMessage.hidden = true;
		loadMore.hidden = true;
		restartOnRetry = false;
		try {
			const url = new URL(results.dataset.fetchUrl, window.location.href);
			if (query) url.searchParams.set('q', query);
			if (cursor) url.searchParams.set('cursor', cursor);
			const response = await fetch(url, {
				credentials: 'same-origin',
				signal: activeRequest.signal
			});
			if (controller !== activeRequest) return;
			if (response.status === 401) {
				errorMessage.textContent = results.dataset.sessionError;
				errorMessage.hidden = false;
				return;
			}
			if (response.status === 409) restartOnRetry = true;
			if (!response.ok) throw new Error('Could not fetch recipes');
			const data = await response.json();
			if (controller !== activeRequest) return;
			appendRecipes(data.html);
			cursor = data.next_cursor;
			hasMore = cursor !== null;
			const noResults = !hasMore && !grid.firstElementChild;
			empty.hidden = !noResults || query !== '';
			noMatches.hidden = !noResults || query === '';
		} catch (error) {
			if (controller !== activeRequest) return;
			errorMessage.textContent = results.dataset.loadError;
			errorMessage.hidden = false;
			loadMore.textContent = loadMore.dataset.retry;
			loadMore.hidden = false;
		} finally {
			clearTimeout(timeout);
			if (controller === activeRequest) {
				controller = null;
				grid.setAttribute('aria-busy', 'false');
				loader.hidden = true;

				if (errorMessage.hidden && hasMore) {
					// Watch again in case the next batch still won't fill the viewport
					if (pageObserver) {
						pageObserver.observe(sentinel);
					} else {
						loadMore.textContent = loadMore.dataset.more;
						loadMore.hidden = false;
					}
				}
			}
		}
	}
	// Search, this waits for a short pause in typing before the results are requested
	function searchRecipes() {
		clearTimeout(searchTimer);
		resetRecipes();
		if (categoryCount) categoryCount.hidden = search.value.trim() !== '';

		searchTimer = setTimeout(function() {
			searchTimer = null;
			loadRecipePage();
		}, 250);
	}
	search.addEventListener('input', function(event) {
		if (!event.isComposing) searchRecipes();
	});
	search.addEventListener('compositionend', searchRecipes);
	loadMore.addEventListener('click', function() {
		if (restartOnRetry) resetRecipes();
		loadRecipePage();
	});
	// The desktop category pane is hidden at narrow widths
	function startRecipes() {
		if (!results.getClientRects().length) return;
		window.removeEventListener('resize', startRecipes);
		if (categoryCount) categoryCount.hidden = search.value.trim() !== '';
		loadRecipePage();
	}
	window.addEventListener('resize', startRecipes);
	startRecipes();
});