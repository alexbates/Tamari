function msgtoggle() {
    var loginerror = document.getElementById('errorlogin');
    var emailerror = document.getElementById('erroremail');
    var passworderror = document.getElementById('errorpassword');
    if (loginerror != null && emailerror == null && passworderror == null)
    {
        document.getElementById("b1box").style.height="353px";
        document.getElementById("b1box").style.marginTop="-176px";
        document.getElementById("b1bottom").style.height="299px";
    }
    if (loginerror == null && emailerror != null && passworderror == null)
    {
        document.getElementById("b1box").style.height="329px";
        document.getElementById("b1box").style.marginTop="-164px";
        document.getElementById("b1bottom").style.height="275px";
    }
    if (loginerror == null && emailerror == null && passworderror != null)
    {
        document.getElementById("b1box").style.height="329px";
        document.getElementById("b1box").style.marginTop="-164px";
        document.getElementById("b1bottom").style.height="275px";
    }
    if (loginerror == null && emailerror != null && passworderror != null)
    {
        document.getElementById("b1box").style.height="344px";
        document.getElementById("b1box").style.marginTop="-172px";
        document.getElementById("b1bottom").style.height="290px";
    }
    if (loginerror != null && emailerror != null && passworderror != null)
    {
        document.getElementById("b1box").style.height="385px";
        document.getElementById("b1box").style.marginTop="-192px";
        document.getElementById("b1bottom").style.height="331px";
    }
}