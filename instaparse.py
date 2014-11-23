#!/usr/bin/env python

import re
from sys import exit
from collections import OrderedDict
from os.path import dirname, basename, join, splitext
from optparse import OptionParser

class InstaParseFile:
    """ Simple custom file class used by code generation components. """

    indentString = "    "
    commentString = "#"

    def __init__( self, name ):
        self.filename = name
        self.fileContents = ""
        self.indentLevel = 0
        self.shouldIndent = True

    def indent(self):
        self.indentLevel += 1

    def dedent(self):
        self.indentLevel -= 1

    def comment( self, line ):
        """ Writes a comment line using the commentString variable that can be adjusted. """
        self.writeLine(self.commentString + " " + line)

    def write( self, line ):
        """ Writes a line to the file, only indenting if it is supposed to.

        It will indent only if the most recent `write` call is a `writeLine` or `writeNewline` (
        ignoring other methods in this class). """
        if self.shouldIndent:
            self.fileContents += InstaParseFile.indentString * self.indentLevel + line
        else:
            self.fileContents += line
        self.shouldIndent = False

    def writeLine( self, line ):
        self.write(line + "\n")
        self.shouldIndent = True

    def writeImportLine( self, line ):
        """ Helps write an import or include line at the top of the file disregarding the indent level. """
        self.fileContents = line + "\n" + self.fileContents

    def writeNewline(self):
        """ Helper to write a simple newline, useful for adding an empty line. """
        self.fileContents += "\n"
        self.shouldIndent = True

    def save(self):
        """ Saves the InstaParseFile. Ideally, use only once per InstaParseFile at the end of code generation. """
        outputFile = open( self.filename, "w")
        outputFile.write(self.fileContents)
        outputFile.close()

    def setExtension( self, extensionString ):
        """ Sets the extension of this file to the given extension, if applicable. """
        extensionIndex = self.filename.rfind("." + extensionString)
        if extensionIndex == -1 or extensionIndex != len(self.filename) - len(extensionString) - 1:
            self.filename += "." + extensionString

class StringConstants:

    HEAD_TAG = "<head>"
    OPTIONS_TAG = "<options>"
    OBJECTS_TAG = "<objects>"
    BODY_TAG = "<body>"
    INLINE_COMMENT = "#"
    DEFAULT_SINGLE_LINE_DELIMITER = " "
    INTEGER_TYPE = "int"
    FLOAT_TYPE = "float"
    STRING_TYPE = "string"
    BOOL_TYPE = "bool"
    LIST_TYPE = "list"
    LINE_ONE_OR_MORE = "+"
    LINE_ZERO_OR_MORE = "*"
    SEPARATE_BY_ADDITIONAL_NEWLINE_MODE = "!"

def isPrimitive(typeName):
    return typeName == StringConstants.INTEGER_TYPE or typeName == StringConstants.FLOAT_TYPE or \
        typeName == StringConstants.BOOL_TYPE or typeName == StringConstants.STRING_TYPE or \
        isList(typeName)

def isInteger(typeName):
    return typeName == StringConstants.INTEGER_TYPE

def isFloat(typeName):
    return typeName == StringConstants.FLOAT_TYPE

def isString(typeName):
    return typeName == StringConstants.STRING_TYPE

def isBool(typeName):
    return typeName == StringConstants.BOOL_TYPE

def isList(typeName):
    """ List is of the form 'list(listType)' where listType is a non-list primitive. """
    if len(typeName) <= 4:
        return False
    if typeName.find(StringConstants.LIST_TYPE) == 0 and \
        typeName[len(StringConstants.LIST_TYPE)] == "(" and \
        typeName[-1] == ")":
        listType = typeName[ len(StringConstants.LIST_TYPE) + 1 : len(typeName) - 1 ].strip()
        if isPrimitive(listType) and not isList(listType):
            return True
        else:
            return False
    return False

def listType(typeName):
    if isList(typeName):
        return typeName[ len(StringConstants.LIST_TYPE) + 1 : len(typeName) - 1 ].strip()
    else:
        return None


class RegexPatterns:
    """ Patterns used for parsing. Names are considered simple words with underscores. """
    DELIMITER = re.compile(r"^delimiter\s+\"(.+)\"\s*(#.*)?$")
    CLASS_NAME = re.compile(r"^[\w_]+$")
    FIELD = re.compile(r"^([\w_]+):(" + StringConstants.LIST_TYPE + r"\s*\(\s*([\w_]+)\s*\)|[\w_]+)(:([\w_]+|\+|\*)(\!)?)?\s*")

class ParserUtil:
    @staticmethod
    def lineStartsValidTag(line):
        return line == StringConstants.HEAD_TAG or \
            line == StringConstants.OPTIONS_TAG or \
            line == StringConstants.OBJECTS_TAG or \
            line == StringConstants.BODY_TAG

    @staticmethod
    def stripCommentsAndWhitespaceFromLine(line):
        firstInlineCommentIndex = line.find(StringConstants.INLINE_COMMENT)
        if firstInlineCommentIndex == -1:
            return line.strip()
        return line[:firstInlineCommentIndex].strip()

    @staticmethod
    def classDeclarationsAsString(classes):
        if len(classes) == 0:
            return ""
        result = ""
        for userClass in classes:
            result += "\n" + str(userClass)
        return result[1:]

    @staticmethod
    def fieldDeclarationsFromLine(line):
        fields = []
        fieldMatchResult = RegexPatterns.FIELD.match(line)
        while fieldMatchResult and len(fieldMatchResult.groups()) in [ 5, 6 ]:
            regexGroups = fieldMatchResult.groups()
            field = FieldDeclaration( regexGroups[0], regexGroups[1] )
            field.instanceRepetitionModeString = regexGroups[-2] if regexGroups[-2] else ""
            field.shouldSeparateInstancesByAdditionalNewline = regexGroups[-1] == StringConstants.SEPARATE_BY_ADDITIONAL_NEWLINE_MODE
            fields.append(field)
            line = line[fieldMatchResult.end():]
            fieldMatchResult = RegexPatterns.FIELD.match(line)
        if line.strip():
            # Unidentified tokens at end of line; invalidate field decls altogether.
            return []
        return fields

class FieldDeclaration:

    def __init__( self, name, typeName ):
        self.name = name
        self.typeName = typeName
        self.instanceRepetitionModeString = ""
        self.shouldSeparateInstancesByAdditionalNewline = False

    def __str__(self):
        return str(( self.name, self.typeName, self.instanceRepetitionModeString,
            self.shouldSeparateInstancesByAdditionalNewline ))

class ClassDeclaration:

    def __init__( self, name ):
        self.name = name
        self.lines = []

    def addFieldsAsLine( self, fields ):
        self.lines.append(fields)

    def __str__(self):
        result = "class " + self.name + "\n"
        for line in self.lines:
            result += "  -"
            for field in line:
                result += "  " + str(field)
            result += "\n"
        return result[:-1]

class FormatFileObjectModel:

    def __init__(self):
        self.lineDelimiter = StringConstants.DEFAULT_SINGLE_LINE_DELIMITER
        self.commandLineOptions = []
        self.classes = []
        self.body = FieldDeclaration("body", "Body")

    def addClass( self, inputClass ):
        self.classes.append(inputClass)

    def __str__(self):
        result = ""
        if len(self.classes) > 0:
            result += ParserUtil.classDeclarationsAsString(self.classes) + "\n"
        return result[:-1]

class InstaParseFormatFileParser:

    def __init__( self, formatFileName ):
        self.tagLineMarkerIntervals = {}
        self.failureMessages = []
        self.objectModel = FormatFileObjectModel()
        try:
            InstaparseFile = open( formatFileName, "r" )
            self.formatInputAsLines = [line.strip() for line in InstaparseFile.readlines()]
            InstaparseFile.close()
        except IOError:
            return self.pushFailureMessage("Could not find file " + formatFileName + ".")
            self.formatInputAsLines = []
        self.computeTagIntervals()
        if len(self.failureMessages) > 0:
            return
        if StringConstants.BODY_TAG not in self.tagLineMarkerIntervals:
            return self.pushFailureMessage("Could not find the required <body> tag.")
        self.parseAllTags()

    def parseAllTags(self):
        self.parseHeadTag()
        self.parseObjectsTag()
        self.parseBodyTag()

    def parseHeadTag(self):
        if StringConstants.HEAD_TAG not in self.tagLineMarkerIntervals:
            return
        headTagBeginMarker, headTagEndMarker = self.tagLineMarkerIntervals[StringConstants.HEAD_TAG]
        for lineMarker in xrange( headTagBeginMarker + 1, headTagEndMarker ):
            currentStrippedLine = self.formatInputAsLines[lineMarker]
            if not currentStrippedLine:
                continue
            delimiterMatchResults = RegexPatterns.DELIMITER.match(currentStrippedLine)
            if delimiterMatchResults is None:
                return self.pushFailureMessage( "Expected delimiter declaration.", lineMarker )
            self.objectModel.lineDelimiter = delimiterMatchResults.group(1)

    def parseObjectsTag(self):
        if StringConstants.OBJECTS_TAG not in self.tagLineMarkerIntervals:
            return
        lineMarker, singleTagEndMarker = self.tagLineMarkerIntervals[StringConstants.OBJECTS_TAG]
        while lineMarker < singleTagEndMarker - 1:
            lineMarker += 1
            currentStrippedLine = ParserUtil.stripCommentsAndWhitespaceFromLine(self.formatInputAsLines[lineMarker])
            if not currentStrippedLine:
                continue
            if not RegexPatterns.CLASS_NAME.match(currentStrippedLine):
                return self.pushFailureMessage( "Found an invalid object declaration.", lineMarker )
            classDecl = ClassDeclaration(currentStrippedLine)
            classDeclLineMarker = lineMarker
            while lineMarker < singleTagEndMarker - 1:
                lineMarker += 1
                currentStrippedLine = ParserUtil.stripCommentsAndWhitespaceFromLine(self.formatInputAsLines[lineMarker])
                if not currentStrippedLine:
                    classDecl.addFieldsAsLine([])
                    continue
                if RegexPatterns.CLASS_NAME.match(currentStrippedLine):
                    lineMarker -= 1
                    break
                fields = ParserUtil.fieldDeclarationsFromLine(currentStrippedLine)
                if len(fields) == 0:
                    return self.pushFailureMessage( "Found invalid field declarations for the object \"%s\"" % (classDecl.name,), classDeclLineMarker, lineMarker )
                classDecl.addFieldsAsLine(fields)
            self.objectModel.addClass(classDecl)

    def parseBodyTag(self):
        if StringConstants.BODY_TAG not in self.tagLineMarkerIntervals:
            return
        bodyTagBeginMarker, bodyTagEndMarker = self.tagLineMarkerIntervals[StringConstants.BODY_TAG]
        hasBegunParsingFields = False
        body = ClassDeclaration("Body")
        for lineMarker in xrange( bodyTagBeginMarker + 1, bodyTagEndMarker ):
            currentStrippedLine = ParserUtil.stripCommentsAndWhitespaceFromLine(self.formatInputAsLines[lineMarker])
            if not currentStrippedLine:
                if hasBegunParsingFields:
                    body.addFieldsAsLine(list())
                continue
            fields = ParserUtil.fieldDeclarationsFromLine(currentStrippedLine)
            if len(fields) == 0:
                return self.pushFailureMessage( "Found invalid field declarations for the body.", lineMarker )
            body.addFieldsAsLine(fields)
            hasBegunParsingFields = True
        self.objectModel.addClass(body)

    def printFailures(self):
        for failureMessage in self.failureMessages:
            print failureMessage, "\n"

    def pushFailureMessage( self, message, *lineMarkers ):
        failureMessage = "Error: " + message
        for lineMarker in lineMarkers:
            failureMessage += "\n    at line " + str(lineMarker + 1) +  ":\t\"" + self.formatInputAsLines[lineMarker] + "\""
        self.failureMessages.append(failureMessage)

    def failureString(self):
        msg = ""
        for failureMessage in self.failureMessages:
            msg += failureMessage + "\n"
        return msg

    def parseFailed(self):
        return len(self.failureMessages) > 0

    def nextTagLocationFromLineMarker( self, marker ):
        while marker < len(self.formatInputAsLines):
            currentStrippedLine = ParserUtil.stripCommentsAndWhitespaceFromLine(self.formatInputAsLines[marker])
            if ParserUtil.lineStartsValidTag(currentStrippedLine):
                return marker
            marker += 1
        return len(self.formatInputAsLines)

    def firstLineMarkerWithText(self):
        marker = 0
        for line in self.formatInputAsLines:
            if ParserUtil.stripCommentsAndWhitespaceFromLine(line):
                return marker
            marker += 1
        return -1

    def computeTagIntervals(self):
        lineMarkerBegin = self.firstLineMarkerWithText()
        if lineMarkerBegin >= len(self.formatInputAsLines):
            return self.pushFailureMessage( "Input file empty or commented out." )
        if not ParserUtil.lineStartsValidTag(self.formatInputAsLines[lineMarkerBegin]):
            return self.pushFailureMessage( "Found an invalid tag declaration.", lineMarkerBegin )
        lastTagName = None
        while lineMarkerBegin < len(self.formatInputAsLines):
            tagName = self.formatInputAsLines[lineMarkerBegin]
            if tagName in self.tagLineMarkerIntervals:
                return self.pushFailureMessage( "Duplicate tag name.", self.tagLineMarkerIntervals[tagName][0], lineMarkerBegin )
            lineMarkerEnd = self.nextTagLocationFromLineMarker(lineMarkerBegin + 1)
            lastTagName = self.formatInputAsLines[lineMarkerBegin]
            self.tagLineMarkerIntervals[lastTagName] = ( lineMarkerBegin, lineMarkerEnd )
            lineMarkerBegin = lineMarkerEnd
        if lastTagName:
            for lineMarker in xrange( len(self.formatInputAsLines) - 1, 0, -1 ):
                if ParserUtil.stripCommentsAndWhitespaceFromLine(self.formatInputAsLines[lineMarker]):
                    lineMarkerBegin, _ = self.tagLineMarkerIntervals[lastTagName]
                    self.tagLineMarkerIntervals[lastTagName] = lineMarkerBegin, lineMarker + 1
                    break


