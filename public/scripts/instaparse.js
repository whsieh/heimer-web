$(function() {

    // Define instaparse syntax highlighting
    CodeMirror.defineSimpleMode("instaparse", {
        start: [
            {
                regex: /#.*/g,
                token: "comment"
            },
            {
                regex: /"[^"]*"/,
                token: "string"
            },
            {
                regex: /\d+/,
                token: "number"
            },
            {
                regex: /(?:<head>|<objects>|<body>)/g,
                token: "header"
            },
            {
                regex: /^\w+$/gm,
                token: "def"
            },
            {
                regex: /(\w+)(?:(:(?:list\s*\(\s*(?:int|float|string|bool)\s*\)|int|float|string|bool))|(:\w+))(:(?:(?:\w+|\+|\*)\!?))?/g,
                token: ["variable", "builtin", "def", "operator"]
            },
            {
                regex: /delimiter/g,
                token: "keyword"
            },
            {
                regex: /\S+/,
                token: "error"
            }
        ]
    });

});