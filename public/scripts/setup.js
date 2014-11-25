$(function() {
    
    //============================================================
    // Setup code in main page
    //============================================================

    var $code = $("#content code");

    $code.each(function(index, element) {
        var $element = $(element);
        var mode = "python";
        if ($element.attr("lang"))
            mode = $element.attr("lang");
        var content = $.trim($(element).text());
        // Replace every tag with a uneditable code mirror object
        CodeMirror(function(result) {
            $(element).replaceWith(result);
        }, {
            value: content,
            mode: mode,
            theme: "solarized dark",
            lineWrapping: true,
            lineNumbers: true,
            readOnly: "nocursor",
            gutters: ["CodeMirror-linenumbers", "CodeMirror-spacegutter"]
        });
    });


});