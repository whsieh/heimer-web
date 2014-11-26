$(document).ready(function() {
    var encodeUserInput = function(input) {
        return encodeURI(input).replace(/&/g, encodeURIComponent("&")).replace(/\+/g, encodeURIComponent("+"));
    }

    var urlStringPrefix = "http://localhost:8000/gencode?language=";
    var gencode = function(language, input, handleFinished) {
        console.log("Calling gencode...");
        if (handleFinished == undefined) {
            handleFinished = function(result) {
                console.log("Success! Printing generated code...");
                for (var sourceName in result) {
                    console.log("\n\n" + sourceName + "\n==========");
                    console.log(decodeURI(result[sourceName]));
                }
            }
        }
        $.ajax({
            url: urlStringPrefix + encodeUserInput(language) + "&input=" + encodeUserInput(input),
            type: "GET",
            dataType: "json",
            success: handleFinished,
            error: function(result) {
                console.log("Error generating code (status " + result.status + ")");
            }
        });
    }
    window.gencode = gencode;
});

var testFormat = "<head>\n\
delimiter \",\"\n\
\n\
<objects>\n\
Adjacency\n\
    vertex:int neighbors:list(int)\n\
Graph\n\
    name:string\n\
    adjacencies:Adjacency:+\n\
    \n\
<body>\n\
graphs:Graph:+!";
