$(function() {
    var encodeUserInput = function(input) {
        return encodeURI(input).replace(/&/g, encodeURIComponent("&")).replace(/\+/g, encodeURIComponent("+"));
    }

    var urlStringPrefix = "http://localhost:8000/gencode?language=";
    var gencode = function(language, input, handleFinished) {
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
    window.exports.gencode = gencode;
});