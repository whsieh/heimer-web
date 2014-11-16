var express = require("express");
var router = express.Router();

var path = require("path");
var fs = require("fs");

var order = JSON.parse(fs.readFileSync(path.join(__dirname, "../", "content", 'order.json')));
var sections = [];

order.files.forEach(function(file) {
    var name = file.name;
    var filename = file.filename;
    var id = file.id;
    var content = fs.readFileSync(path.join(__dirname, "../", "content", filename), "utf8");

    sections.push({ id: id, name: name, content: content });
});

// sections.forEach(function(section){
//     console.log(section.id);
//     console.log(section.content);
// });

/* GET home page. */
router.get("/", function(req, res) {
  res.render("index", { title: "InstaParser", sections: sections });
});

module.exports = router;
