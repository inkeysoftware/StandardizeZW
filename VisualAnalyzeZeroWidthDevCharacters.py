# coding=utf-8
import re
import sys
import codecs

# c = set of all consonant characters
c = '[' + r'\u0915-\u0939\u0958-\u095f\u097b-\u097f' + r'\u0995-\u09b9\u09ce\u09dc-\u09df\u09f0-\u09f1' + r'\u0a15-\u0a39\u0a59-\u0a5f' + r'\u0a95-\u0ab9' + r'\u0b15-\u0b39\u0b5c-\u0b5f\u0b71' + r'\u0b95-\u0bb9' + r'\u0c15-\u0c39\u0c58\u0c59' + r'\u0c95-\u0cb9\u0cde' + r'\u0d15-\u0d39\u0d7a-\u0d7f' + ']'

# optional nukta
optNukta = r'[\u093c\u09bc\u0a3c\u0abc\u0b3c\u0bbc\u0c3c\u0cbc\u0d3c]*' # includes some yet-to-be adopted nuktas.

# virama
virama = r'[\u094d\u09cd\u0a4d\u0acd\u0b4d\u0bcd\u0c4d\u0ccd\u0d4d]'

# zw
zw = r'[\u200c\u200d]*'

# cluster
cluster =  '(?:' + c + optNukta + zw + virama + zw + ')+(?:' + c + optNukta + ')?'

hoh = {}

# Return true if input is valid
def validInput():
    global Parameter1, Parameter2, hoh, bases, thisVirama, f

    if len(Parameter1) == 0:
        sys.stderr.write("You must enter the full path and filename of the exported wordlist file to read.\n")
        return 0

    if len(Parameter2) == 0:
        sys.stderr.write("You must enter the full path and filename of the output file to create/overwrite.\n")
        return 0

    try:
        f = codecs.open(Parameter1, encoding='utf-8')
        filecontents = f.read()
    except Exception, e:
        sys.stderr.write("Unable to read file: " + Parameter1 + "\n")
        return 0

    try:
        f = codecs.open(Parameter2, mode='w', encoding='utf-8')
        f.write(u'\uFEFF\r\n') # BOM
    except Exception, e:
        sys.stderr.write("Unable to write to file: " + Parameters + "\n")
        return 0

    try:
        for line in re.split(r'[\r\n]+', filecontents):
            if line == '':
                continue
            matchobj = re.search(r' word="(\S+)" count="(\d+)"', line)
            if matchobj:
                wd = matchobj.group(1)
                ct = int(matchobj.group(2))
                clusters = re.findall(cluster, wd)
                for cl in clusters:
                    base = re.sub(zw, '', cl)
                    if base in hoh:
                        if cl in hoh[base]:
                            hoh[base][cl] += ct
                        else:
                            hoh[base][cl] = ct
                    else:
                        hoh[base] = {cl : ct}

    except Exception, e:
        sys.stderr.write("Problem reading file: " + Parameter1 + "\n")
        return 0
    
    return 1    

outputlines = {} # base -> lines of text to output
priority = {}    # base -> number of changes
space = ""
import tempfile
tfName = tempfile.mktemp()
from subprocess import check_output
fontFile = '"' + SettingsDirectory + 'cms\\AnnapurnaSIL-Regular.ttf' + '"'

def getPriority(base):
    global priority
    return priority[base]

def getRawGlyphs(str):
    global SettingsDirectory, fontFile
    try:
        tf = codecs.open(tfName, mode='w', encoding='utf-8')
#        tf.write(u'\uFEFF\r\n') # BOM
        tf.write(str) 
        tf.close()
    except Exception, e:
        sys.stderr.write("Unable to write to temp file: " + tfName + "\n")
        return 0
    outstr = check_output('"' + SettingsDirectory + 'cms\\harfbuzz\\hb-shape.exe" --text-file ' + tfName + ' --no-positions --no-clusters --font-file ' + fontFile, shell=True)
    return re.sub('[\[\]\r\n\s]', '', outstr)

space = getRawGlyphs(" ")
def getGlyphs(str):
    global space
    return re.sub('\\|' + space, '', getRawGlyphs(str))

