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
        if(localStorage.getItem("accentcolor") == "dark-green") {var accentcolor = "dark-green";}
		if(localStorage.getItem("accentcolor") == "dark-purple") {var accentcolor = "dark-purple";}
		if(localStorage.getItem("accentcolor") == "dark-pink") {var accentcolor = "dark-pink";}
		if(localStorage.getItem("accentcolor") == "light-blue") {var accentcolor = "light-blue";}
		if(localStorage.getItem("accentcolor") == "light-green") {var accentcolor = "light-green";}
		if(localStorage.getItem("accentcolor") == "light-purple") {var accentcolor = "light-purple";}
		if(localStorage.getItem("accentcolor") == "light-pink") {var accentcolor = "light-pink";}
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
        }
        else if (theme === "dark" && useraccentcolor === "green") {
            document.documentElement.setAttribute("data-theme", "dark");
            document.documentElement.setAttribute("data-accentcolor", "dark-green");
        }
        else if (theme === "dark" && useraccentcolor === "purple") {
            document.documentElement.setAttribute("data-theme", "dark");
            document.documentElement.setAttribute("data-accentcolor", "dark-purple");
        }
        else if (theme === "dark" && useraccentcolor === "pink") {
            document.documentElement.setAttribute("data-theme", "dark");
            document.documentElement.setAttribute("data-accentcolor", "dark-pink");
        }
        else if (theme === "light" && useraccentcolor === "blue") {
            document.documentElement.setAttribute("data-theme", "light");
            document.documentElement.setAttribute("data-accentcolor", "light-blue");
        }
        else if (theme === "light" && useraccentcolor === "green") {
            document.documentElement.setAttribute("data-theme", "light");
            document.documentElement.setAttribute("data-accentcolor", "light-green");
            console.log("test")
        }
        else if (theme === "light" && useraccentcolor === "purple") {
            document.documentElement.setAttribute("data-theme", "light");
            document.documentElement.setAttribute("data-accentcolor", "light-purple");
        }
        else {
            document.documentElement.setAttribute("data-theme", "light");
            document.documentElement.setAttribute("data-accentcolor", "light-pink");
        }
    }
}
// This always runs, after "data-theme" attribute is set
function themeElements() {
    // Assign settings, add recipe, prev, next icon to constants
    const settingsImg = document.getElementById("settingsimg");
    const addRecipeImg = document.getElementById("addrecipeimg");
    const prevImg = document.getElementById("previmg");
    const nextImg = document.getElementById("nextimg");
    var trashImages = document.querySelectorAll('img.trashimg');
    // Check if data-theme attribute is set to light
    if (document.documentElement.getAttribute("data-theme") === "light") {
        // If light, switch settings, add recipe, prev, next icon
        if (settingsImg !== null) {settingsImg.src = "/static/settings-light.png";}
        if (addRecipeImg !== null) {addRecipeImg.src = "/static/add-recipe-button-light.png";}
        if (prevImg !== null) {prevImg.src = "/static/prev-light.png";}
        if (nextImg !== null) {nextImg.src = "/static/next-light.png";}
        if (trashImages !== null) {
            trashImages.forEach(function(img) {img.src = "/static/trash-light.png";});
        }
    }
    // Check if data-theme attribute is set to dark
    if (document.documentElement.getAttribute("data-theme") === "dark") {
        // If dark, switch settings, add recipe, prev, next icon
        if (settingsImg !== null) {settingsImg.src = "/static/settings-dark.png";}
        if (addRecipeImg !== null) {addRecipeImg.src = "/static/add-recipe-button-dark.png";}
        if (prevImg !== null) {prevImg.src = "/static/prev-dark.png";}
        if (nextImg !== null) {nextImg.src = "/static/next-dark.png";}
        if (trashImages !== null) {
            trashImages.forEach(function(img) {img.src = "/static/trash-dark.png";});
        }
    }
}