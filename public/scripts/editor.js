$(function() {

    //============================================================
    // Editor initialization
    //============================================================

    var editor = CodeMirror($("#code-panel .content")[0], {
        theme: "neo",
        mode: "instaparse",
        lineWrapping: true,
        lineNumbers: true,
        autofocus: true,
        indentUnit: 4,
        styleActiveLine: true,
        gutters: ["CodeMirror-linenumbers", "CodeMirror-spacegutter"]
    });

    //============================================================
    // Editor API
    //============================================================
    window.exports.editor = {};

    var isEditorOpen = false;

    //------------------------------------------------------------
    // Determine if editor is open or not
    //------------------------------------------------------------

    var isOpen = function() {
        return isEditorOpen;
    };

    //------------------------------------------------------------
    // Determine if editor is open or not
    //------------------------------------------------------------

    var language = function() {
        return $("#language .dropdown").text();
    }

    //------------------------------------------------------------
    // Toggle the editor
    //------------------------------------------------------------
    var toggleScroll = function() {
        $("body").toggleClass("hideScrollBar");
        // TODO: Handle background scrolling
    };

    var toggleEditor = function() {
        isEditorOpen = !isEditorOpen;
        $("#editor").toggle();
        toggleScroll();
        if (isEditorOpen) {
            editor.refresh();
            editor.focus();
        }
    };

    window.exports.editor.isOpen = isOpen;
    window.exports.editor.language = language;
    window.exports.editor.toggleEditor = toggleEditor;

    //============================================================
    // Editor nav handlers
    //============================================================

    // Handler for languages button
    $("#language .subitems").hide();
    $("#language").hover(function (e) {
        $("#language .subitems").toggle();
    });
    $("#language .subitems").click(function(e) {
        $("#language .subitems").toggle();
        var newLanguage = $(e.target).text();
        $("#language .dropdown").text(newLanguage)
        $("#language .subitems .subitem").remove();
        _.each(window.exports.globals.languages, function(language) {
            if (language == newLanguage) return;
            $("<div>").addClass("subitem").text(language).appendTo("#language .subitems");
        });
    });

    // Handler for key presses
    $(document).keyup(function (e) {
        var key = e.which;
        // on ESC quit editor
        if (key == 27) {
            if (isEditorOpen)
                toggleEditor();
        }
    });
});