def clusType(clus):
    typ = re.sub(virama + u'\u200C', 'N', clus)
    typ = re.sub(virama + u'\u200D', 'J', typ)
    typ = re.sub(virama, 'S', typ)
    typ = re.sub(u'[\u200D\u200C]', 'x', typ)
    typ = re.sub(r'[^NJSx]', '', typ)
    return typ

clusCt = 0

if validInput():
    # f.write(space + '\r\n')
    # f.write(getGlyphs(u'\u091F\u094D\u091F') + '\r\n')
    # f.write(getGlyphs(u'\u091F\u094D\u200D\u091F') + '\r\n')
    # f.write(getGlyphs(u'\u091F\u094D\u200C\u091F') + '\r\n')
    # f.write("Root\tS\tS Ct\tJ\tJ Ct\tN\tN Ct\tOther\tType\tCt\r\n")
    for base in hoh.iterkeys():
        clusCt += 1
        root = re.sub(virama, '', base)
        cform = re.sub('(' + virama + ')', r'\1' + u'\u200c', base)
        dform = re.sub('(' + virama + ')', r'\1' + u'\u200d', base)
        glyphs = {}
        priority = 0
        clusterlines = root + '\r\n'
        for cl in sorted(hoh[base].iterkeys()):
            g = getGlyphs(cl)
            if g in glyphs:
                glyphs[g].append((hoh[base][cl], cl))
            else:
                glyphs[g] = [(hoh[base][cl], cl)]
        for g in sorted(glyphs.iterkeys(), reverse=True, key=lambda x: len(glyphs[x])):
            if len(glyphs[g]) > 1:
                a = sorted(glyphs[g], reverse=True)
                main = a[0]
                a = a[1:]
                clusterlines += '\t' + g + "\t" + main[1] + '\t' + clusType(main[1]) + '\t' + str(main[0])
                for secondary in a:
                    clusterlines += "\t" + secondary[1] + '\t' + clusType(secondary[1]) + '\t' + str(secondary[0])
                    priority += secondary[0]
                clusterlines += '\r\n'
            else:
                if priority == 0:  # For bases that have no visually-identical sets, set priority simply by total count
                    priority -= 100000
                if priority < 0:
                    priority += glyphs[g][0][0]
                clusterlines += '\t' + g + "\t\t\t\t" + glyphs[g][0][1] + '\t' + clusType(glyphs[g][0][1]) + '\t' + str(glyphs[g][0][0]) + '\r\n'
        outputlines[base] = (priority, clusterlines)

    # for base in sorted(hoh.iterkeys()):
        # clusCt += 1
        # root = re.sub(virama, '', base)
        # cform = re.sub('(' + virama + ')', r'\1' + u'\u200c', base)
        # dform = re.sub('(' + virama + ')', r'\1' + u'\u200d', base)
        # f.write(root + "\t" + base + "\t")
        # if base in hoh[base]:
            # f.write(str(hoh[base][base]))
            # del hoh[base][base]
        # f.write("\t" + dform + "\t")
        # if dform in hoh[base]:
            # f.write(str(hoh[base][dform]))
            # del hoh[base][dform]
        # f.write("\t" + cform + "\t")
        # if cform in hoh[base]:
            # f.write(str(hoh[base][cform]))
            # del hoh[base][cform]
        # for cl in sorted(hoh[base].iterkeys()):
            # typ = re.sub(virama + u'\u200C', 'N', cl)
            # typ = re.sub(virama + u'\u200D', 'J', typ)
            # typ = re.sub(virama, 'S', typ)
            # typ = re.sub(u'[\u200D\u200C]', 'x', typ)
            # typ = re.sub(r'[^NJSx]', '', typ)
            # f.write("\t" + cl + "\t" + typ + "\t" + str(hoh[base][cl]))
        # f.write("\r\n")
    for base in sorted(outputlines.iterkeys(), reverse=True, key=lambda x: outputlines[x][0]):
        # f.write('<' + str(outputlines[base][0]) + '>\t' + outputlines[base][1])
        f.write(outputlines[base][1])

sys.stderr.write(str(clusCt) + " clusters written to " + Parameter2 + "\n\nPaste the contents of this file into a spreadsheet for analysis.\nFrom this you can create a preferred_clusters.txt file to be used with the <Standardize Zero-Width Characters> tool,\nand an invalid_clusters.txt file to be used with the <Generate Zero-Width Spelling Rules> tool.")