class InstaParseFormat:
    def __init__( self, objectModel ):
        self._model = objectModel
        self._userClasses = OrderedDict()
        # The class names are stored twice because we want to perserve the ordering of the classes
        self._userClassNames = list()
        # Make sure the user defined classes are of the correct format, else raise error.
        for c in self._model.classes:
            _assertValidName( c.name, self._userClasses )
            _assertValidClass( c, self._userClasses )
            self._userClasses[c.name] = c
            self._userClassNames.append(c.name)
        self._classes = OrderedDict()
        for className in self._userClasses:
            self._classes[className] = _generateFormatLines( className, self._userClasses )
        self._bodyTypeName = self._model.body.typeName

    def lineDelimiter(self):
        return self._model.lineDelimiter

    def classes(self):
        """ Return a ordered dictionary with class names as keys and the corresponding list of
        FormatLine's (containing the fields on that line) as values. """
        return self._classes

    def bodyTypeName(self):
        return self._bodyTypeName

class FormatField:
    def __init__( self, field, userClasses, parent=None ):
        self._field = field
        self._userClasses = userClasses
        self._parent = parent
        # Verify this field has a valid type
        _assertValidType( field.typeName, userClasses )


    def name(self):
        return self._field.name

    def typeName(self):
        return self._field.typeName

    def parent(self):
        """ The parent of this object """
        return self._parent

    def isRepeating(self):
        return self._instanceRepetitionModeString() != ""

    def _instanceRepetitionModeString(self):
        mode = self._field.instanceRepetitionModeString
        try:
            return int(mode)
        except ValueError as e:
            return mode

    def _shouldSeparateInstancesByAdditionalNewline(self):
        return self._field.shouldSeparateInstancesByAdditionalNewline


    def isPrimitive(self):
        return isPrimitive(self._field.typeName)

    def isInteger(self):
        return isInteger(self._field.typeName)

    def isFloat(self):
        return isFloat(self._field.typeName)

    def isString(self):
        return isString(self._field.typeName)

    def isBool(self):
        return isBool(self._field.typeName)

    def isList(self):
        return isList(self._field.typeName)

    def listType(self):
        if self.isList():
            return listType(self._field.typeName)
        else:
            return None

    def __str__(self):
        s = ""
        s += "%s:%s" % ( self.name(), self.typeName() )
        if self._instanceRepetitionModeString():
            s += ":%s" % self._instanceRepetitionModeString()
            if self._shouldSeparateInstancesByAdditionalNewline():
                s += "!"
        return s

class FormatLine:
    """ Representing a line in a class declaration or body of the format file.
    May contains zero or more fields. """
    def __init__( self, fields, container=None ):
        self._fields = fields
        # container is the FormatField object representing the class field that contains this line
        self._container = container
        self._currentIndex = 0
        # Repetition string only makes sense when a line has exactly one field
        self._repetitionString = fields[0]._instanceRepetitionModeString() if len(fields) == 1 else ""
        self._isSplitByNewline = fields[0]._shouldSeparateInstancesByAdditionalNewline() if \
            len(fields) == 1 else ""

    def container(self):
        return self._container

    def isEmpty(self):
        return len(self._fields) == 0

    def numFields(self):
        return len(self._fields)

    def getField( self, index ):
        return self._fields[index]

    def repetitionAmountString(self):
        return str(self._repetitionString)

    def isRepeating(self):
        return self._repetitionString != ""

    def isZeroOrMoreRepetition(self):
        return self._repetitionString == StringConstants.LINE_ZERO_OR_MORE

    def isOneOrMoreRepetition(self):
        return self._repetitionString == StringConstants.LINE_ONE_OR_MORE

    def isIntegerRepetition(self):
        try:
            int(self._repetitionString)
            return True
        except ValueError as e:
            # Failed to cast to int, it's not int
            return False

    def isVariableRepetition(self):
        return ( not self.isZeroOrMoreRepetition() and
            not self.isOneOrMoreRepetition() and
            not self.isIntegerRepetition() )

    def isSplitByNewline(self):
        return self._isSplitByNewline

    def __iter__(self):
        return self

    def next(self):
        if self._currentIndex < len(self._fields):
            self._currentIndex += 1
            return self._fields[self._currentIndex - 1]
        else:
            # Reset the counter so we can use this in more than one for loop
            self._currentIndex = 0
            raise StopIteration

    def __str__(self):
        s = ""
        for f in self:
            s += str(f) + " "
        return s

def _generateFormatLines( className, userClasses ):
    """ Return a list of FormatLine, where each FormatLine contains the fields of the given class. """
    lines = []
    variables = dict()
    for line in userClasses[className].lines:
        fields = []
        for var in line:
            _assertValidName( var.name, variables.keys() + userClasses.keys() )
            obj = FormatField( var, userClasses )
            variables[var.name] = obj
            fields.append(obj)
            # Make sure if the variable has a instance repetition mode, it is either an
            # integer, a special symbol, or an integer variable already defined in this
            # particular user class.
            mode = obj._instanceRepetitionModeString()
            if ( mode and type(mode) != int and \
                mode != StringConstants.LINE_ONE_OR_MORE and \
                mode != StringConstants.LINE_ZERO_OR_MORE and \
                ( mode not in variables or \
                not variables[mode].isInteger() ) ):
                raise ValueError("Unknown repetition mode '%s': it must be either an integer, " + \
                    "the symbol '+' or '*', or an int variable already defined in class." % mode)
        lines.append(FormatLine( fields ))
    return lines


def _assertValidName( name, usedNames ):
    """ Verify a name isn't already used by another user defined class or field. """
    if name in usedNames:
        raise ValueError("Name conflict: User defined class/field must have unique name, the name " + \
            "'%s' is used more than once." % name)
    if isPrimitive(name):
        raise ValueError("Name conflict: " + name + " is a primitive type and cannot be used as " + \
            "the name of user defined classes/fields.")

def _assertValidType( typeName, userClasses ):
    # Valid type if it's a user defined class
    if typeName in userClasses:
        return
    # Valid type if it's a primitive
    elif isPrimitive(typeName):
        return
    # Invalid type if it's a list but the list type is not a non-list primitive
    elif ( typeName.find(StringConstants.LIST_TYPE) == 0 and \
            typeName[len(StringConstants.LIST_TYPE)] == "(" and \
            typeName[-1] == ")" ):
        # get the list type and remove whitespaces in the front and back
        listType = typeName[ len(StringConstants.LIST_TYPE) + 1 : len(typeName) - 1 ].strip()
        if not isPrimitive(listType) or isList(listType):
            raise ValueError("The type of a list can only be a non-list primitive type.")
        return
    # Else invalid type.
    raise ValueError("Unknown field type " + typeName + ", it should either be a primitive type " + \
        "or a user defined class.")

def _assertValidClass( c, userClasses ):
    # Verify that every field in the class follows the spec
    for line in c.lines:
        for index, field in enumerate(line):
            if isPrimitive(field.typeName):
                # a list can only be the last field on a line
                if isList(field.typeName) and ( index + 1 ) < len(line):
                    raise ValueError("Format error in user defined class '%s': list can only be the last field on a line." % c.name)
            else:
                if field.typeName not in userClasses:
                    raise ValueError("""Format error in user defined class '%s': unknown field type '%s', all types must be either primitive type or a already defined user class."""
                        % ( c.name, field.typeName ))
                # There is more than one field on this line
                if len(line) > 1:
                    raise ValueError("Format error in user defined class '%s': unexpected field type '%s', there can be exactly one field with user defined class as type in each line." % ( c.name, field.tpyName))

def getFormat(fileName):
    from parser import InstaParseFormatFileParser
    p = InstaParseFormatFileParser(fileName)
    return InstaParseFormat(p.objectModel)


