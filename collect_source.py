import urllib
import json
import os
import sys

def usage():
    print "Usage: python collect_source.py <dir> <formatName> <mainName>"
    print "    <dir> is the directory under which the source files exist"
    print "    <formatName> is the name of the format file"
    print "    <mainName> the name of the main file"

def main():
    if len(sys.argv) != 4:
        usage()
        sys.exit(0)

    directoryName = sys.argv[1]
    formatName = sys.argv[2]
    mainName = sys.argv[3]

    dataFileName = "InstaParseData."
    utilFileName = "InstaParseUtil."

    jsonResult = { "classes": [] }
    for sourceName in os.listdir(directoryName):
        if sourceName == formatName:
            continue

        sourceFile = open(directoryName + "/" + sourceName, "r")
        if mainName + "." in sourceName:
            jsonResult["main"] = {"name": sourceName, "content": urllib.quote(sourceFile.read(), safe="~@#$&()*!+=:;,.?/\'")}
        elif utilFileName in sourceName:
            jsonResult["util"] = {"name": sourceName, "content": urllib.quote(sourceFile.read(), safe="~@#$&()*!+=:;,.?/\'")}
        elif dataFileName in sourceName:
            jsonResult["data"] = {"name": sourceName, "content": urllib.quote(sourceFile.read(), safe="~@#$&()*!+=:;,.?/\'")}
        else:
            jsonResult["classes"].append({"name": sourceName, "content": urllib.quote(sourceFile.read(), safe="~@#$&()*!+=:;,.?/\'")})

        sourceFile.close()
    print json.dumps(jsonResult)

if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        pass