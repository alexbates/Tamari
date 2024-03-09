function msgtoggle() {
    var password1error = document.getElementById('errorpassword1');
    var password2error = document.getElementById('errorpassword2');
    if (password1error != null && password2error != null)
    {
        document.getElementById("b1box").style.height="291px";
        document.getElementById("b1box").style.marginTop="-145px";
        document.getElementById("b1bottom").style.height="237px";
    }
    if (password1error != null && password2error == null)
    {
        document.getElementById("b1box").style.height="275px";
        document.getElementById("b1box").style.marginTop="-137px";
        document.getElementById("b1bottom").style.height="221px";
    }
    if (password1error == null && password2error != null)
    {
        document.getElementById("b1box").style.height="275px";
        document.getElementById("b1box").style.marginTop="-137px";
        document.getElementById("b1bottom").style.height="221px";
    }
}