class CodeGenerator:
    """ Base class for generating the parser code. Subclass this for every language supported by InstaParse. """

    # Namespace
    PARSER_NAME = "InstaParse"

    # Filenames
    UTIL_FILE_NAME = PARSER_NAME + "Util"
    DATA_FILE_NAME = PARSER_NAME + "Data"

    # Used variable names
    USER_ARGS = "userArgs"
    PARSED_OBJ = "parsedObject"

    # Method/Function names
    PARSE_INT = "parseInt"
    PARSE_BOOL = "parseBool"
    PARSE_STRING = "parseString"
    PARSE_FLOAT = "parseFloat"
    PARSE_INT_LIST = "parseIntList"
    PARSE_BOOL_LIST = "parseBoolList"
    PARSE_STRING_LIST = "parseStringList"
    PARSE_FLOAT_LIST = "parseFloatList"
    PARSE_NEWLINE = "parseNewline"
    PARSE_INPUT = "parse"

    def __init__( self, filename, format ):
        self.foldername = dirname(filename)
        self.filename = basename(filename)
        self.main = InstaParseFile(filename)
        self.util = InstaParseFile(join(self.foldername, CodeGenerator.UTIL_FILE_NAME))
        self.data = InstaParseFile(join(self.foldername, CodeGenerator.DATA_FILE_NAME))
        self.format = format
        self.classes = format.classes()
        self.bodyTypeName = format.bodyTypeName()
        self.currentFile = None
        self.typeNameToParseFuncName = {
            StringConstants.INTEGER_TYPE: CodeGenerator.PARSE_INT,
            StringConstants.FLOAT_TYPE: CodeGenerator.PARSE_FLOAT,
            StringConstants.STRING_TYPE: CodeGenerator.PARSE_STRING,
            StringConstants.BOOL_TYPE: CodeGenerator.PARSE_BOOL,
            "list(%s)" % StringConstants.INTEGER_TYPE: CodeGenerator.PARSE_INT_LIST,
            "list(%s)" % StringConstants.FLOAT_TYPE: CodeGenerator.PARSE_FLOAT_LIST,
            "list(%s)" % StringConstants.STRING_TYPE: CodeGenerator.PARSE_STRING_LIST,
            "list(%s)" % StringConstants.BOOL_TYPE: CodeGenerator.PARSE_BOOL_LIST,
        }
        self.initialize()

    def initialize(self):
        """ Perform additional initialization if required. """
        pass

    def codeGen(self):
        """ This method is called to generate and write the parser to the specified file. """
        self.generateDataFile()
        self.generateUtilFile()
        self.generateMainFile()
        self.main.save()
        self.util.save()
        self.data.save()

    ################################################################################
    # Generate Data File
    ################################################################################

    def generateDataFile(self):
        """ Generate classes in a separate data file. """
        self.currentFile = self.data
        self.generateDataFileHeader()
        self.generateClasses()

    def generateDataFileHeader(self):
        """ For generating the data file header, such as the import statements. """
        raise NotImplementedError()

    def generateClasses(self):
        """ For generating code segment that defines all the data structures needed by the parser. """
        for className, lines in self.classes.items():
            fields = []
            for line in lines:
                for field in line:
                    fields.append(field)
            self.generateClass( className, fields )
            #The name for the parseing function for class X is parseX
            self.typeNameToParseFuncName[className] = "parse%s" % className

    def generateClass( self, className, fields ):
        """ Helper function for generating the code segement defining a class (or the corresponding
        data structure). The first argument is the class name and the second argument is a list of
        fields (in order) of that class. """
        print "classGen"
        raise NotImplementedError()

    ################################################################################
    # Generate Util File
    ################################################################################

    def generateUtilFile(self):
        """ Generate helper functions in the separate util file. """
        self.currentFile = self.util
        self.generateUtilFileHeader()
        self.generateHelperFunctions()
        self.generateClassParserFunctions()

    def generateUtilFileHeader(self):
        """ For generating the util file header, such as the import statements. """
        raise NotImplementedError()

    def generateHelperFunctions(self):
        """ For generating the helper functions that will be useful when parsing in the util file. """
        raise NotImplementedError()

    def generateClassParserFunctions(self):
        """ For generating all the functions for parsing user defined classes. """
        for className, lines in self.classes.items():
            self.generateClassParserFunction( className, lines )

    def generateClassParserFunction( self, className, lines ):
        """ For generating a helper functions for parsing a user defined class. The first argument
        is the class name and the second argument is a list of FormatLine's. """
        raise NotImplementedError

    ################################################################################
    # Generate Main File
    ################################################################################

    def generateMainFile(self):
        """ Generate main file where the main function resides. """
        self.currentFile = self.main
        self.generateMainFileHeader()
        self.generateInputParserFunction()
        self.generateMainFunction()

    def generateMainFileHeader(self):
        """ For generating the main file header, such as the import statements. """
        raise NotImplementedError()

    def generateInputParserFunction(self):
        """ For generating the function to parse an input file. """
        raise NotImplementedError()

    def generateMainFunction(self):
        """ For generating the empty main method that the user can fill in. """
        raise NotImplementedError()


def javagenStaticHelpers():
    helpers = """
public static int javagenParseInt(String s, int[] lineNumber)
{
\ttry
\t{
\t\treturn Integer.parseInt(s);
\t}
\tcatch (NumberFormatException e)
\t{
\t\tthrow new NumberFormatException(
\t\t\t"Parser Error on line " + lineNumber[0] + ": Could not parse \\"" + s + "\\" as int.");
\t}
}

public static boolean javagenParseBool(String s, int[] lineNumber)
{
\tif (s.equals("1") || s.toLowerCase().equals("true"))
\t{
\t\treturn true;
\t}
\telse if (s.equals("0") || s.toLowerCase().equals("false"))
\t{
\t\treturn false;
\t}
\tthrow new NumberFormatException(
\t\t"Parser Error on line " + lineNumber[0] + ": Could not parse \\"" + s + "\\" as bool.");
}

public static String javagenParseString(String s, int[] lineNumber)
{
\treturn s;
}

public static float javagenParseFloat(String s, int[] lineNumber)
{
\ttry
\t{
\t\treturn Float.parseFloat(s);
\t}
\tcatch (NumberFormatException e)
\t{
\t\tthrow new NumberFormatException(
\t\t\t"Parser Error on line " + lineNumber[0] + ": Could not parse \\"" + s + "\\" as float.");
\t}
}

public static ArrayList<Integer> javagenParseIntList(String[] strings, int[] lineNumber)
{
\tif (strings.length == 0)
\t\tthrow new NumberFormatException(
\t\t\t"Parser Error on line " + lineNumber[0] + ": Could not parse empty string as list.");
\tArrayList<Integer> resval = new ArrayList<Integer>();
\tfor (String s : strings)
\t\tresval.add(javagenParseInt(s, lineNumber));
\treturn resval;
}

public static ArrayList<Boolean> javagenParseBoolList(String[] strings, int[] lineNumber)
{
\tif (strings.length == 0)
\t\tthrow new NumberFormatException(
\t\t\t"Parser Error on line " + lineNumber[0] + ": Could not parse empty string as list.");
\tArrayList<Boolean> resval = new ArrayList<Boolean>();
\tfor (String s : strings)
\t\tresval.add(javagenParseBool(s, lineNumber));
\treturn resval;
}

public static ArrayList<String> javagenParseStringList(String[] strings, int[] lineNumber)
{
\tif (strings.length == 0)
\t\tthrow new NumberFormatException(
\t\t\t"Parser Error on line " + lineNumber[0] + ": Could not parse empty string as list.");
\tArrayList<String> resval = new ArrayList<String>();
\tfor (String s : strings)
\t\tresval.add(javagenParseString(s, lineNumber));
\treturn resval;
}

public static ArrayList<Float> javagenParseFloatList(String[] strings, int[] lineNumber)
{
\tif (strings.length == 0)
\t\tthrow new NumberFormatException(
\t\t\t"Parser Error on line " + lineNumber[0] + ": Could not parse empty string as list.");
\tArrayList<Float> resval = new ArrayList<Float>();
\tfor (String s : strings)
\t\tresval.add(javagenParseFloat(s, lineNumber));
\treturn resval;
}

public static String readLine(RandomAccessFile f, String className)
{
\ttry
\t{
\t\tString result = f.readLine();
\t\tif (result == null) throw new RuntimeException("Parser Error: Reached end of file while parsing object \\"" + className + "\\".");
\t\treturn result;
\t}
\tcatch (IOException e)
\t{
\t\tthrow new RuntimeException("IO Error: Unknown problem when reading input file.");
\t}
}

public static void seek(RandomAccessFile f, long pos)
{
\ttry
\t{
\t\tf.seek(pos);
\t}
\tcatch (IOException e)
\t{
\t\tthrow new RuntimeException("IO Error: Unknown problem when reading input file.");
\t}
}

public static long getFilePointer(RandomAccessFile f)
{
\ttry
\t{
\t\treturn f.getFilePointer();
\t}
\tcatch (IOException e)
\t{
\t\tthrow new RuntimeException("IO Error: Unknown problem when reading input file.");
\t}
}
"""

    helpers = helpers.replace("javagenParseIntList", CodeGenerator.PARSE_INT_LIST)
    helpers = helpers.replace("javagenParseBoolList", CodeGenerator.PARSE_BOOL_LIST)
    helpers = helpers.replace("javagenParseStringList", CodeGenerator.PARSE_STRING_LIST)
    helpers = helpers.replace("javagenParseFloatList", CodeGenerator.PARSE_FLOAT_LIST)
    helpers = helpers.replace("javagenParseInt", CodeGenerator.PARSE_INT)
    helpers = helpers.replace("javagenParseBool", CodeGenerator.PARSE_BOOL)
    helpers = helpers.replace("javagenParseString", CodeGenerator.PARSE_STRING)
    helpers = helpers.replace("javagenParseFloat", CodeGenerator.PARSE_FLOAT)

    # Replace the tabs with the appropriate amount of indent spaces
    helpers = helpers.replace( "\t", InstaParseFile.indentString )

    return helpers



