import xml.etree.ElementTree as ET
import sys
import os
import argparse

classes = {}
maxdepth = 0
deepestclass = ''

def parse_args():
    parser = argparse.ArgumentParser(description="""scrubber.py - Constructs \
            class heirarchies from XML files""")
    parser.add_argument('-p', '--path', help='The root path to XML files')
    parser.add_argument('-o', '--output', help='The file to write output to')
    return parser.parse_args()

def updateFunctionCounts(className, funcName, virtualFuncs):
    if virtualFuncs.has_key(funcName):
        virtualFuncs[funcName] += 1
    else:
        virtualFuncs[funcName] = 1

    classes[className] = virtualFuncs

def parseBaseXml(path):
    tree = ET.parse(path)
    root = tree.getroot()
    baseclasses = []
    baseclasscount = 0
    for baseClass in root.iter('basecompoundref'):
        baseclasses.append(baseClass.text)
        if not classes.has_key(baseClass.text):
            classes[baseClass.text] = {}
        baseclasscount += 1

    # we only care about polymorphic classes
    if baseclasscount == 0:
        return

    classname = root.find('compounddef').find('compoundname').text
    print("Parsing %s" % classname)
    virtualfuncs = classes[classname]
    for baseClass in baseclasses:
        basefuncs = classes[baseClass]
        for virtualfunc in virtualfuncs.keys():
            if basefuncs.has_key(virtualfunc):
                basefuncs[virtualfunc] += 1
                if basefuncs[virtualfunc] > maxdepth:
                    maxdepth = basefuncs[virtualfunc]
                    deepestclass = classname
        classes[baseClass] = basefuncs

def getFunctionName(memberdef):
    funcName = memberdef.find('name').text + \
            memberdef.find('argsstring').text

# argsstring contains the 'override' keyword, so remove it
# so we can get the "original" function name
    funcName = funcName.replace(' override ', '')
    funcName = funcName.replace(' final ', '')
    virtidx = funcName.find('=')
    if virtidx > 0:
        funcName = funcName[0 : virtidx]
    funcName = funcName.strip()
    return funcName

def parseXml(path):
    tree = ET.parse(path)
    root = tree.getroot()
    virtualfuncs = {}

    classname = root.find('compounddef').find('compoundname').text
    print("Parsing %s" % classname)
    if classes.has_key(classname):
        virtualfuncs = classes[classname]

    for section in root.iter('sectiondef'):
        if section.attrib['kind'] == 'public-func' or \
                section.attrib['kind'] == 'protected-func':
            for memberdef in section.iter('memberdef'):
                funcName = getFunctionName(memberdef)
                if memberdef.attrib['virt'] == 'virtual':
                    updateFunctionCounts(classname, funcName, virtualfuncs)
                elif memberdef.attrib['virt'] == 'pure-virtual':
                    updateFunctionCounts(classname, funcName, virtualfuncs)

    classes[classname] = virtualfuncs

def printCounts(out):
    for className in classes.keys():
        out.write("%s:\n" % className)
        for funcName in classes[className].keys():
            out.write("\t%s: %d\n" % (funcName, classes[className][funcName]))

    out.write("Max depth: %d\n" % maxdepth)
    out.write("Deepest class: %s\n" % deepestclass)

def parseDir(rootDir, outpath):
    if outpath:
        out = open(outpath, 'w')
    else:
        out = sys.stdout

    print 'Finding class virtual functions'
    for dirName, subdirList, fileList in os.walk(rootDir):
        for fileName in fileList:
            fName, ext = os.path.splitext(fileName)
            if ext and ext == '.xml':
                parseXml(os.path.join(dirName, fileName))


    print 'Finding potential call site numbers'
    for dirName, subdirList, fileList in os.walk(rootDir):
        for fileName in fileList:
            fName, ext = os.path.splitext(fileName)
            if ext and ext == '.xml':
                parseBaseXml(os.path.join(dirName, fileName))

    printCounts(out)

def main():
    args = parse_args()
    try:
        pathname = '.'
        outpath = None
        if args.path:
            pathname = args.path
        if args.output:
            outpath = args.output
        parseDir(pathname, outpath)
    except IOError as e:
        print "I/O error({0}): {1}".format(e.errno, e.strerror)
        raise
    except:
        print "Unexpected Error: ", sys.exc_info()[0]
        raise


if __name__ == "__main__":
    main()
