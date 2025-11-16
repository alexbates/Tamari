/* 
THEME AND ACCENT COLOR
This runs on all pages with Navbar.
*/ 

// This runs if user is not authenticated
function themeNoAuth() {
    // Set theme variable to dark by default, prior to detection
    var theme="dark";    
	var accentcolor = "dark-blue";
    // Check whether we have already used local storage to set theme
    if(localStorage.getItem("theme")){
        // If we have used local storage to set theme and theme is light, set theme variable to light
        if(localStorage.getItem("theme") == "light") {var theme = "light";}
    } 
    // Check if the browser theme setting is light mode, set theme to light if so
    else if(window.matchMedia("(prefers-color-scheme: light)").matches) {var theme = "light";}
	// Check if the browser theme setting is dark mode, set theme to dark if so
    else if(window.matchMedia("(prefers-color-scheme: dark)").matches) {var theme = "dark";}
	// Set theme to light if prefers-color-scheme AND localStorage theme is NOT set
	else {var theme = "light";}
    // If theme variable is light following detection, set "data-theme" attribute for the document
    if (theme=="light") {document.documentElement.setAttribute("data-theme", "light");}
	// Else set "data-theme" attribute for document to dark
	else {document.documentElement.setAttribute("data-theme", "dark");}
	// Check whether we have already used local storage to set accentcolor
    if(localStorage.getItem("accentcolor")){
        var lsaccent = localStorage.getItem("accentcolor");
        if(theme=="dark") {
            if(lsaccent == "dark-blue" || lsaccent == "light-blue") {var accentcolor = "dark-blue";}
            if(lsaccent == "dark-green" || lsaccent == "light-green") {var accentcolor = "dark-green";}
            if(lsaccent == "dark-purple" || lsaccent == "light-purple") {var accentcolor = "dark-purple";}
            if(lsaccent == "dark-pink" || lsaccent == "light-pink") {var accentcolor = "dark-pink";}
        }
        else {
            if(lsaccent == "dark-blue" || lsaccent == "light-blue") {var accentcolor = "light-blue";}
            if(lsaccent == "dark-green" || lsaccent == "light-green") {var accentcolor = "light-green";}
            if(lsaccent == "dark-purple" || lsaccent == "light-purple") {var accentcolor = "light-purple";}
            if(lsaccent == "dark-pink" || lsaccent == "light-pink") {var accentcolor = "light-pink";}
        }
    } 
    else {
        if(theme=="dark") {var accentcolor = "dark-blue"}
        if(theme=="light") {var accentcolor = "light-blue"}
    }
	// Set "data-accentcolor" attribute based on value of accentcolor variable
    if (accentcolor=="dark-green") {document.documentElement.setAttribute("data-accentcolor", "dark-green");}
	else if (accentcolor=="dark-purple") {document.documentElement.setAttribute("data-accentcolor", "dark-purple");}
	else if (accentcolor=="dark-pink") {document.documentElement.setAttribute("data-accentcolor", "dark-pink");}
	else if (accentcolor=="light-blue") {document.documentElement.setAttribute("data-accentcolor", "light-blue");}
	else if (accentcolor=="light-green") {document.documentElement.setAttribute("data-accentcolor", "light-green");}
	else if (accentcolor=="light-purple") {document.documentElement.setAttribute("data-accentcolor", "light-purple");}
	else if (accentcolor=="light-pink") {document.documentElement.setAttribute("data-accentcolor", "light-pink");}
	else {document.documentElement.setAttribute("data-accentcolor", "dark-blue");}
}
// This runs if user is authenticated
function themeAuth(usertheme, useraccentcolor) {
    // If user's theme setting is set to "Light" or "Dark"
    if (usertheme !== null) {
        document.documentElement.setAttribute("data-theme", usertheme);
        localStorage.setItem('theme', usertheme);
        document.documentElement.setAttribute("data-accentcolor", useraccentcolor);
        localStorage.setItem('accentcolor', useraccentcolor);
    }
    // If user's theme setting is set to "System Default"
    else {
        // Remove theme from localStorage since user wants to use system default
        localStorage.removeItem("theme");
        // Set theme variable to light by default, prior to detection
        var theme="dark";
        // Check if the browser theme setting is light mode, set theme to light if so
        if(window.matchMedia("(prefers-color-scheme: light)").matches) {var theme = "light";}
	    // Check if the browser theme setting is dark mode, set theme to dark if so
        else if(window.matchMedia("(prefers-color-scheme: dark)").matches) {var theme = "dark";}
	    // Set theme to light if prefers-color-scheme is NOT set
	    else {var theme = "light";}
        // Set document attributes based on prefers-color-scheme and accentcolor user preference
        if (theme === "dark" && useraccentcolor === "blue") {
            document.documentElement.setAttribute("data-theme", "dark");
            document.documentElement.setAttribute("data-accentcolor", "dark-blue");
            localStorage.setItem('accentcolor', 'dark-blue');
        }
        else if (theme === "dark" && useraccentcolor === "green") {
            document.documentElement.setAttribute("data-theme", "dark");
            document.documentElement.setAttribute("data-accentcolor", "dark-green");
            localStorage.setItem('accentcolor', 'dark-green');
        }
        else if (theme === "dark" && useraccentcolor === "purple") {
            document.documentElement.setAttribute("data-theme", "dark");
            document.documentElement.setAttribute("data-accentcolor", "dark-purple");
            localStorage.setItem('accentcolor', 'dark-purple');
        }
        else if (theme === "dark" && useraccentcolor === "pink") {
            document.documentElement.setAttribute("data-theme", "dark");
            document.documentElement.setAttribute("data-accentcolor", "dark-pink");
            localStorage.setItem('accentcolor', 'dark-pink');
        }
        else if (theme === "light" && useraccentcolor === "blue") {
            document.documentElement.setAttribute("data-theme", "light");
            document.documentElement.setAttribute("data-accentcolor", "light-blue");
            localStorage.setItem('accentcolor', 'light-blue');
        }
        else if (theme === "light" && useraccentcolor === "green") {
            document.documentElement.setAttribute("data-theme", "light");
            document.documentElement.setAttribute("data-accentcolor", "light-green");
            localStorage.setItem('accentcolor', 'light-green');
        }
        else if (theme === "light" && useraccentcolor === "purple") {
            document.documentElement.setAttribute("data-theme", "light");
            document.documentElement.setAttribute("data-accentcolor", "light-purple");
            localStorage.setItem('accentcolor', 'light-purple');
        }
        else {
            document.documentElement.setAttribute("data-theme", "light");
            document.documentElement.setAttribute("data-accentcolor", "light-pink");
            localStorage.setItem('accentcolor', 'light-pink');
        }
    }
}
// This always runs, after "data-theme" attribute is set
function themeElements() {
    // Assign icons to constants
    const settingsImg = document.getElementById("settingsimg");
    const addRecipeImg = document.getElementById("addrecipeimg");
    const prevImg = document.getElementById("previmg");
    const nextImg = document.getElementById("nextimg");
    const trashImg = document.getElementById("trashimg");
    const favoriteImg = document.getElementById("favoriteimg");
    const publicImg = document.getElementById("publicimg");
    const scheduleImg = document.getElementById("scheduleimg");
    const editImg = document.getElementById("editimg");
    const searchImg = document.getElementById("searchimg");
    const saveImg = document.getElementById("saveimg");
    var trashImages = document.querySelectorAll('img.trashimg');
    const accountPic1 = document.getElementById("account-pic1");
    const accountPic2 = document.getElementById("account-pic2");
    const accountPic3 = document.getElementById("account-pic3");
    const accountPic4 = document.getElementById("account-pic4");
    const accountBlue = document.getElementById("account-blue");
    const accountGreen = document.getElementById("account-green");
    const accountPurple = document.getElementById("account-purple");
    const accountPink = document.getElementById("account-pink");
	var informationImages = document.querySelectorAll('img.inf-image');
	const scrollRight = document.getElementById("scroll-right");
	const scrollLeft = document.getElementById("scroll-left");
	const scrollRightRecip = document.getElementById("scroll-right-recip");
	const scrollLeftRecip = document.getElementById("scroll-left-recip");
	const barcodeCameraImg = document.getElementById("barcodecameraimg");
	const printImg = document.getElementById("printimg");
	const pdfImg = document.getElementById("pdfimg");
	const footerRecipes = document.getElementById("footerRecipes");
	const footerExplore = document.getElementById("footerExplore");
	const footerLists = document.getElementById("footerLists");
	const footerPlanner = document.getElementById("footerPlanner");
	const footerLogin = document.getElementById("footerLogin");
	const footerRegister = document.getElementById("footerRegister");
    // Check if data-theme attribute is set to light
    if (document.documentElement.getAttribute("data-theme") === "light") {
        // If light, switch icons
        if (settingsImg !== null) {settingsImg.src = "/static/settings-light.png";}
        if (addRecipeImg !== null) {addRecipeImg.src = "/static/add-recipe-button-light.png";}
        if (prevImg !== null) {prevImg.src = "/static/prev-light.png";}
        if (nextImg !== null) {nextImg.src = "/static/next-light.png";}
        if (trashImg !== null) {trashImg.src = "/static/trash-light.png";}
        if (favoriteImg !== null) {favoriteImg.src = "/static/favorite-recipe-light.png";}
        if (publicImg !== null) {publicImg.src = "/static/public-private-light.png";}
        if (scheduleImg !== null) {scheduleImg.src = "/static/schedule-light.png";}
        if (editImg !== null) {editImg.src = "/static/edit-recipe-light.png";}
        if (searchImg !== null) {searchImg.src = "/static/search-light.png";}
        if (saveImg !== null) {saveImg.src = "/static/save-light.png";}
        if (trashImages !== null) {
            trashImages.forEach(function(img) {img.src = "/static/trash-light.png";});
        }
        if (accountPic1 !== null) {accountPic1.src = "/static/account-pic1-light.png";}
        if (accountPic2 !== null) {accountPic2.src = "/static/account-pic2-light.png";}
        if (accountPic3 !== null) {accountPic3.src = "/static/account-pic3-light.png";}
        if (accountPic4 !== null) {accountPic4.src = "/static/account-pic4-light.png";}
        if (accountBlue !== null) {accountBlue.src = "/static/account-blue-light.png";}
        if (accountGreen !== null) {accountGreen.src = "/static/account-green-light.png";}
        if (accountPurple !== null) {accountPurple.src = "/static/account-purple-light.png";}
        if (accountPink !== null) {accountPink.src = "/static/account-pink-light.png";}
		if (informationImages !== null) {
            informationImages.forEach(function(img) {img.src = "/static/information-light.png";});
        }
		if (scrollRight !== null) {scrollRight.src = "/static/navbar-scroll-right-light.png";}
		if (scrollLeft !== null) {scrollLeft.src = "/static/navbar-scroll-left-light.png";}
		if (scrollRightRecip !== null) {scrollRightRecip.src = "/static/navbar-scroll-right-light.png";}
		if (scrollLeftRecip !== null) {scrollLeftRecip.src = "/static/navbar-scroll-left-light.png";}
		if (barcodeCameraImg !== null) {barcodeCameraImg.src = "/static/barcode-camera-light.png";}
		if (printImg !== null) {printImg.src = "/static/print-light.png";}
		if (pdfImg !== null) {pdfImg.src = "/static/download-light.png";}
		if (footerRecipes !== null) {footerRecipes.src = "/static/footer-recipes-light.png";}
		if (footerExplore !== null) {footerExplore.src = "/static/footer-explore-light.png";}
		if (footerLists !== null) {footerLists.src = "/static/footer-lists-light.png";}
		if (footerPlanner !== null) {footerPlanner.src = "/static/footer-planner-light.png";}
		if (footerLogin !== null) {footerLogin.src = "/static/footer-login-light.png";}
		if (footerRegister !== null) {footerRegister.src = "/static/footer-register-light.png";}
    }
    // Check if data-theme attribute is set to dark
    if (document.documentElement.getAttribute("data-theme") === "dark") {
        // If dark, switch icons
        if (settingsImg !== null) {settingsImg.src = "/static/settings-dark.png";}
        if (addRecipeImg !== null) {addRecipeImg.src = "/static/add-recipe-button-dark.png";}
        if (prevImg !== null) {prevImg.src = "/static/prev-dark.png";}
        if (nextImg !== null) {nextImg.src = "/static/next-dark.png";}
        if (trashImg !== null) {trashImg.src = "/static/trash-dark.png";}
        if (favoriteImg !== null) {favoriteImg.src = "/static/favorite-recipe-dark.png";}
        if (publicImg !== null) {publicImg.src = "/static/public-private-dark.png";}
        if (scheduleImg !== null) {scheduleImg.src = "/static/schedule-dark.png";}
        if (editImg !== null) {editImg.src = "/static/edit-recipe-dark.png";}
        if (searchImg !== null) {searchImg.src = "/static/search-dark.png";}
        if (saveImg !== null) {saveImg.src = "/static/save-dark.png";}
        if (trashImages !== null) {
            trashImages.forEach(function(img) {img.src = "/static/trash-dark.png";});
        }
        if (accountPic1 !== null) {accountPic1.src = "/static/account-pic1-dark.png";}
        if (accountPic2 !== null) {accountPic2.src = "/static/account-pic2-dark.png";}
        if (accountPic3 !== null) {accountPic3.src = "/static/account-pic3-dark.png";}
        if (accountPic4 !== null) {accountPic4.src = "/static/account-pic4-dark.png";}
        if (accountBlue !== null) {accountBlue.src = "/static/account-blue-dark.png";}
        if (accountGreen !== null) {accountGreen.src = "/static/account-green-dark.png";}
        if (accountPurple !== null) {accountPurple.src = "/static/account-purple-dark.png";}
        if (accountPink !== null) {accountPink.src = "/static/account-pink-dark.png";}
		if (informationImages !== null) {
            informationImages.forEach(function(img) {img.src = "/static/information-dark.png";});
        }
		if (scrollRight !== null) {scrollRight.src = "/static/navbar-scroll-right-dark.png";}
		if (scrollLeft !== null) {scrollLeft.src = "/static/navbar-scroll-left-dark.png";}
		if (scrollRightRecip !== null) {scrollRightRecip.src = "/static/navbar-scroll-right-dark.png";}
		if (scrollLeftRecip !== null) {scrollLeftRecip.src = "/static/navbar-scroll-left-dark.png";}
		if (barcodeCameraImg !== null) {barcodeCameraImg.src = "/static/barcode-camera-dark.png";}
		if (printImg !== null) {printImg.src = "/static/print-dark.png";}
		if (pdfImg !== null) {pdfImg.src = "/static/download-dark.png";}
		if (footerRecipes !== null) {footerRecipes.src = "/static/footer-recipes-dark.png";}
		if (footerExplore !== null) {footerExplore.src = "/static/footer-explore-dark.png";}
		if (footerLists !== null) {footerLists.src = "/static/footer-lists-dark.png";}
		if (footerPlanner !== null) {footerPlanner.src = "/static/footer-planner-dark.png";}
		if (footerLogin !== null) {footerLogin.src = "/static/footer-login-dark.png";}
		if (footerRegister !== null) {footerRegister.src = "/static/footer-register-dark.png";}
    }
}