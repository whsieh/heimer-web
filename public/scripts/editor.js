$(document).ready(function() {
    var isEditorOpen = false;
    var toggleScroll = function() {
        $("body").toggleClass("hideScrollBar");
        $("body").on("scroll touchmove mousewheel", function (e) {
            return !isEditorOpen;
        });
    }

    var toggleEditor = function() {
        isEditorOpen = !isEditorOpen;
        $("#editor").toggle();
        toggleScroll();
    }

    window.export.toggleEditor = toggleEditor;

    $(window).keypress(function(e) {
        var code = e.keyCode || e.which;
        if (code == 101) {
            window.export.toggleEditor();
        }
    });
});