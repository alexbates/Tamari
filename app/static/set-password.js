function msgtoggle() {
    var password1error = document.getElementById('errorpassword1');
    var password2error = document.getElementById('errorpassword2');
    if (password1error != null && password2error != null)
    {
        document.getElementById("b1box").style.height="299px";
        document.getElementById("b1box").style.marginTop="-149px";
        document.getElementById("b1bottom").style.height="245px";
    }
    if (password1error != null && password2error == null)
    {
        document.getElementById("b1box").style.height="283px";
        document.getElementById("b1box").style.marginTop="-141px";
        document.getElementById("b1bottom").style.height="229px";
    }
    if (password1error == null && password2error != null)
    {
        document.getElementById("b1box").style.height="283px";
        document.getElementById("b1box").style.marginTop="-141px";
        document.getElementById("b1bottom").style.height="229px";
    }
}