""" Class for generating Java code. """
class JavaGenerator(CodeGenerator):

    def initialize(self):
        """ Perform additional initialization if required. """
        InstaParseFile.commentString = "//"
        self.main.setExtension("java")
        self.util.setExtension("java")
        self.classFiles = []

    def codeGen(self):
        """ This method is called to generate and write the parser to the specified file. """
        self.generateClasses()
        self.generateUtilFile()
        self.generateMainFile()
        self.main.save()
        self.util.save()
        map(lambda c: c.save(), self.classFiles)

    ################################################################################
    # Generate Data File
    ################################################################################

    def generateClass( self, className, fields ):
        """ Helper function for generating the code segement defining a class (or the corresponding
        data structure). The first argument is the class name and the second argument is a list of
        fields (in order) of that class. """
        self.typeNameToParseFuncName[className] = "parse%s" % className
        classFile = InstaParseFile(join(self.foldername, className + ".java"))
        self.classFiles.append(classFile)
        self.currentFile = classFile

        shouldImportArrayList = False

        self._beginBlock("public class " + className )

        for field in fields:
            if field.isRepeating() or field.isList():
                shouldImportArrayList = True
            classFile.writeLine("public " + self._getTypeName(field) + " " + field.name() + ";")

        if shouldImportArrayList:
            classFile.writeImportLine("")
            classFile.writeImportLine("import java.util.ArrayList;")

        self._endBlock()

    ################################################################################
    # Generate Util File
    ################################################################################

    def generateUtilFile(self):
        self.currentFile = self.util
        self.generateUtilFileHeader()
        self._beginBlock("public class " + CodeGenerator.UTIL_FILE_NAME)
        self.generateHelperFunctions()
        self.generateClassParserFunctions()
        self._endBlock()

    def generateUtilFileHeader(self):
        """ For generating the util file header, such as the import statements. """
        # Import library headers
        self.currentFile.writeLine("import java.util.ArrayList;")
        self.currentFile.writeLine("import java.util.Arrays;")
        self.currentFile.writeLine("import java.io.RandomAccessFile;")
        self.currentFile.writeLine("import java.io.EOFException;")
        self.currentFile.writeLine("import java.io.IOException;")

        self.currentFile.writeNewline()

    def generateHelperFunctions(self):
        """ For generating the helper functions that will be useful when parsing in the util file. """
        # Static helpers for primitives
        helpers = javagenStaticHelpers()
        map(lambda s: self.currentFile.writeLine(s), helpers.splitlines())
        self.currentFile.writeNewline()

    def generateClassParserFunction( self, className, lines ):
        """ For generating a helper functions for parsing a user defined class. The first argument
        is the class name and the second argument is a list of FormatLine's. """
        writeLine = self.currentFile.writeLine
        write = self.currentFile.write

        def isSimplePrimitive(field):
            return field.isInteger() or field.isFloat() or field.isString() or field.isBool()

        def generateSetup():
            # Helper to do some setup in every parser function
            writeLine(className + " result = new " + className + "();")
            didSplit = False
            didRepeat = False
            didRepeatPlus = False

            for line in lines:
                didRepeat = didRepeat or line.isRepeating()
                didRepeatPlus = didRepeatPlus or  line.isOneOrMoreRepetition()
                didSplit = didSplit or line.numFields() > 1 or (not line.isEmpty() and line.getField(0).isList())

            if didSplit:
                writeLine("String[] fields;")
            if didRepeat:
                writeLine("long prevFilePos = getFilePointer(f);")
                writeLine("int prevLineNumber = lineNumber[0];")
            if didRepeatPlus:
                writeLine("boolean didRepeatOnce = false;")

        def handleEmptyLine():
            # Handle the empty line case
            self._beginBlock("if (!readLine(f, \"" + className + "\").trim().equals(\"\"))")
            writeLine("throw new RuntimeException(\"Parser Error on line \" + lineNumber[0] +" +
                "\": Should be an empty line.\");")
            self._endBlock()
            writeLine("lineNumber[0] += 1;")

        def handleSimpleLineOneField(field):
            # Helper for handleSimpleLine
            if isSimplePrimitive(field):
                # Field is simple, just parse it
                writeLine("result." + field.name() + " = "
                    + self.typeNameToParseFuncName[field.typeName()] + "(readLine(f, \"" + className + "\"), lineNumber);")
                writeLine("lineNumber[0] += 1;")
            elif field.isPrimitive():
                # Field is primitive list, split line
                writeLine("fields = readLine(f, \"" + className + "\").split(\"" + self.format.lineDelimiter() + "\");")
                write("result." + field.name() + " = "
                    + self.typeNameToParseFuncName["list(%s)" % field.listType()] + "(fields, lineNumber);")
                writeLine("lineNumber[0] += 1;")
            else:
                # Field is a class, recurse
                writeLine("result." + field.name() + " = "
                    + self.typeNameToParseFuncName[field.typeName()] + "(f, lineNumber);")

        def handleSimpleLineMultipleField(index, field):
            # Helper for handleSimpleLine
            if isSimplePrimitive(field):
                writeLine("result." + field.name() + " = "
                    + self.typeNameToParseFuncName[field.typeName()]
                    + "(fields[" + str(index) + "], lineNumber);")
            elif field.isPrimitive():
                # Field is primitive list, use rest of fields)
                writeLine("result." + field.name() + " = "
                    + self.typeNameToParseFuncName["list(%s)" % field.listType()]
                    + "(Arrays.copyOfRange(fields, " + str(index) + ", fields.length), lineNumber);")
            else:
                # Field is a class? Cannot be!
                raise Exception("This should never happen.")

            writeLine("lineNumber[0] += 1;")

        def handleSimpleLine(line):
            if line.numFields() == 1:
                # Only one field, no need to split unnecessarily
                handleSimpleLineOneField(line.getField(0))
            else:
                # Multiple fields, split it
                writeLine("fields = readLine(f, \"" + className + "\").split(\"" + self.format.lineDelimiter() + "\");")
                if (line.getField(-1).isList()):
                    self._beginBlock("if (fields.length < " + str(line.numFields()) + ")")
                else:
                    self._beginBlock("if (fields.length != " + str(line.numFields()) + ")")
                writeLine("throw new RuntimeException(\"Parser Error on line \" + lineNumber[0] + " +
                    "\": Expecting " + str(line.numFields()) + " fields (\" + fields.length + \" found).\");")
                self._endBlock()
                for index, field in enumerate(line):
                    handleSimpleLineMultipleField(index, field)

        def handleRepeatingLineForField(field):
            # Helper for handleRepeating
            if isSimplePrimitive(field):
                # Field is simple, just parse it
                writeLine("result." + field.name() + ".add("
                    + self.typeNameToParseFuncName[field.typeName()] + "(readLine(f, \"" + className + "\"), lineNumber));")
                writeLine("lineNumber[0] += 1;")
            elif field.isPrimitive():
                # Field is primitive list, split line
                writeLine("fields = readLine(f, \"" + className + "\").split(\"" + self.format.lineDelimiter() + "\");")
                writeLine("result." + field.name() + ".add("
                    + self.typeNameToParseFuncName["list(%s)" % field.listType()] + "(fields, lineNumber));")
                writeLine("lineNumber[0] += 1;")
            else:
                # Field is a class, recurse
                writeLine("result." + field.name() + ".add("
                    + self.typeNameToParseFuncName[field.typeName()] + "(f, lineNumber));")

        def handleRepeatingLine(line):
            # Must be a primitive or class repeated
            if line.isIntegerRepetition() or line.isVariableRepetition():
                # Constant repetition amount
                field = line.getField(0)
                # Generate the repetition string
                repetitionString = ""
                if line.isIntegerRepetition():
                    repetitionString = str(line.repetitionAmountString())
                else:
                    repetitionString =  "result." + line.repetitionAmountString()
                # Initialize the arraylist
                writeLine("result." + field.name() + " = new " + self._getTypeName(field) + "();")
                # Begin loop
                self._beginBlock("for (int i = 0; i < " + repetitionString + "; i++)")
                # Wrap with try
                self._beginBlock("try")
                # Main handler
                handleRepeatingLineForField(field)
                # Check for newline
                if (line.isSplitByNewline()):
                    self._beginBlock("if (i != " + repetitionString + " - 1)")
                    handleEmptyLine()
                    self._endBlock()
                # End try
                self._endBlock()
                # Catch any error to throw appropriate error message
                self._beginBlock("catch (Exception e)")
                writeLine("throw new RuntimeException(\"Parser Error on line \" + lineNumber[0] +"
                    + "\": Expecting exactly \" + " + repetitionString + " + \" \\\"" + field.typeName()
                    + "\\\" when parsing \\\"" + className + "." + field.name()
                    + "\\\" (\" + i + \" found).\");")
                self._endBlock()
                # End loop
                self._endBlock()
            elif line.isZeroOrMoreRepetition():
                field = line.getField(0)
                # Wrap with try block
                self._beginBlock("try")
                # Initialize object
                writeLine("result." + field.name() + " = new " + self._getTypeName(field) + "();")
                # Save initial position
                writeLine("prevFilePos = getFilePointer(f);")
                writeLine("prevLineNumber = lineNumber[0];")
                # Begin infinite loop
                self._beginBlock("while (true)")
                # Main handler
                handleRepeatingLineForField(field)
                writeLine("prevFilePos = getFilePointer(f);")
                writeLine("prevLineNumber = lineNumber[0];")
                # Check for newline
                if (line.isSplitByNewline()):
                    handleEmptyLine()
                # End infinite loop and try block
                self._endBlock()
                self._endBlock()
                # Catch any errors, reset line number and continue
                self._beginBlock("catch (Exception e)")
                writeLine("seek(f, prevFilePos);")
                writeLine("lineNumber[0] = prevLineNumber;")
                self._endBlock()
            elif line.isOneOrMoreRepetition:
                field = line.getField(0)
                # Wrap with try block
                self._beginBlock("try")
                # Initialize object and checker to ensure at least one repetition
                writeLine("didRepeatOnce = false;")
                writeLine("result." + field.name() + " = new " + self._getTypeName(field) + "();")
                # Begin infinite loop
                self._beginBlock("while (true)")
                # Main handler
                handleRepeatingLineForField(field)
                writeLine("prevFilePos = getFilePointer(f);")
                writeLine("prevLineNumber = lineNumber[0];")
                writeLine("didRepeatOnce = true;")
                # Check for newline
                if (line.isSplitByNewline()):
                    handleEmptyLine()
                # End infinite loop and try block
                self._endBlock()
                self._endBlock()
                # Catch any errors, either (1) reset line number and continue (2) error if did not repeat once
                self._beginBlock("catch (Exception e)")
                self._beginBlock("if (!didRepeatOnce)")
                writeLine("throw new RuntimeException(\"Parser Error on line \" + lineNumber[0] +"
                    + "\": Expecting at least 1 \\\"" + field.typeName()
                    + "\\\" when parsing \\\"" + className + "." + field.name()
                    + "\\\" (0 found).\");")
                self._endBlock()
                writeLine("seek(f, prevFilePos);")
                writeLine("lineNumber[0] = prevLineNumber;")
                self._endBlock()
            else:
                raise Exception("This should never happen.")


        self._beginBlock("public static " + className + " parse" + className + "(RandomAccessFile f, int[] lineNumber)")
        generateSetup()

        # Handle the three different cases, helpers are inner functions defined above
        for line in lines:
            if line.isEmpty():
                handleEmptyLine()
            elif line.isRepeating():
                handleRepeatingLine(line)
            else:
                handleSimpleLine(line)

        writeLine("return result;")
        self._endBlock()
        self.currentFile.writeNewline()

    ################################################################################
    # Generate Main File
    ################################################################################

    def generateMainFile(self):
        """ Generate main file where the main function resides. """
        self.currentFile = self.main
        self.generateMainFileHeader()
        self._beginBlock("public class " + splitext(basename(self.currentFile.filename))[0])
        self.generateMainFunction()
        self.generateInputParserFunction()
        self._endBlock()

    def generateMainFileHeader(self):
        """ For generating the main file header, such as the import statements. """
        # Import library headers
        self.currentFile.writeLine("import java.io.RandomAccessFile;")
        self.currentFile.writeLine("import java.io.FileNotFoundException;")
        self.currentFile.writeLine("import java.io.IOException;")
        self.currentFile.writeLine("import java.io.EOFException;")
        self.currentFile.writeNewline()

    def generateMainFunction(self):
        """ For generating the empty main method that the user can fill in. """
        self._beginBlock("public static void main(String[] args)")
        self.currentFile.comment("Call " + CodeGenerator.PARSE_INPUT + "(filename) to parse the file of that name.")
        self._endBlock()
        self.currentFile.writeNewline()

    def generateInputParserFunction(self):
        """ For generating the function to parse an input file. """
        writeLine = self.currentFile.writeLine
        # Begin function declaration
        self._beginBlock("private static " + self.bodyTypeName
            + " " + CodeGenerator.PARSE_INPUT + "(String filename)")

        # Main try block
        self._beginBlock("try")
        # Initial setup
        writeLine("RandomAccessFile f = new RandomAccessFile(filename, \"r\");")
        writeLine("int[] lineNumber = {1};")
        # Begin parsing
        writeLine(self.bodyTypeName + " result = "
            + CodeGenerator.UTIL_FILE_NAME + "." + self.typeNameToParseFuncName[self.bodyTypeName] + "(f, lineNumber);")
        # Handle trailing newlines
        writeLine("String line;")
        self._beginBlock("while ((line = f.readLine()) != null)")
        self._beginBlock("if (!line.equals(\"\"))")
        writeLine("throw new RuntimeException(\"Parser Error on line \" + lineNumber[0] + \": Finished parsing but did not reach end of file.\");")
        self._endBlock()
        self._endBlock()
        # Finish up
        writeLine("f.close();")
        writeLine("return result;")
        self._endBlock()

        # Catch file not found
        self._beginBlock("catch (FileNotFoundException e)")
        writeLine("System.err.println(\"Input file '\" + filename + \"' not found.\");")
        writeLine("System.exit(1);")
        self._endBlock()
        # Catch random IOExceptions
        self._beginBlock("catch (IOException e)")
        writeLine("System.err.println(\"Could not open \\\"\" + filename + \"\\\".\");")
        self._endBlock()
        # All other exception catches (EOF exception caught here)
        self._beginBlock("catch (Exception e)")
        writeLine("System.err.println(e.getMessage());")
        writeLine("System.exit(1);")
        self._endBlock()

        # Should never reach this line
        writeLine("System.err.println(\"Unknown error occurred.\");")
        writeLine("System.exit(1);")
        writeLine("return null;")

        # End function declaration
        self._endBlock()

    ################################################################################
    # Helper Functions
    ################################################################################

    def _getBasicTypeName( self, typeName ):
        if isInteger(typeName):
            return "Integer"
        if isFloat(typeName):
            return "Float"
        elif isString(typeName):
            return "String"
        elif isBool(typeName):
            return "Boolean"
        elif isList(typeName):
            return "ArrayList<" + self._getBasicTypeName(listType(typeName)) + ">"
        else:
            return None


    def _getTypeName( self, field ):
        typeName = self._getBasicTypeName(field.typeName())
        if typeName == None:
            typeName = field.typeName()

        if field.isRepeating():
            return "ArrayList<" + typeName + ">"
        else:
            return typeName

    def _beginBlock( self, line ):
        self.currentFile.writeLine(line)
        self.currentFile.writeLine("{")
        self.currentFile.indent()

    def _endBlock(self):
        self.currentFile.dedent()
        self.currentFile.writeLine("}")


