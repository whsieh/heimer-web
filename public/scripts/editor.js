$(function() {
    // Append code editor
    var editor = CodeMirror($("#code-panel .content")[0], {
            lineWrapping: true,
            lineNumbers: true,
            styleActiveLine: true,
            gutters: ["CodeMirror-linenumbers", "CodeMirror-spacegutter"]
        });

    // Handler for languages button
    $("#language .subitems").hide();
    $("#language").hover(function (e) {
        $("#language .subitems").toggle();
    });

    // Handler for handling text pasting in the editor
    // $("#code-panel .content pre").on("paste", function(e) {
    //     var text = "";
    //     if (e.clipboardData)
    //         text = e.clipboardData.getData('text/plain');
    //     else if (window.clipboardData)
    //         text = window.clipboardData.getData('Text');
    //     else if (e.originalEvent.clipboardData)
    //         text = $('<div></div>').text(e.originalEvent.clipboardData.getData('text'))
    //     document.execCommand('insertHTML', false, $(text).html());
    //     return false;
    // });

    

    // Export editor util functions
    window.export.editor = {};

    var isEditorOpen = false;
    var toggleScroll = function() {
        $("body").toggleClass("hideScrollBar");
        // Handle removing editor
    }

    var toggleEditor = function() {
        isEditorOpen = !isEditorOpen;
        $("#editor").toggle();
        toggleScroll();
        if (isEditorOpen) {
            editor.refresh();
            editor.focus();
        }
    }

    window.export.editor.toggleEditor = toggleEditor;

    // HACKHACK TO BE REMOVED
    $(window).keypress(function(e) {
        var code = e.keyCode || e.which;
        if (code == 92) {
            window.export.editor.toggleEditor();
        }
    });
});