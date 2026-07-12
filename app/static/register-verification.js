function msgtoggle() {
    var emailerror = document.getElementById('erroremail');
    if (emailerror != null)
    {
        document.getElementById("b1box").style.height="238px";
        document.getElementById("b1box").style.marginTop="-119px";
        document.getElementById("b1bottom").style.height="184px";
    }
    else
    {
        document.getElementById("b1box").style.height="223px";
        document.getElementById("b1box").style.marginTop="-112px";
        document.getElementById("b1bottom").style.height="169px";
    }
}