def pygenStaticHelpers():
    helpers = """
def readline(inputFile, className):
\tline = inputFile.readline()
\tif line == "":
\t\traise ValueError("Parser Error: Reached end of file while parsing object \\"" + className + "\\".")
\treturn line.strip()

def intParse( s, currentLineNumber ):
\ttry:
\t\treturn int(s)
\texcept ValueError as e:
\t\traise ValueError("Parser Error on line %d: Could not parse \\\"%s\\\" as int." % ( currentLineNumber, s ))

def boolParse( s, currentLineNumber ):
\tif s == "1" or s.lower() == "true":
\t\treturn True
\telif s == "0" or s.lower() == "false":
\t\treturn False
\traise ValueError("Parser Error on line %d: Could not parse \\\"%s\\\" as bool." % ( currentLineNumber, s ))

def stringParse( s, currentLineNumber ):
\treturn s

def floatParse( s, currentLineNumber ):
\ttry:
\t\treturn float(s)
\texcept ValueError as e:
\t\traise ValueError("Parser Error on line %d: Could not parse \\\"%s\\\" as float." % ( currentLineNumber, s ))

def intListParse( strings, currentLineNumber ):
\tintList = []
\tif len(strings) == 0:
\t\traise ValueError("Parser Error on line %d: Could not parse empty string as list." % currentLineNumber)
\tfor s in strings:
\t\tintList.append(intParse( s, currentLineNumber ))
\treturn intList

def boolListParse( strings, currentLineNumber ):
\tboolList = []
\tif len(strings) == 0:
\t\traise ValueError("Parser Error on line %d: Could not parse empty string as list." % currentLineNumber)
\tfor s in strings:
\t\tboolList.append(boolParse( s, currentLineNumber ))
\treturn boolList

def stringListParse( strings, currentLineNumber ):
\tstringList = []
\tif len(strings) == 0:
\t\traise ValueError("Parser Error on line %d: Could not parse empty string as list." % currentLineNumber)
\tfor s in strings:
\t\tstringList.append(stringParse( s, currentLineNumber ))
\treturn stringList

def floatListParse( strings, currentLineNumber ):
\tfloatList = []
\tif len(strings) == 0:
\t\traise ValueError("Parser Error on line %d: Could not parse empty string as list." % currentLineNumber)
\tfor s in strings:
\t\tfloatList.append(floatParse( s, currentLineNumber ))
\treturn floatList


"""
    helpers = helpers.replace( "intParse", CodeGenerator.PARSE_INT )
    helpers = helpers.replace( "boolParse", CodeGenerator.PARSE_BOOL )
    helpers = helpers.replace( "stringParse", CodeGenerator.PARSE_STRING )
    helpers = helpers.replace( "floatParse", CodeGenerator.PARSE_FLOAT )
    helpers = helpers.replace( "intListParse", CodeGenerator.PARSE_INT_LIST )
    helpers = helpers.replace( "boolListParse", CodeGenerator.PARSE_BOOL_LIST )
    helpers = helpers.replace( "stringListParse", CodeGenerator.PARSE_STRING_LIST )
    helpers = helpers.replace( "floatListParse", CodeGenerator.PARSE_FLOAT_LIST )

    # Replace the tabs with the appropriate amount of indent spaces
    helpers = helpers.replace( "\t", InstaParseFile.indentString )

    return helpers


