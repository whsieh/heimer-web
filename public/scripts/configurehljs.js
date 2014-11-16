var language = function(hljs) {
    return {};
};

// Configure highlight.js to only load instaparser
hljs.registerLanguage("InstaParser", language);
hljs.configure({
    tabReplace: "  ",
    languages: ["InstaParser", "python"]
});

hljs.initHighlightingOnLoad()
