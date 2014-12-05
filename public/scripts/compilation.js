$(function() {

    var editor = window.exports.editor
    var gencode = window.exports.gencode

    var output = {}

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

            var mainFileContents = decodeURI(result.main.content)
            var utilFileContents = decodeURI(result.util.content)
            editor.selectOutput(editor.addOutput(editorLanguage, result.main.name, mainFileContents));
            editor.addOutput(editorLanguage, result.util.name, utilFileContents);
            output = {}
            output[result.main.name] = mainFileContents;
            output[result.util.name] = utilFileContents;

            if (result.classes.length != 0) {
                var filenames = [];
                var contents = [];
                _.each(result.classes, function(classfile) {
                    filenames.push(classfile.name);
                    var classFileContents = decodeURI(classfile.content);
                    contents.push(classFileContents);
                    output[classfile.name] = classFileContents;
                });
                editor.addOutputDropdown(editorLanguage, "Classes", filenames, contents);
            } else {
                var fileContents = decodeURI(result.data.content);
                editor.addOutput(editorLanguage, result.data.name, dataFileContents);
                output[result.data.name] = dataFileContents;
            }
        });
    });
    $("#downloadOutput").click(function() {
        var zip = new JSZip();
        var root = zip.folder("src");
        for (var filename in output)
            root.file(filename, output[filename]);

        var content = zip.generate( {type: "blob"} );
        saveToFile(content, "parser.zip");
    });
});