class PythonGenerator(CodeGenerator):

    def write( self, line ):
        self.currentFile.write(line)

    def writeLine( self, line ):
        self.currentFile.writeLine(line)

    def writeNewline(self):
        self.currentFile.writeNewline()

    def comment( self, line ):
        self.currentFile.comment(line)

    def writeImportLine( self, line ):
        self.currentFile.writeImportLine(line)

    def beginBlock( self, line ):
        self.writeLine(line)
        self.currentFile.indent()

    def endBlock(self):
        self.currentFile.dedent()

    def initialize(self):
        """ Perform additional initialization if required. """
        InstaParseFile.commentString = "#"
        self.main.setExtension("py")
        self.util.setExtension("py")
        self.data.setExtension("py")

    ################################################################################
    # Generate Data File
    ################################################################################

    def generateDataFileHeader(self):
        """ For generating the data file header, such as the import statements. """
        self.writeLine("#!/usr/bin/env python")
        self.writeNewline()

    def generateClass( self, className, fields ):
        """ Helper function for generating the code segement defining a class (or the corresponding
        data structure). The first argument is the class name and the second argument is a list of
        fields (in order) of that class. """
        self.beginBlock("class %s:" % className)
        self.beginBlock("def __init__(self):")
        # Initialize each field to be None
        for f in fields:
            self.writeLine("self.%s = None" % f.name())
        self.endBlock()
        self.endBlock()
        self.writeNewline()

    ################################################################################
    # Generate Util File
    ################################################################################

    def generateUtilFileHeader(self):
        """ For generating the util file header, such as the import statements. """
        self.writeLine("#!/usr/bin/env python")
        self.writeNewline()
        self.writeLine("import " + CodeGenerator.DATA_FILE_NAME)

    def generateHelperFunctions(self):
        """ For generating the helper functions that will be useful when parsing in the util file. """
        helpers =  pygenStaticHelpers()
        self.write(helpers)
        self.writeNewline()

    def generateClassParserFunction( self, className, lines ):
        """ For generating the helper functions for parsing a user defined class. The first argument
        is the class name and the second argument is a list of FormatLine's. """
        # The name of the class parser should be "parseX" where X is the class name.
        # The argument to the parser should be the input file to be parsed ,the current
        # line number and the position of the current line in the input file.
        # If parsed successfully, the parser should return a X object, the new line number and position.
        self.beginBlock("def parse%s( inputFile, currentLineNumber, currentLinePos ):" % className)
        self.writeLine("userClass = %s.%s()" % ( CodeGenerator.DATA_FILE_NAME, className ))
        self.writeNewline()

        def handleEmptyLine():
            self.comment("Parsing empty line")
            self.writeLine("fields = readline(inputFile, \"%s\").split()" % className)
            self.beginBlock("if len(fields) > 0:")
            self.writeLine("raise ValueError(\"Parser Error on line %d: Should be an empty line.\"" + \
                " % (currentLineNumber))")
            self.endBlock()
            self.writeLine("currentLineNumber += 1")
            self.writeLine("currentLinePos = inputFile.tell()")

        def handleSimpleLine(line):
            # The case where there is only one primitve field that is not a list.
            if line.numFields() == 1 and line.getField(0).isPrimitive() and not line.getField(0).isList():
                field = line.getField(0)
                self.writeLine("userClass.%s = %s( readline(inputFile, \"%s\"), currentLineNumber )" % \
                    ( field.name(), self.typeNameToParseFuncName[field.typeName()], className ))
                self.writeLine("currentLineNumber += 1")
                self.writeLine("currentLinePos = inputFile.tell()")
            # The case where ther is only one list primitive field.
            elif line.numFields() == 1 and line.getField(0).isPrimitive() and line.getField(0).isList():
                field = line.getField(0)
                listType = "list(%s)" % field.listType()
                self.writeLine("fields = readline(inputFile, \"%s\").split('%s')" % (className, self.format.lineDelimiter()))
                self.writeLine("userClass.%s = %s( fields, currentLineNumber )" % ( field.name(), self.typeNameToParseFuncName[listType] ))
                self.writeLine("currentLineNumber += 1")
                self.writeLine("currentLinePos = inputFile.tell()")
            # The case where there is only one non-primitive field.
            elif line.numFields() == 1 and not line.getField(0).isPrimitive():
                field = line.getField(0)
                self.writeLine("userClass.%s, currentLineNumber, currentLinePos = %s( inputFile, currentLineNumber, currentLinePos )" % ( field.name(), self.typeNameToParseFuncName[field.typeName()] ))
            # The case where there is multiple fields on a line. The fields are all primitives.
            else:
                self.writeLine("fields = readline(inputFile, \"%s\").split('%s')" % (className, self.format.lineDelimiter()))
                # If the last field is not a list, then the number of fields should match exactly
                if not line.getField(-1).isList():
                    self.beginBlock("if len(fields) != %d:" % line.numFields())
                    self.writeLine("raise ValueError('Parser Error on line %d: Expecting " + \
                        str(line.numFields()) + " fields (%d found).' % ( currentLineNumber, len(fields) ))")
                    self.endBlock()
                # Else there should be at least X fields on the line, where X is the number of fields
                # on the line in the format file
                else:
                    self.beginBlock("if len(fields) < %d:" % (line.numFields()))
                    self.writeLine("raise ValueError('Parser Error on line %d: Expecting " + \
                        str(line.numFields()) + " fields (%d found).' % ( currentLineNumber, len(fields) ))")
                    self.endBlock()
                for i, field in enumerate(line):
                    if field.isList():
                        listType = "list(%s)" % field.listType()
                        self.writeLine("userClass.%s = %s( fields[%d:], currentLineNumber )" % ( \
                            field.name(), self.typeNameToParseFuncName[field.typeName()], i ))
                    else:
                        self.writeLine("userClass.%s = %s( fields[%d], currentLineNumber )" % ( \
                            field.name(), self.typeNameToParseFuncName[field.typeName()], i ))
                self.writeLine("currentLineNumber += 1")
                self.writeLine("currentLinePos = inputFile.tell()")

        def handleRepeatingLine(line):
            field = line.getField(0)
            self.writeLine("userClass.%s = []" % field.name())

            if line.isZeroOrMoreRepetition() or line.isOneOrMoreRepetition():
                self.writeLine("prevLineNumber = currentLineNumber")
                self.writeLine("prevLinePos = currentLinePos")
                self.beginBlock("try:")
                self.beginBlock("while True:")
                # Field is an user defined class.
                if not field.isPrimitive():
                    self.writeLine("retObj, currentLineNumber, currentLinePos = %s( inputFile, currentLineNumber, currentLinePos )" % self.typeNameToParseFuncName[field.typeName()])
                # Field is a non-list primitive.
                elif field.isPrimitive() and not field.isList():
                    self.writeLine("retObj = %s( readline(inputFile, \"%s\"), currentLineNumber )" % \
                        (self.typeNameToParseFuncName[field.typeName()], className))
                    self.writeLine("currentLineNumber += 1")
                    self.writeLine("currentLinePos = inputFile.tell()")
                # Field is a list primitive.
                else:
                    listType = "list(%s)" % field.listType()
                    self.writeLine("fields = readline(inputFile, \"%s\").split(%s)" % (className, self.format.lineDelimiter()))
                    self.writeLine("retObj = %s( fields, currentLineNumber )" % \
                        self.typeNameToParseFuncName[listType])
                    self.writeLine("currentLineNumber += 1")
                    self.writeLine("currentLinePos = inputFile.tell()")
                self.writeLine("userClass.%s.append(retObj)" % field.name())
                if line.isSplitByNewline():
                    self.writeLine("prevLineNumber = currentLineNumber")
                    self.writeLine("prevLinePos = currentLinePos")
                    handleEmptyLine()
                self.endBlock()
                self.endBlock()

                self.beginBlock("except ( ValueError, EOFError ) as e:")
                if line.isOneOrMoreRepetition():
                    self.beginBlock("if len(userClass.%s) < 1:" % field.name())
                    self.writeLine("raise ValueError(\"Parser Error on line %d: Expecting at least 1 \\\"" + \
                        field.typeName() + "\\\" when parsing \\\"" + className + "." + field.name() + \
                        "\\\" (0 found).\" % currentLineNumber)")
                    self.endBlock()
                if line.isSplitByNewline():
                    self.writeLine("currentLineNumber = prevLineNumber")
                    self.writeLine("currentLinePos = prevLinePos")
                self.writeLine("inputFile.seek(currentLinePos)")
                self.endBlock()

            elif line.isIntegerRepetition() or line.isVariableRepetition():
                numRepetition = line.repetitionAmountString()
                if line.isVariableRepetition():
                    numRepetition = "userClass." + numRepetition

                self.beginBlock("try:")
                self.beginBlock("for _index in xrange(%s):" % numRepetition)
                # Field is an user defined class.
                if not field.isPrimitive():
                    self.writeLine("retObj, currentLineNumber, currentLinePos = %s( inputFile, currentLineNumber, currentLinePos )" % self.typeNameToParseFuncName[field.typeName()])
                # Field is a non-list primitive.
                elif field.isPrimitive() and not field.isList():
                    self.writeLine("retObj = %s( readline(inputFile, \"%s\"), currentLineNumber )" % \
                        (self.typeNameToParseFuncName[field.typeName()], className))
                    self.writeLine("currentLineNumber += 1")
                    self.writeLine("currentLinePos = inputFile.tell()")
                # Field is a list primitive.
                else:
                    listType = "list(%s)" % field.listType()
                    self.writeLine("fields = readline(inputFile, \"%s\").split(%s)" % (className, self.format.lineDelimiter()))
                    self.writeLine("retObj = %s( fields, currentLineNumber )" % \
                        self.typeNameToParseFuncName[listType])
                    self.writeLine("currentLineNumber += 1")
                self.writeLine("userClass.%s.append(retObj)" % field.name())
                if line.isSplitByNewline():
                    self.beginBlock("if _index + 1 < %s:" % numRepetition)
                    handleEmptyLine()
                    self.endBlock()
                self.endBlock()
                self.endBlock()

                self.beginBlock("except ValueError as e:")
                self.writeLine("raise ValueError('Parser Error on line %d: Expecting exactly %d \\\"" + \
                    field.typeName() + "\\\" when parsing \\\"" + className + "." + field.name() + \
                    "\\\" (%d found)' % ( currentLineNumber, " + numRepetition + ", _index ))")
                self.endBlock()

        def handleLine(line):
            if line.isEmpty():
                handleEmptyLine()
            elif line.isRepeating():
                handleRepeatingLine(line)
            else:
                handleSimpleLine(line)

        for line in lines:
            handleLine(line)
            self.writeNewline()

        self.writeLine("return userClass, currentLineNumber, currentLinePos")
        self.endBlock()
        self.writeNewline()

    ################################################################################
    # Generate Main File
    ################################################################################

    def generateMainFileHeader(self):
        """ For generating the main file header, such as the import statements. """
        self.writeLine("#!/usr/bin/env python")
        self.writeNewline()
        self.writeLine("import " + CodeGenerator.UTIL_FILE_NAME)
        self.writeLine("import sys")
        self.writeNewline()

    def generateInputParserFunction(self):
        """ For generating the function to parse an input file. """
        self.beginBlock("def %s( filename ):" % CodeGenerator.PARSE_INPUT)

        self.beginBlock("try:")
        # Open file
        self.writeLine("inputFile = open(filename, 'r')")
        # Parse file
        self.writeLine("body, lineNumber, linePos = %s.%s( inputFile, 1, 0 )"
            % ( CodeGenerator.UTIL_FILE_NAME, self.typeNameToParseFuncName[self.bodyTypeName] ))
        # Handle trailing newlines
        self.writeLine("line = inputFile.readline()")
        self.beginBlock("while line != '':")
        self.beginBlock("if line.strip() != '':")
        self.writeLine("sys.stderr.write(\"Parser Error on line %d: Finished parsing but did not reach end of file.\" % lineNumber)")
        self.writeLine("exit(1)")
        self.endBlock()
        self.writeLine("lineNumber += 1")
        self.writeLine("line = inputFile.readline()")
        self.endBlock()

        self.writeLine("return body")
        self.endBlock()

        # Catch File IO errors
        self.beginBlock("except IOError as e:")
        self.writeLine("sys.stderr.write('Parser Error: Problem opening file, %s' % e)" )
        self.writeLine("exit(1)")
        self.endBlock()
        # Catch parser errors
        self.beginBlock("except ValueError as e:")
        self.writeLine("sys.stderr.write(str(e) + \"\\n\")")
        self.writeLine("exit(1)")
        self.endBlock()
        # Catch all other errors
        self.beginBlock("except Exception as e:")
        self.writeLine("sys.stderr.write('Parser Error: %s\\n' % e)")
        self.writeLine("import traceback")
        self.writeLine("traceback.print_exc()")
        self.writeLine("exit(1)")
        self.endBlock()

        self.endBlock()
        self.writeNewline()

    def generateMainFunction(self):
        """ For generating the empty main method that the user can fill in. """
        self.beginBlock("if __name__ == '__main__':")
        self.currentFile.comment("Call " + CodeGenerator.PARSE_INPUT + "(filename) to parse the file of that name.")
        self.writeLine("pass")
        self.endBlock()



