/* 
SET APP SCALING
*/ 

// This runs if user is not authenticated
function scalingNoAuth() {
    // Set theme variable to dark by default, prior to checking local storage
    var scaling="normal";    
    // Check whether we have already used local storage to set scaling
    if(localStorage.getItem("scaling")){
        // If we have used local storage to set scaling and scaling is large, set scaling variable to large
        if(localStorage.getItem("scaling") == "large") {var scaling = "large";}
    } 
    // If scaling variable is large following detection, set "data-scaling" attribute for the document
    if (scaling=="large") {document.documentElement.setAttribute("data-scaling", "large");}
	// Else set "data-scaling" attribute for document to normal
	else {document.documentElement.setAttribute("data-scaling", "normal");}
}
// This runs if user is authenticated
function scalingAuth(userscaling) {
    // If user's theme setting is set to "Normal" or "Large"
    if (userscaling !== null) {
        document.documentElement.setAttribute("data-scaling", userscaling);
        localStorage.setItem('scaling', userscaling);
    }
}