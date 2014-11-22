$(document).ready(function() {
    Prism.languages.instaparse = {
        "comment": /#.*/g,
        "tag": /<head>|<objects>|<body>/g,
        "class": {
            pattern: /^\w+$/gm,
            alias: "function"
        },
        "string": /"[^"]"/g,
        "field": {
            pattern: /\w+:(list\s*\(\s*\w+\s*\)|\w+)(:(\w+|\+|\*)(\!)?)?\s*/gm,
            inside: {
                "variable": /^\w+/,
                "class": {
                    pattern: /(list\s*\(\s*\w+\s*\)|\w+)/,
                    alias: "function"
                },
                "operator": {
                    pattern: /(\w+|\+|\*)(\!)?/
                }
            }
        },
        "keyword": /delimiter/
    };
});