def cppgenStaticHelpers():
    helpers = """
static const std::string ws = " \\t\\n\\r\\f\\v";

inline std::string rtrim(std::string s, std::string t = ws)
{
\ts.erase(s.find_last_not_of(t) + 1);
\treturn s;
}

inline std::string ltrim(std::string s, std::string t = ws)
{
\ts.erase(0, s.find_first_not_of(t));
\treturn s;
}

inline std::string trim(std::string s, std::string t = ws)
{
\treturn ltrim(rtrim(s, t), t);
}

std::vector<std::string> copyRange(std::vector<std::string> v, int begin, int end)
{
\tusing namespace std;
\tvector<string>::const_iterator first = v.begin() + begin;
\tvector<string>::const_iterator last = v.begin() + end;
\treturn vector<string>(first, last);
}

std::vector<std::string> split(std::string s, std::string delim) {
\tusing namespace std;
\tvector<string> result;

\tsize_t delimLength = delim.length();
\tsize_t start = 0, end = 0;
\twhile ((end = s.find(delim, start)) != string::npos) {
\t\tresult.push_back(s.substr(start, end - start));
\t\tstart = end + delimLength;
\t}
\tresult.push_back(s.substr(start, s.length() - start));

\treturn result;
}

std::string lowercase(std::string &s)
{
\tusing namespace std;
\tchar result[s.length() + 1];
\tfor (unsigned int i = 0; i < s.length(); i++)
\t{
\t\tresult[i] = tolower(s[i]);
\t}
\tresult[s.length()] = '\0';
\treturn string(result);
}

int cppgenParseInt(std::string s, int& lineNumber)
{
\tusing namespace std;
\tstringstream ss(s);
\tint result;
\tss >> result;
\tif (!ss.eof() || ss.fail())
\t{
\t\tstringstream err;
\t\terr << "Parser Error on line " << lineNumber << ": Could not parse \\"" << s << "\\" as int.";
\t\tthrow invalid_argument(err.str());
\t}
\treturn result;
}

bool cppgenParseBool(std::string s, int& lineNumber)
{
\tusing namespace std;
\tif (s.compare("1") == 0 || lowercase(s).compare("true") == 0)
\t{
\t\treturn true;
\t}
\telse if (s.compare("0") == 0 || lowercase(s).compare("false") == 0)
\t{
\t\treturn false;
\t}

\tstringstream err;
\terr << "Parser Error on line " << lineNumber << ": Could not parse \\"" << s << "\\" as bool.";
\tthrow invalid_argument(err.str());
}

std::string cppgenParseString(std::string s, int& lineNumber)
{
\treturn s;
}

float cppgenParseFloat(std::string s, int& lineNumber)
{
\tusing namespace std;
\tstringstream ss(s);
\tfloat result;
\tss >> result;
\tif (!ss.eof() || ss.fail())
\t{
\t\tstringstream err;
\t\terr << "Parser Error on line " << lineNumber << ": Could not parse \\"" << s << "\\" as float.";
\t\tthrow invalid_argument(err.str());
\t}
\treturn result;
}

std::vector<int> cppgenParseIntList(std::vector<std::string> strings, int& lineNumber)
{
\tusing namespace std;
\tif (strings.size() == 0)
\t{
\t\tstringstream err;
\t\terr << "Parser Error on line " << lineNumber << ": Could not parse empty string as list.";
\t\tthrow invalid_argument(err.str());
\t}
\tvector<int> resval;
\tfor (unsigned int i = 0; i < strings.size(); i++)
\t{
\t\tresval.push_back(cppgenParseInt(strings[i], lineNumber));
\t}
\treturn resval;
}

std::vector<bool> cppgenParseBoolList(std::vector<std::string> strings, int& lineNumber)
{
\tusing namespace std;
\tif (strings.size() == 0)
\t{
\t\tstringstream err;
\t\terr << "Parser Error on line " << lineNumber << ": Could not parse empty string as list.";
\t\tthrow invalid_argument(err.str());
\t}
\tvector<bool> resval;
\tfor (unsigned int i = 0; i < strings.size(); i++)
\t{
\t\tresval.push_back(cppgenParseBool(strings[i], lineNumber));
\t}
\treturn resval;
}

std::vector<std::string> cppgenParseStringList(std::vector<std::string> strings, int& lineNumber)
{
\tusing namespace std;
\tif (strings.size() == 0)
\t{
\t\tstringstream err;
\t\terr << "Parser Error on line " << lineNumber << ": Could not parse empty string as list.";
\t\tthrow invalid_argument(err.str());
\t}
\tvector<string> resval;
\tfor (unsigned int i = 0; i < strings.size(); i++)
\t{
\t\tresval.push_back(cppgenParseString(strings[i], lineNumber));
\t}
\treturn resval;
}

std::vector<float> cppgenParseFloatList(std::vector<std::string> strings, int& lineNumber)
{
\tusing namespace std;
\tif (strings.size() == 0)
\t{
\t\tstringstream err;
\t\terr << "Parser Error on line " << lineNumber << ": Could not parse empty string as list.";
\t\tthrow invalid_argument(err.str());
\t}
\tvector<float> resval;
\tfor (unsigned int i = 0; i < strings.size(); i++)
\t{
\t\tresval.push_back(cppgenParseFloat(strings[i], lineNumber));
\t}
\treturn resval;
}

std::string readLine(std::ifstream &f, std::string className)
{
\tusing namespace std;
\tif (f.eof())
\t{
\t\tstringstream err;
\t\terr << "Parser Error: Reached end of file while parsing object \\"" << className << "\\".";
\t\tthrow runtime_error(err.str());
\t}
\tstring result;
\tgetline(f, result);
\tif (f.bad())
\t{
\t\tthrow runtime_error("IO Error: Unknown problem when reading input file.");
\t}
\treturn result;
}

void seek(std::ifstream &f, std::streampos pos)
{
\tusing namespace std;
\tf.seekg(pos);
\tif (f.bad())
\t{
\t\tthrow runtime_error("IO Error: Unknown problem when reading input file.");
\t}
}

std::streampos getFilePointer(std::ifstream &f)
{
\tusing namespace std;
\tstreampos pos = f.tellg();
\tif (pos == -1)
\t{
\t\tthrow runtime_error("IO Error: Unknown problem when reading input file.");
\t}
\treturn pos;
}
"""

    helpers = helpers.replace("cppgenParseIntList", CodeGenerator.PARSE_INT_LIST)
    helpers = helpers.replace("cppgenParseBoolList", CodeGenerator.PARSE_BOOL_LIST)
    helpers = helpers.replace("cppgenParseStringList", CodeGenerator.PARSE_STRING_LIST)
    helpers = helpers.replace("cppgenParseFloatList", CodeGenerator.PARSE_FLOAT_LIST)
    helpers = helpers.replace("cppgenParseInt", CodeGenerator.PARSE_INT)
    helpers = helpers.replace("cppgenParseBool", CodeGenerator.PARSE_BOOL)
    helpers = helpers.replace("cppgenParseString", CodeGenerator.PARSE_STRING)
    helpers = helpers.replace("cppgenParseFloat", CodeGenerator.PARSE_FLOAT)

    # Replace the tabs with the appropriate amount of indent spaces
    helpers = helpers.replace( "    ", InstaParseFile.indentString )

    return helpers



