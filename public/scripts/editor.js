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
    window.exports.editor.toggleEditor = toggleEditor;

    //============================================================
    // Editor nav handlers
    //============================================================

    // Handler for languages button
    $("#language .subitems").hide();
    $("#language").hover(function (e) {
        $("#language .subitems").toggle();
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