var express = require("express");
var router = express.Router();

var path = require("path");
var fs = require("fs");
var temp = require("temp");
var childProcess = require("child_process");
var rimraf = require("rimraf");

//============================================================
// Automatically generate webpage content
//============================================================

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

//============================================================
// Route Handlers
//============================================================

/* GET home page. */
router.get(["/", "/editor"], function(req, res) {
  res.render("index", { title: "InstaParse", sections: sections, languages: languages, globals: globals });
});

/* GET code generation. */

// Helpers for generation
var onCodegenError = function(res, error) {
    res.send({error: error});
};

var onCodegenSuccess = function(res, outputDirectoryName) {
    var command = "python collect_source.py " + outputDirectoryName + " input.format Main";

    childProcess.exec(command, function(error, stdout, stderr) {
        if (error) {
            onCodegenError(res, stderr.toString());
        } else {
            res.send(stdout.toString());
        }

        rimraf(outputDirectoryName, function (error) {
            if (error) {
                console.log("Unable to clean temporary directory: " + dirPath);
            }
        });
    });
};

router.get("/gencode", function(req, res) {
    var language = req.query.language;
    var directoryName = "tmp";

    temp.mkdir(directoryName, function(err, dirPath) {
        var formatFile = path.join(dirPath, "input.format");
        fs.writeFile(formatFile, req.query.input, function(err) {
            if (err) {
                onCodegenError("IO Error. Try again!");
            } else {
                var command = "python instaparse.py -l " + language + " " 
                    + formatFile  + " "
                    + "-o " + path.join(dirPath, "Main");
                childProcess.exec(command, function(error, stdout, stderr) {
                    if (error) {
                        onCodegenError(res, stderr.toString());
                    } else {
                        onCodegenSuccess(res, dirPath);
                    }
                });
            }
        });
    });
});

module.exports = router;