""" Class for generating CPP code. """
class CPPGenerator(CodeGenerator):

    def initialize(self):
        """ Perform additional initialization if required. """
        InstaParseFile.commentString = "//"
        self.main.setExtension("cpp")
        self.util.setExtension("h")
        self.data.setExtension("h")

    ################################################################################
    # Generate Data File
    ################################################################################

    def generateDataFile(self):
        """ Generate classes in a separate data file. """
        self.currentFile = self.data
        self.currentFile.writeLine("#ifndef %s_H" % CodeGenerator.DATA_FILE_NAME.upper())
        self.currentFile.writeLine("#define %s_H" % CodeGenerator.DATA_FILE_NAME.upper())
        self.currentFile.writeNewline()
        CodeGenerator.generateDataFile(self);
        self.currentFile.writeLine("#endif")

    def generateDataFileHeader(self):
        """ For generating the data file header, such as the import statements. """
        writeLine = self.currentFile.writeLine
        writeNewline = self.currentFile.writeNewline
        writeLine("#include <vector>")
        writeLine("#include <string>")
        writeNewline()

    def generateClass( self, className, fields ):
        """ Helper function for generating the code segement defining a class (or the corresponding
        data structure). The first argument is the class name and the second argument is a list of
        fields (in order) of that class. """
        self.typeNameToParseFuncName[className] = "parse%s" % className
        self._beginBlock("struct " + className )
        for field in fields:
            self.currentFile.writeLine(self._getTypeName(field) + " " + field.name() + ";")
        self._endBlock(";")
        self.currentFile.writeNewline()

    ################################################################################
    # Generate Util File
    ################################################################################

    def generateUtilFile(self):
        self.currentFile = self.util
        self.currentFile.writeLine("#ifndef %s_H" % CodeGenerator.UTIL_FILE_NAME.upper())
        self.currentFile.writeLine("#define %s_H" % CodeGenerator.UTIL_FILE_NAME.upper())
        self.generateUtilFileHeader()
        self._beginBlock("namespace " + CodeGenerator.PARSER_NAME)
        self.generateHelperFunctions()
        self.generateClassParserFunctions()
        self._endBlock()
        self.currentFile.writeLine("#endif")

    def generateUtilFileHeader(self):
        """ For generating the util file header, such as the import statements. """
        # Import library headers
        self.currentFile.writeLine("#include <vector>")
        self.currentFile.writeLine("#include <sstream>")
        self.currentFile.writeLine("#include <string>")
        self.currentFile.writeLine("#include <cctype>")
        self.currentFile.writeLine("#include <stdexcept>")
        self.currentFile.writeLine("#include <fstream>")
        self.currentFile.writeNewline()

        # Import data header
        self.currentFile.writeLine("#include \"" + CodeGenerator.DATA_FILE_NAME + ".h" + "\"")

    def generateHelperFunctions(self):
        """ For generating the helper functions that will be useful when parsing in the util file. """
        # Static helpers for primitives
        helpers = cppgenStaticHelpers()
        map(lambda s: self.currentFile.writeLine(s), helpers.splitlines())
        self.currentFile.writeNewline()

    def generateClassParserFunction( self, className, lines ):
        """ For generating a helper functions for parsing a user defined class. The first argument
        is the class name and the second argument is a list of FormatLine's. """
        writeLine = self.currentFile.writeLine
        write = self.currentFile.write

        def isSimplePrimitive(field):
            return field.isInteger() or field.isFloat() or field.isString() or field.isBool()

        def generateSetup():
            # include std in all parser functions
            writeLine("using namespace std;")

            # Helper to do some setup in every parser function
            writeLine(className + " result;")
            didSplit = False
            didRepeat = False
            didRepeatPlus = False

            for line in lines:
                didRepeat = didRepeat or line.isRepeating()
                didRepeatPlus = didRepeatPlus or  line.isOneOrMoreRepetition()
                didSplit = didSplit or line.numFields() > 1 or (not line.isEmpty() and line.getField(0).isList())

            if didSplit:
                writeLine("vector<string> fields;")
            if didRepeat:
                writeLine("streampos prevFilePos = getFilePointer(f);")
                writeLine("int prevLineNumber = lineNumber;")
            if didRepeatPlus:
                writeLine("bool didRepeatOnce = false;")

        def handleEmptyLine():
            # Handle the empty line case
            self._beginBlock("if (!(trim(readLine(f, \"" + className + "\")).compare(\"\") == 0))")
            writeLine("stringstream err;")
            writeLine("err << \"Parser Error on line \"  << lineNumber << " +
                "\": Should be an empty line.\";")
            writeLine("throw invalid_argument(err.str());")
            self._endBlock()
            writeLine("lineNumber += 1;")

        def handleSimpleLineOneField(field):
            # Helper for handleSimpleLine
            if isSimplePrimitive(field):
                # Field is simple, just parse it
                writeLine("result." + field.name() + " = "
                    + self.typeNameToParseFuncName[field.typeName()] + "(readLine(f, \"" + className + "\"), lineNumber);")
                writeLine("lineNumber += 1;")
            elif field.isPrimitive():
                # Field is primitive list, split line
                writeLine("fields = split(readLine(f, \"" + className + "\"), \"" + self.format.lineDelimiter() + "\");")
                write("result." + field.name() + " = "
                    + self.typeNameToParseFuncName["list(%s)" % field.listType()] + "(fields, lineNumber);")
                writeLine("lineNumber += 1;")
            else:
                # Field is a class, recurse
                writeLine("result." + field.name() + " = "
                    + self.typeNameToParseFuncName[field.typeName()] + "(f, lineNumber);")

        def handleSimpleLineMultipleField(index, field):
            # Helper for handleSimpleLine
            if isSimplePrimitive(field):
                writeLine("result." + field.name() + " = "
                    + self.typeNameToParseFuncName[field.typeName()]
                    + "(fields[" + str(index) + "], lineNumber);")
            elif field.isPrimitive():
                # Field is primitive list, use rest of fields)
                # FIXME WRONG
                writeLine("result." + field.name() + " = "
                    + self.typeNameToParseFuncName["list(%s)" % field.listType()]
                    + "(copyRange(fields, " + str(index) + ", fields.size()), lineNumber);")
            else:
                # Field is a class? Cannot be!
                raise Exception("This should never happen.")

            writeLine("lineNumber += 1;")

        def handleSimpleLine(line):
            if line.numFields() == 1:
                # Only one field, no need to split unnecessarily
                handleSimpleLineOneField(line.getField(0))
            else:
                # Multiple fields, split it
                writeLine("fields = split(readLine(f, \"" + className + "\"), \"" + self.format.lineDelimiter() + "\");")
                if (line.getField(-1).isList()):
                    self._beginBlock("if (fields.size() < " + str(line.numFields()) + ")")
                else:
                    self._beginBlock("if (fields.size() != " + str(line.numFields()) + ")")
                writeLine("stringstream err;")
                writeLine("err << \"Parser Error on line \" << lineNumber << " +
                    "\": Expecting " + str(line.numFields()) + " fields (\" << fields.size() << \" found).\";")
                writeLine("throw invalid_argument(err.str());")
                self._endBlock()
                for index, field in enumerate(line):
                    handleSimpleLineMultipleField(index, field)

        def handleRepeatingLineForField(field):
            # Helper for handleRepeating
            if isSimplePrimitive(field):
                # Field is simple, just parse it
                writeLine("result." + field.name() + ".push_back("
                    + self.typeNameToParseFuncName[field.typeName()] + "(readLine(f, \"" + className + "\"), lineNumber));")
                writeLine("lineNumber += 1;")
            elif field.isPrimitive():
                # Field is primitive list, split line
                writeLine("fields = split(readLine(f, \"" + className + "\"), \"" + self.format.lineDelimiter() + "\");")
                writeLine("result." + field.name() + ".push_back("
                    + self.typeNameToParseFuncName["list(%s)" % field.listType()] + "(fields, lineNumber));")
                writeLine("lineNumber += 1;")
            else:
                # Field is a class, recurse
                writeLine("result." + field.name() + ".push_back("
                    + self.typeNameToParseFuncName[field.typeName()] + "(f, lineNumber));")

        def handleRepeatingLine(line):
            # Must be a primitive or class repeated
            if line.isIntegerRepetition() or line.isVariableRepetition():
                # Constant repetition amount
                field = line.getField(0)
                # Generate the repetition string
                repetitionString = ""
                if line.isIntegerRepetition():
                    repetitionString = str(line.repetitionAmountString())
                else:
                    repetitionString =  "result." + line.repetitionAmountString()
                # Begin loop
                self._beginBlock("for (int i = 0; i < " + repetitionString + "; i++)")
                # Wrap handler with try
                self._beginBlock("try")
                # Main handler
                handleRepeatingLineForField(field)
                # Check for newline
                if (line.isSplitByNewline()):
                    self._beginBlock("if (i != " + repetitionString + " - 1)")
                    handleEmptyLine()
                    self._endBlock()
                # End try
                self._endBlock()
                # Catch any error to throw appropriate error message
                self._beginBlock("catch (...)")
                writeLine("stringstream err;")
                writeLine("err << \"Parser Error on line \" << lineNumber << "
                    + "\": Expecting exactly \" << " + repetitionString + " << \" \\\"" + field.typeName()
                    + "\\\" when parsing \\\"" + className + "." + field.name()
                    + "\\\" (\" << i << \" found).\";")
                writeLine("throw runtime_error(err.str());")
                self._endBlock()
                # End loop
                self._endBlock()
            elif line.isZeroOrMoreRepetition():
                field = line.getField(0)
                # Wrap with try block
                self._beginBlock("try")
                # Save initial position
                writeLine("prevFilePos = getFilePointer(f);")
                writeLine("prevLineNumber = lineNumber;")
                # Begin infinite loop
                self._beginBlock("while (true)")
                # Main handler
                handleRepeatingLineForField(field)
                writeLine("prevFilePos = getFilePointer(f);")
                writeLine("prevLineNumber = lineNumber;")
                # Check for newline
                if (line.isSplitByNewline()):
                    handleEmptyLine()
                # End infinite loop and try block
                self._endBlock()
                self._endBlock()
                # Catch any errors, reset line number and continue
                self._beginBlock("catch (...)")
                writeLine("seek(f, prevFilePos);")
                writeLine("lineNumber = prevLineNumber;")
                self._endBlock()
            elif line.isOneOrMoreRepetition:
                field = line.getField(0)
                # Wrap with try block
                self._beginBlock("try")
                # Initialize object and checker to ensure at least one repetition
                writeLine("didRepeatOnce = false;")
                # Begin infinite loop
                self._beginBlock("while (true)")
                # Main handler
                handleRepeatingLineForField(field)
                writeLine("prevFilePos = getFilePointer(f);")
                writeLine("prevLineNumber = lineNumber;")
                writeLine("didRepeatOnce = true;")
                # Check for newline
                if (line.isSplitByNewline()):
                    handleEmptyLine()
                # End infinite loop and try block
                self._endBlock()
                self._endBlock()
                # Catch any errors, either (1) reset line number and continue (2) error if did not repeat once
                self._beginBlock("catch (...)")
                self._beginBlock("if (!didRepeatOnce)")
                writeLine("stringstream err;")
                writeLine("err << \"Parser Error on line \" << lineNumber << "
                    + "\": Expecting at least 1 \\\"" + field.typeName()
                    + "\\\" when parsing \\\"" + className + "." + field.name()
                    + "\\\" (0 found).\";")
                writeLine("throw invalid_argument(err.str());")
                self._endBlock()
                writeLine("seek(f, prevFilePos);")
                writeLine("lineNumber = prevLineNumber;")
                self._endBlock()
            else:
                raise Exception("This should never happen.")


        self._beginBlock(className + " parse" + className + "(std::ifstream& f, int& lineNumber)")
        generateSetup()

        # Handle the three different cases, helpers are inner functions defined above
        for line in lines:
            if line.isEmpty():
                handleEmptyLine()
            elif line.isRepeating():
                handleRepeatingLine(line)
            else:
                handleSimpleLine(line)

        writeLine("return result;")
        self._endBlock()
        self.currentFile.writeNewline()

    ################################################################################
    # Generate Main File
    ################################################################################

    def generateMainFile(self):
        """ Generate main file where the main function resides. """
        self.currentFile = self.main
        self.generateMainFileHeader()
        self.generateForwardDeclarations()
        self.generateMainFunction()
        self.generateInputParserFunction()

    def generateMainFileHeader(self):
        """ For generating the main file header, such as the import statements. """
        # Import library headers
        self.currentFile.writeLine("#include <vector>")
        self.currentFile.writeLine("#include <string>")
        self.currentFile.writeLine("#include <stdexcept>")
        self.currentFile.writeLine("#include <fstream>")
        self.currentFile.writeLine("#include <iostream>")
        self.currentFile.writeNewline()
        # Import data and util headers
        self.currentFile.writeLine("#include \"" + CodeGenerator.DATA_FILE_NAME + ".h" + "\"")
        self.currentFile.writeLine("#include \"" + CodeGenerator.UTIL_FILE_NAME + ".h" + "\"")
        self.currentFile.writeNewline()

    def generateForwardDeclarations(self):
        self.currentFile.writeLine(self.bodyTypeName + " " + CodeGenerator.PARSE_INPUT + "(const std::string &filename);")
        self.currentFile.writeNewline()

    def generateMainFunction(self):
        """ For generating the empty main method that the user can fill in. """
        self._beginBlock("int main(int argc, char** argv)")
        self.currentFile.comment("Call " + CodeGenerator.PARSE_INPUT + "(filename) to parse the file of that name.")
        self._endBlock()
        self.currentFile.writeNewline()

    def generateInputParserFunction(self):
        """ For generating the function to parse an input file. """
        writeLine = self.currentFile.writeLine
        # Begin function declaration
        self._beginBlock(self.bodyTypeName + " " + CodeGenerator.PARSE_INPUT + "(const std::string &filename)")
        writeLine("using namespace std;")

        # Open file
        writeLine("ifstream f(filename.c_str(), ios_base::in);")
        self._beginBlock("if (f.fail())")
        writeLine("cerr << \"Could not open \\\"\" + filename + \"\\\".\" << endl;")
        writeLine("exit(1);")
        self._endBlock()

        # Main try block
        self._beginBlock("try")
        # Initial setup
        writeLine("int lineNumber = 1;")
        writeLine(self.bodyTypeName + " result = "
            + CodeGenerator.PARSER_NAME + "::" + self.typeNameToParseFuncName[self.bodyTypeName] + "(f, lineNumber);")
        # Handle trailing newlines
        writeLine("string line;")
        self._beginBlock("while (getline(f, line))")
        self._beginBlock("if (!(" + CodeGenerator.PARSER_NAME + "::trim(line).compare(\"\") == 0))")
        writeLine("stringstream err;");
        writeLine("err << \"Parser Error on line\" << lineNumber << \": Finished parsing but did not reach end of file.\";")
        writeLine("throw runtime_error(err.str());")
        self._endBlock()
        self._endBlock()
        writeLine("return result;")
        self._endBlock()

        # Catch parser errors
        self._beginBlock("catch (invalid_argument& ia)")
        writeLine("cerr << ia.what() << endl;")
        writeLine("exit(1);")
        self._endBlock()
        # Catch parser errors
        self._beginBlock("catch (runtime_error& re)")
        writeLine("cerr << re.what() << endl;")
        writeLine("exit(1);")
        self._endBlock()
        # Catch all other errors
        self._beginBlock("catch (...)")
        writeLine("cerr << \"Unknown error occurred.\" << endl;")
        writeLine("exit(1);")
        self._endBlock()

        # Should never reach this line
        writeLine("cerr << \"Unknown error occurred.\" << endl;")
        writeLine("exit(1);")

        # End function declaration
        self._endBlock()

    ################################################################################
    # Helper Functions
    ################################################################################

    def _getBasicTypeName( self, typeName ):
        if isInteger(typeName):
            return "int"
        elif isString(typeName):
            return "std::string"
        elif isBool(typeName):
            return "bool"
        elif isFloat(typeName):
            return "float"
        elif isList(typeName):
            return "std::vector<" + self._getBasicTypeName(listType(typeName)) + ">"
        else:
            return None


    def _getTypeName( self, field ):
        typeName = self._getBasicTypeName(field.typeName())
        if typeName == None:
            typeName = field.typeName()

        if field.isRepeating():
            space = ""
            if isList(field.typeName()):
                space = " "
            return "std::vector<" + typeName + space + ">"
        else:
            return typeName

    def _beginBlock( self, line ):
        self.currentFile.writeLine(line)
        self.currentFile.writeLine("{")
        self.currentFile.indent()

    def _endBlock(self, semicolon = False):
        self.currentFile.dedent()
        self.currentFile.writeLine("}" + (";" if semicolon else ""))



USAGE = "usage: %prog [options] format_file_name"
DEFAULT_LANGUAGE = "python"

if __name__ == "__main__":
    # Option parser
    optParser = OptionParser(usage = USAGE)
    optParser.add_option( "-l", "--lang", action = "store", dest = "language",
            help = "specifies the output parser language. Defaults to using the extension on the output file name or Python. \n"
                   "Accepts 'python', 'java', or 'c++'." )
    optParser.add_option( "-o", "--output", action = "store", dest = "outputName", default = "out",
            help = "specifies the output file name" )
    (options, args) = optParser.parse_args()

    # Clean up provided flags
    if options.language == None:
        periodIndex = options.outputName.find(".")
        if periodIndex == -1:
            options.language = DEFAULT_LANGUAGE
        else:
            extension = options.outputName[options.outputName.find(".") + 1:]
            if extension == "py":
                options.language = "python"
            elif extension == "java":
                options.language = "java"
            elif extension in [ "c", "cc", "cpp" ]:
                options.language = "c++"

    # Check that a format file is provided
    if len(args) != 1:
        optParser.print_help()
        exit(1)

    # Parser format file into a object model
    parser = InstaParseFormatFileParser(args[0])
    if parser.parseFailed():
        parser.printFailures()
        exit(1)

    # Generate a format object from the object model
    formatObject = InstaParseFormat(parser.objectModel)

    # Depending on output language, call the associated code generator
    generator = None
    if options.language == "python":
        generator = PythonGenerator(options.outputName, formatObject)
    elif options.language == "java":
        generator = JavaGenerator(options.outputName, formatObject)
    elif options.language == "c++":
        generator = CPPGenerator(options.outputName, formatObject)
    else:
        print "language not supported."
        exit(1)

    generator.codeGen()

