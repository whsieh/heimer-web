var express = require('express');
var path = require('path');
var favicon = require('serve-favicon');
var logger = require('morgan');
var cookieParser = require('cookie-parser');
var bodyParser = require('body-parser');
var expressLess = require('express-less');
var routes = require('./routes/index');

/* Required to run instaparse on the server. */
var childProcess = require("child_process")

var app = express();

// view engine setup
app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'jade');

// uncomment after placing your favicon in /public
//app.use(favicon(__dirname + '/public/favicon.ico'));
app.use(logger('dev'));
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: false }));
app.use(cookieParser());
app.use(expressLess(path.join(__dirname, 'public', 'styles')));
app.use(express.static(path.join(__dirname, 'public')));

app.use('/', routes);


// catch 404 and forward to error handler
app.use(function(req, res, next) {
    var err = new Error('Not Found');
    err.status = 404;
    next(err);
});

// error handlers

// development error handler
// will print stacktrace
if (app.get('env') === 'development') {
    app.use(function(err, req, res, next) {
        res.status(err.status || 500);
        res.render('error', {
            message: err.message,
            error: err
        });
    });
}

// production error handler
// no stacktraces leaked to user
app.use(function(err, req, res, next) {
    res.status(err.status || 500);
    res.render('error', {
        message: err.message,
        error: {}
    });
});

function syscall( commandString, handleSuccess, handleError) {
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
            console.log("Error: failed to execute system call \"" + commandString + "\"(" + error + ")");
            return;
        }
        errorString = stderr.toString();
        if (errorString)
            handleError(errorString);
        else
            handleSuccess(stdout.toString());
    });
}

module.exports = app;
