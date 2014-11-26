import urllib
import json
import os
import sys

def usage():
    print "Usage: python collect_source.py <dir> <formatfile>"
    print "    <dir> is the directory under which the source files exist"
    print "    <formatfile> is the name of the format file"

def main():
    if len(sys.argv) != 3:
        usage()
        sys.exit(0)

    directoryName = sys.argv[1]
    formatName = sys.argv[2]
    sourceNames = [sourceName for sourceName in os.listdir(directoryName) if formatName != sourceName]
    jsonResult = {}
    for sourceName in sourceNames:
        sourceFile = open(directoryName + "/" + sourceName, "r")
        jsonResult[sourceName] = urllib.quote(sourceFile.read(), safe="~@#$&()*!+=:;,.?/\'")
        sourceFile.close()
    print json.dumps(jsonResult)

if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        pass