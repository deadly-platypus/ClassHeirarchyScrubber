import xml.etree.ElementTree as ET
import sys
import os
import argparse

classes = {}

def parse_args():
    parser = argparse.ArgumentParser(description="""scrubber.py - Constructs \
            class heirarchies from XML files""")
    parser.add_argument('-p', '--path', help='The root path to XML files')
    parser.add_argument('-o', '--out', help="""Output directory. Defaults to \
            \'out\'""")
    return parser.parse_args()

def updateFunctionCounts(className, funcName, baseClasses, virtualFuncs):
    if virtualFuncs.has_key(funcName):
        virtualFuncs[funcName] += 1
    else:
        virtualFuncs[funcName] = 1

    for baseClass in baseClasses:
        if classes[baseClass].has_key(funcName):
            classes[baseClass][funcName] += 1
        else:
            classes[baseClass][funcName] = 1

    classes[className] = virtualFuncs

def parseXml(path):
    tree = ET.parse(path)
    root = tree.getroot()
    virtualfuncs = {}
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
    if classes.has_key(classname):
        virtualfuncs = classes[classname]

    for section in root.iter('sectiondef'):
        if section.attrib['kind'] == 'public-func' or \
                section.attrib['kind'] == 'protected-func':
            for memberdef in section.iter('memberdef'):
                funcName = memberdef.find('definition').text + \
                        memberdef.find('argsstring').text
                virtidx = funcName.find('=')
                if virtidx > 0:
                    funcName = funcName[0 : virtidx]
                funcName = funcName.strip()
                if memberdef.attrib['virt'] == 'virtual':
                    updateFunctionCounts(classname, funcName, baseclasses, \
                            virtualfuncs)
                elif memberdef.attrib['virt'] == 'pure-virtual':
                    updateFunctionCounts(classname, funcName, baseclasses, \
                            virtualfuncs)

    classes[classname] = virtualfuncs

def parseDir(rootDir, outname):
    for dirName, subdirList, fileList in os.walk(rootDir):
        for fileName in fileList:
            fName, ext = os.path.splitext(fileName)
            if ext and ext == '.xml':
                parseXml(os.path.join(dirName, fileName))
    print classes

def main():
    args = parse_args()
    try:
        pathname = '.'
        outname = 'out'
        if args.path:
            pathname = args.path
        if args.out:
            outname = args.out
        parseDir(pathname, outname)
    except IOError as e:
        print "I/O error({0}): {1}".format(e.errno, e.strerror)
        raise
    except:
        print "Unexpected Error: ", sys.exc_info()[0]
        raise


if __name__ == "__main__":
    main()
