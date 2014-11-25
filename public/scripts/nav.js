$(function() {
    //============================================================
    // Nav setup
    //============================================================

    // Offset the navbar height
    var topOffset = $("#navbar").innerHeight();

    //============================================================
    // Nav event handlers
    //============================================================

    // Animation for brand click
    $("#brand a").click(function (e) {
        var scrollFrom = $(document).scrollTop();
        var scrollTo = 0;

        $("html, body").animate({
            scrollTop: scrollTo
        }, Math.abs(scrollTo - scrollFrom) / 1.75);

        return false;
    });

    // Use button click
    $("#use").click(function (e) {
        window.exports.editor.toggleEditor();
        return false;
    });

    //============================================================
    // Nav popup bubble handlers
    //============================================================

    // Controlling popup bubbles
    $("#github-popup,#download-popup,#use-popup").hide();

    $("#download").hover(function (e) {
        $("#download-popup").fadeToggle(100);
    });

    $("#github").hover(function (e) {
        $("#github-popup").fadeToggle(100);
    });

    $("#use").hover(function (e) {
        $("#use-popup").fadeToggle(100);
    });
});
