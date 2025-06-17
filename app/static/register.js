function msgtoggle() {
    var emailerror = document.getElementById('erroremail');
    var password1error = document.getElementById('errorpassword1');
    var password2error = document.getElementById('errorpassword2');
    if (emailerror != null && password1error != null && password2error != null)
    {
        document.getElementById("b1box").style.height="385px";
        document.getElementById("b1box").style.marginTop="-192px";
        document.getElementById("b1bottom").style.height="331px";
    }
    if (emailerror != null && password1error != null && password2error == null)
    {
        document.getElementById("b1box").style.height="370px";
        document.getElementById("b1box").style.marginTop="-185px";
        document.getElementById("b1bottom").style.height="316px";
    }
    if (emailerror == null && password1error != null && password2error != null)
    {
        document.getElementById("b1box").style.height="370px";
        document.getElementById("b1box").style.marginTop="-185px";
        document.getElementById("b1bottom").style.height="316px";
    }
    if (emailerror != null && password1error == null && password2error != null)
    {
        document.getElementById("b1box").style.height="370px";
        document.getElementById("b1box").style.marginTop="-185px";
        document.getElementById("b1bottom").style.height="316px";
    }
    if (emailerror != null && password1error == null && password2error == null)
    {
        document.getElementById("b1box").style.height="354px";
        document.getElementById("b1box").style.marginTop="-177px";
        document.getElementById("b1bottom").style.height="300px";
    }
    if (emailerror == null && password1error != null && password2error == null)
    {
        document.getElementById("b1box").style.height="354px";
        document.getElementById("b1box").style.marginTop="-177px";
        document.getElementById("b1bottom").style.height="300px";
    }
    if (emailerror == null && password1error == null && password2error != null)
    {
        document.getElementById("b1box").style.height="354px";
        document.getElementById("b1box").style.marginTop="-177px";
        document.getElementById("b1bottom").style.height="300px";
    }
}