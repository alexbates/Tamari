function msgtoggle() {
    var emailerror = document.getElementById('erroremail');
    var password1error = document.getElementById('errorpassword1');
    var password2error = document.getElementById('errorpassword2');
    if (emailerror != null && password1error != null && password2error != null)
    {
        document.getElementById("b1box").style.height="373px";
        document.getElementById("b1box").style.marginTop="-186px";
        document.getElementById("b1bottom").style.height="319px";
    }
    if (emailerror != null && password1error != null && password2error == null)
    {
        document.getElementById("b1box").style.height="358px";
        document.getElementById("b1box").style.marginTop="-179px";
        document.getElementById("b1bottom").style.height="304px";
    }
    if (emailerror == null && password1error != null && password2error != null)
    {
        document.getElementById("b1box").style.height="358px";
        document.getElementById("b1box").style.marginTop="-179px";
        document.getElementById("b1bottom").style.height="304px";
    }
    if (emailerror != null && password1error == null && password2error != null)
    {
        document.getElementById("b1box").style.height="358px";
        document.getElementById("b1box").style.marginTop="-179px";
        document.getElementById("b1bottom").style.height="304px";
    }
    if (emailerror != null && password1error == null && password2error == null)
    {
        document.getElementById("b1box").style.height="342px";
        document.getElementById("b1box").style.marginTop="-171px";
        document.getElementById("b1bottom").style.height="288px";
    }
    if (emailerror == null && password1error != null && password2error == null)
    {
        document.getElementById("b1box").style.height="342px";
        document.getElementById("b1box").style.marginTop="-171px";
        document.getElementById("b1bottom").style.height="288px";
    }
    if (emailerror == null && password1error == null && password2error != null)
    {
        document.getElementById("b1box").style.height="342px";
        document.getElementById("b1box").style.marginTop="-171px";
        document.getElementById("b1bottom").style.height="288px";
    }
}
