$(document).ready(function() {
    var isEditorOpen = false;
    var toggleScroll = function() {
        $("body").toggleClass("hideScrollBar");
        $("body").on("scroll touchmove mousewheel", function (e) {
            return !isEditorOpen;
        });
    }

    $(window).keypress(function(e) {
        var code = e.keyCode || e.which;
        if (code == 101) {
            isEditorOpen = !isEditorOpen;
            $("#editor").toggle();
            toggleScroll();
        }
    });
});