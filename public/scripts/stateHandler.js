$(function() {
    var editor = window.exports.editor;

    history.replaceState({id: 0}, "home", "/");

    var toggleEditor = editor.toggleEditor;
    editor.toggleEditor = function() {
        if (editor.isOpen()) {
            history.back();
        } else {
            history.pushState({id: 1}, "editor", "/editor");
            toggleEditor();
        }
    }

    $(window).on("popstate", function(e) {
        if (!e.originalEvent.state)
            return true;
        if (e.originalEvent.state.id == 0 && editor.isOpen())
            toggleEditor();
        else if (e.originalEvent.state.id == 1 && !editor.isOpen())
            toggleEditor();
    });
});