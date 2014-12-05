$(function() {

    var editor = window.exports.editor
    var gencode = window.exports.gencode

    // Helper to convert language to CodeMirror language types
    var convertLanguageName = function(name) {
        if (name == "java") {
            return "text/x-java";
        } else if (name == "c++") {
            return "text/x-c++hdr";
        } else {
            return name;
        }
    }

    // Handle compilation click
    $("#compile").click(function() {
        editor.clearOutputNav();

        var formatFile = editor.getContent();
        var language = editor.getLanguage();

        gencode(language, formatFile, function(result) {
            if (result.hasOwnProperty("error")) {
                console.log(result.error);
                return;
            }

            var editorLanguage = convertLanguageName(language);

            editor.selectOutput(editor.addOutput(editorLanguage, result.main.name, decodeURI(result.main.content)));
            editor.addOutput(editorLanguage, result.util.name, decodeURI(result.util.content));
            if (result.classes.length != 0) {
                var filenames = [];
                var contents = [];
                _.each(result.classes, function(classfile) {
                    filenames.push(classfile.name);
                    contents.push(decodeURI(classfile.content));
                });

                console.log(filenames, contents);

                editor.addOutputDropdown(editorLanguage, "Classes", filenames, contents);
            } else {
                editor.addOutput(editorLanguage, result.data.name, decodeURI(result.data.content));
            }
        });
    });

});