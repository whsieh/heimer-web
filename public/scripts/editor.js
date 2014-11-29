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
    // Editor nav handlers
    //============================================================

    // Always toggle subitems for dropdowns
    $("#editor .dropdown .subitems").hide();
    $("#editor .dropdown").hover(function (e) {
        $(e.target).closest(".dropdown").find(".subitems").toggle();
    });

    // Handle language dropdowns
    var currentLanguageSubitem = $("#language .subitem")[0];
    var $languageTabText = $("#language .text");
    $("#language .subitems").click(function (e) {
        var $clicked = $(e.target);
        var $current = $(currentLanguageSubitem);
        if ($clicked.hasClass("selected")) return;

        $current.removeClass("selected");
        $clicked.addClass("selected");
        $languageTabText.text($clicked.text());

        currentLanguageSubitem = e.target;
    });

    // Handler for key presses
    $(document).keyup(function (e) {
        var key = e.which;
        // on ESC quit editor
        if (key == 27) {
            if (isEditorOpen)
                window.exports.editor.toggleEditor();
        }
    });

    //============================================================
    // Editor API
    //============================================================
    window.exports.editor = {};

    var isEditorOpen = false;
    var currentOutputState = null;

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
            if (currentOutputState)
                currentOutputState.CodeMirror.refresh();
        }
    };

    //------------------------------------------------------------
    // Clear output nav
    //------------------------------------------------------------

    var clearOutputNav = function() {
        $("#output-panel nav .output").remove();
        $("#output-panel .content .CodeMirror").remove();
    };

    //------------------------------------------------------------
    // Add output tab
    //------------------------------------------------------------

    // Helper to handle click events for output tabs
    var handleClick = function(nextOutputState) {
        if (currentOutputState && currentOutputState.id.is(nextOutputState.id)) return;

        if (currentOutputState) {
            $(currentOutputState.CodeMirror.getWrapperElement()).hide();
            _.each(currentOutputState.$selectedItems, function(item) {
                item.removeClass("selected");
            });
            if (currentOutputState.deselectId && !currentOutputState.deselectId.is(nextOutputState.deselectId))
                currentOutputState.deselectFn();
        }

        $(nextOutputState.CodeMirror.getWrapperElement()).show();
        nextOutputState.CodeMirror.refresh();
        _.each(nextOutputState.$selectedItems, function(item) {
            item.addClass("selected");
        });
        if (nextOutputState.selectFn) nextOutputState.selectFn();

        currentOutputState = nextOutputState;
    };

    var addOutput = function(language, filename, content) {
        var $tab = $("<div>")
            .addClass("output").addClass("tab")
            .html(filename)
            .appendTo("#output-panel nav");

        var cm = CodeMirror($("#output-panel .content")[0], {
            theme: "neo",
            value: content,
            mode: language,
            lineWrapping: true,
            lineNumbers: true,
            readOnly: "nocursor",
            gutters: ["CodeMirror-linenumbers", "CodeMirror-spacegutter"]
        });

        var $output = $(cm.getWrapperElement());
        $output.hide();

        var outputState = {
            id: $tab,
            CodeMirror: cm,
            $selectedItems: [$tab],
        };

        // Event handling
        $tab.click(function (e) {
            handleClick(outputState);
        });

        return $tab[0];
    }

    //------------------------------------------------------------
    // Add output dropdown tab
    //------------------------------------------------------------

    var addOutputDropdown = function(language, defaultText, filenames, contents) {
        var $dropdown = $("<div>")
            .addClass("output").addClass("tab").addClass("dropdown")
            .appendTo("#output-panel nav")
            .append($("<div>").addClass("text").text(defaultText))

        var $subitems = $("<div>").addClass("subitems").appendTo($dropdown);
        $subitems.hide();

        $dropdown.hover(function (e) {
            $subitems.toggle();
        });

        var deselectFn = function() {
            $dropdown.find(".text").text(defaultText);
        };

        _.each(_.zip(filenames, contents), function(pair) {
            $subitem = $("<div>").addClass("subitem").text(pair[0]).appendTo($subitems);

            var cm = CodeMirror($("#output-panel .content")[0], {
                theme: "neo",
                value: pair[1],
                mode: language,
                lineWrapping: true,
                lineNumbers: true,
                readOnly: "nocursor",
                gutters: ["CodeMirror-linenumbers", "CodeMirror-spacegutter"]
            });

            var $output = $(cm.getWrapperElement());
            $output.toggle();

            var selectFn = function() {
                $dropdown.find(".text").text(pair[0]);
            };

            var outputState = {
                CodeMirror: cm,
                id: $subitem,
                $selectedItems: [$subitem, $dropdown],
                selectFn: selectFn,
                deselectId: $dropdown,
                deselectFn: deselectFn
            };

            // Event handling
            $subitem.click(function(e) {
                handleClick(outputState);
            });
        });

        return $subitems.find(".subitem");
    }

    //------------------------------------------------------------
    // Select a tab/subitem
    //------------------------------------------------------------

    var selectOutput = function(element) {
        $(element).click();
    }

    window.exports.editor.isOpen = isOpen;
    window.exports.editor.language = language;
    window.exports.editor.toggleEditor = toggleEditor;
    window.exports.editor.clearOutputNav = clearOutputNav;
    window.exports.editor.addOutputDropdown = addOutputDropdown;
    window.exports.editor.selectOutput = selectOutput;
});