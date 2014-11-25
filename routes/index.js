var express = require("express");
var router = express.Router();

var path = require("path");
var fs = require("fs");


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

module.exports = router;
