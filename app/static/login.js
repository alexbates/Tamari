function msgtoggle() {
    var loginerror = document.getElementById('errorlogin');
    var emailerror = document.getElementById('erroremail');
    var passworderror = document.getElementById('errorpassword');
    if (loginerror != null && emailerror == null && passworderror == null)
    {
        document.getElementById("b1box").style.height="345px";
        document.getElementById("b1box").style.marginTop="-172px";
        document.getElementById("b1bottom").style.height="291px";
    }
    if (loginerror == null && emailerror != null && passworderror == null)
    {
        document.getElementById("b1box").style.height="321px";
        document.getElementById("b1box").style.marginTop="-160px";
        document.getElementById("b1bottom").style.height="267px";
    }
    if (loginerror == null && emailerror == null && passworderror != null)
    {
        document.getElementById("b1box").style.height="321px";
        document.getElementById("b1box").style.marginTop="-160px";
        document.getElementById("b1bottom").style.height="267px";
    }
    if (loginerror == null && emailerror != null && passworderror != null)
    {
        document.getElementById("b1box").style.height="336px";
        document.getElementById("b1box").style.marginTop="-168px";
        document.getElementById("b1bottom").style.height="282px";
    }
    if (loginerror != null && emailerror != null && passworderror != null)
    {
        document.getElementById("b1box").style.height="377px";
        document.getElementById("b1box").style.marginTop="-188px";
        document.getElementById("b1bottom").style.height="323px";
    }
}
