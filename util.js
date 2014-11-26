/* Required to run instaparse on the server. */
var childProcess = require("child_process");

function syscall( commandString, handleSuccess, handleError ) {
    if (handleSuccess == undefined) {
        handleSuccess = function( output, command ) {
            console.log(output);
        }
    }
    if (handleError == undefined) {
        handleError = function( errorString, command ) {
            console.log("Error when running " + command + ": " + errorString);
        }
    }
    childProcess.exec(commandString, function(error, stdout, stderr) {
        if (error) {
            console.log(error);
            return;
        }
        var errorString = stderr.toString();
        if (errorString)
            handleError(errorString);
        else
            handleSuccess(stdout.toString());
    });
}

module.exports = {
    "syscall": syscall
}