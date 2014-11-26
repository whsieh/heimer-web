var express = require("express");
var router = express.Router();

var path = require("path");
var fs = require("fs");
var util = require("../util");


// Grab the sections to automatically generate the navigation
var order = JSON.parse(fs.readFileSync(path.join(__dirname, "../", "content", "order.json")));
var sections = [];

order.files.forEach(function(file) {
    if (!("name" in file || "filename" in file)) {
        console.log("Missing name or filename in order.json");
    }

    var name = file.name;
    var filename = file.filename;
    var subsections;
    if ("subsections" in file) {
        var subsections = file.subsections;
    } else {
        var subsections = [];
    }

    var content = fs.readFileSync(path.join(__dirname, "../", "content", filename), "utf8");

    sections.push({ name: name, content: content, subsections: subsections });
});

// Grab languages to generate the editor
var languages = JSON.parse(fs.readFileSync(path.join(__dirname, "../", "content", "languages.json"))).languages;

// Setup global variables to pass to the client
var globals = {languages: languages};

/* GET home page. */
router.get(["/", "/editor"], function(req, res) {
  res.render("index", { title: "InstaParse", sections: sections, languages: languages, globals: globals });
});

/* GET code generation. */
router.get("/gencode", function(req, res) {
    var language = req.query.language;
    if (language.toLowerCase() != "java" && language.toLowerCase() != "c++" && language.toLowerCase() != "python") {
        console.log("Invalid language detected.");
        res.send({"error": "Invalid language"});
        return;
    }
    console.log("\nThe client input is: " + req.query.input);
    console.log("The language is: " + req.query.language);

    function onCollectSourceSuccess(output, command) {
        console.log("collect_source executed successfully!");
        res.send(output);
    }

    function onCodegenSuccess(output, command) {
        console.log("instaparse executed successfully!");
        util.syscall("python collect_source.py tmp input.format", onCollectSourceSuccess);
    }

    fs.writeFile("tmp/input.format", req.query.input, function(err) {
        if (err)
            console.log("Error writing input file: " + err);
        else {
            console.log("Successfully wrote tmp/input.format.");
            util.syscall("python instaparse.py -l " + language + " tmp/input.format -o tmp/out", onCodegenSuccess);
        }
    });
});

module.exports = router;
