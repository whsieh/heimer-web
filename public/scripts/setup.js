$(function() {
    
    //============================================================
    // Setup code in main page
    //============================================================

    var $code = $("#content code");

    $code.each(function(index, element) {
        var $element = $(element);
        var mode = "instaparse";
        if ($element.attr("lang"))
            mode = $element.attr("lang");
        var content = $.trim($(element).text());
        // Replace every tag with a uneditable code mirror object
        CodeMirror(function(result) {
            $(element).replaceWith(result);
        }, {
            value: content,
            mode: mode,
            theme: "solarized light",
            lineWrapping: false,
            lineNumbers: true,
            readOnly: "nocursor",
            gutters: ["CodeMirror-linenumbers", "CodeMirror-spacegutter"]
        });
    });

    var $vs = $("#content .vs");

    $vs.each(function(index, element) {
        var height = Math.max.apply(Math, $(element).children().map(function() {
            return $(this).height();
        }));

        $(element).children().map(function() {
            $(this).height(height);
        });
    });


});