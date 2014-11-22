var express = require("express");
var router = express.Router();

var path = require("path");
var fs = require("fs");

var order = JSON.parse(fs.readFileSync(path.join(__dirname, "../", "content", 'order.json')));
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

// sections.forEach(function(section){
//     console.log(section.id);
//     console.log(section.content);
// });

/* GET home page. */
router.get("/", function(req, res) {
  res.render("index", { title: "InstaParse", sections: sections });
});

module.exports = router;
