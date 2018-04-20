# coding=utf-8
from ScriptureObjects import ScriptureText
import re
import sys
import codecs
import glob, os

# VERSION 0.3

## OPTIONS REMOVED FROM THE CMS FILE FOR NOW:

# \optionName ResetAllZW
# \optionLocalizedName Reset all ZWJ and ZWNJ?
# \optionDescription Chose Yes if you wish to reset *all* ZWJ and ZWNJ characters in the text, including any that are in clusters not listed in the CLUSTERS.TXT file.
# \optionDefault No

# \optionName DefaultToResetAllZW
# \optionLocalizedName Reset to what?
# \optionDescription (Only used if you select YES above.) What is the default form for any cluster NOT listed in the STANDARD_CLUSTERS.TXT file. Valid options: NONE, ZWJ, ZWNJ
# \optionDefault ZWJ


# c = set of all consonant characters, from each Indic script
c = '[' + u'\u0915-\u0939\u0958-\u095f\u097b-\u097f' + u'\u0995-\u09b9\u09ce\u09dc-\u09df\u09f0-\u09f1' + u'\u0a15-\u0a39\u0a59-\u0a5f' + u'\u0a95-\u0ab9' + u'\u0b15-\u0b39\u0b5c-\u0b5f\u0b71' + u'\u0b95-\u0bb9' + u'u0c15-\u0c39\u0c58\u0c59' + u'\u0c95-\u0cb9\u0cde' + u'u0d15-\u0d39\u0d7a-\u0d7f' + ']'

# v = set of all vowel characters
v = '[' + u'\u0904-\u0914\u093e-\u094c' + ']'  # TO DO: Need to add other scripts, only DEV so far

# optional nukta
optNukta = u'[\u093c\u09bc\u0a3c\u0abc\u0b3c\u0bbc\u0c3c\u0cbc\u0d3c]*' # includes some yet-to-be adopted nuktas.

# virama
virama = u'[\u094d\u09cd\u0a4d\u0acd\u0b4d\u0bcd\u0c4d\u0ccd\u0d4d]'
notVirama = u'([^\u094d\u09cd\u0a4d\u0acd\u0b4d\u0bcd\u0c4d\u0ccd\u0d4d])'

# zw
zw = u'[\u200c\u200d]*'

# cluster
cluster =  '(?:' + c + optNukta + zw + virama + zw + ')+(?:' + c + optNukta + ')?' 

infile = SettingsDirectory + Project + "\\STANDARD_CLUSTERS.TXT"

pref = {}  # For a cluster, maps from the "base" form (without ZW chars) to the "preferred" form (with whatever ZW chars are preferred)
valid = set()  # The set of all valid clusters provided in the input file

# Initialize the above two objects (pref, valid) by reading the input file.
# Return true if sucessful.
def loadFromFile():
    global infile, pref, valid
    # global ResetAllZW

    try:
        f = codecs.open(infile, encoding='utf-8')
        filecontents = f.read()
    except Exception, e:
        sys.stderr.write("Unable to open file: " + infile + "\nPlease create this file containing the standardized forms of clusters.")
        return 0


    try:
        for line in re.split(r'[\s\r\n]+', filecontents):
            if line == '':
                continue
            valid.add(line)
            base = re.sub(u'[\u200c\u200d]+', '', line)
            # if already in dict, we have a duplicate. Cancel ResetAllZW.
            if (base in pref.keys()) and (ResetAllZW=="Yes"):
                ResetAllZW = "No"
                sys.stderr.write("\nWarning: ResetAllZW setting disabled due to multiple forms of same cluster specified in file: " + repr(pref[base]) + "\t" + repr(line) + "\n")
            pref[base] = line
    except Exception, e:
        sys.stderr.write("Problem reading file: " + infile + "\n")
        return 0

    return 1    

# Function to provide the replacement wherever a cluster pattern is matched
def prefCluster(matchobj):
    global pref, valid

    if matchobj.group(0) in valid: # if the cluster is in the valid set, return it unchanged.
        # sys.stderr.write("#")
        return matchobj.group(0)

    base = re.sub(u'[\u200c\u200d]+', '', matchobj.group(0))  # Find the base form of the cluster.
    if base in pref.keys():     # If there is a preferred form for this base, return that.
        # sys.stderr.write("!")
        return pref[base]
    else:
        # sys.stderr.write(">")
        return matchobj.group(0)  # Otherwise, return the cluster unchanged.

# Returns a tally of the differences between two strings, assuming the only differences are ZWJ/ZWNJ
def countChanges(aStr, bStr):  
    global abort
    a = 0
    b = 0
    aLen = len(aStr)
    bLen = len(bStr)
    changes = 0
    zws = u'\u200c\u200d'
    while 1:
        if a == aLen and b == bLen:  # reached the end of both strings at the same time?
            return changes
        if a == aLen or b == bLen:  # reached the end of one string before the other?
            return changes + aLen - a + bLen - b 
        if aStr[a] == bStr[b]:    # character not changed
            a += 1
            b += 1
            continue
        if ((aStr[a] in zws) and (bStr[b] in zws)): # two different ZWs
            changes += 1
            a += 1
            b += 1
            continue
        if aStr[a] in zws:    # aStr contains ZW
            changes += 1
            a += 1
            continue
        if bStr[b] in zws:    # bStr contains ZW
            changes += 1
            b += 1
            continue
        sys.stderr.write("ERROR: This script was only supposed to affect ZW characters, but it was about to make other changes: " + repr(aStr[a]) + "!" + repr(bStr[b]) + "\n")
        sys.exit()
#        sys.stdin.read(1)
#        return 0
    return 0

# Apply changes to the provided fileContents, returning them as a string
def makeChanges(fileContents, bookName):
    global RemoveBadZWs, StandardizeClusters, notVirama, totBadChanges, totStdChanges, anyChanges
    phase1Text = fileContents
    changeBadCt = 0
    changeStdCt = 0
    ## For later features
    # if ResetAllZW == "Yes":
        # newText = re.sub(u'[\u200c\u200d]+', '', newText)
        # if zwOpt == "ZWJ":
            # newText = re.sub('(' + virama + ')', r'\1' + u'\u200d', newText)
        # elif zwOpt == "ZWNJ":
             # newText = re.sub('(' + virama + ')', r'\1' + u'\u200c', newText)
    if RemoveBadZWs=="Yes":
        phase1Text = re.sub(notVirama + u'[\u200c\u200d]+', r'\1', phase1Text)  # remove ZW that doesn't follow virama
        phase1Text = re.sub('(' + v + virama + ')' + u'[\u200c\u200d]+', r'\1', phase1Text) # remove ZW that follows virama that follows a vowel
        if phase1Text != fileContents:
            changeBadCt = countChanges(fileContents, phase1Text)
            totBadChanges += changeBadCt
    phase2Text = phase1Text
    if StandardizeClusters=="Yes":
        phase2Text = re.sub(cluster, prefCluster, phase2Text)
        if phase2Text != phase1Text:
            changeStdCt = countChanges(phase1Text, phase2Text)
            totStdChanges += changeStdCt
    if changeBadCt + changeStdCt > 0:
        if anyChanges == 0:
            sys.stderr.write("Invalid\tNonStd\tFile\n")
            anyChanges = 1
        sys.stderr.write(str(changeBadCt) + "\t" + str(changeStdCt) + "\t" + bookName + "\n")
    return phase2Text


scr = ScriptureText(Project)     # open input project
if Project == OutputProject:
    scrOut = scr
else:
    scrOut = ScriptureText(OutputProject)    # open output project


totBadChanges = 0
totStdChanges = 0
anyChanges = 0

## For later feature
# zwOpt = DefaultToResetAllZW.upper()

if (StandardizeClusters=="No" or loadFromFile()):

    for reference, text in scr.allBooks(Books):  # process all books
        text2 = makeChanges(text, reference[:-4])
        if text2 != text:
            scrOut.putText(reference, text2)

# The books present might have changed so we need to update ssf file.
scrOut.save(OutputProject)

otherFiles = re.split(r'\s*,\s*', AdditionalFiles)

##os.chdir(SettingsDirectory + Project)
##for file in glob.glob("Notes_*.xml"):
##    otherFiles.append(file)
    
for otherFile in otherFiles:
    xmlfile = SettingsDirectory + Project + "\\" + otherFile
    try:
        f = codecs.open(xmlfile, encoding='utf-8')
        text = f.read()
        text2 = makeChanges(text, otherFile)
        f.close()
        
    except Exception, e:
        sys.stderr.write("Unable to open file: " + xmlfile + "\n")
        continue

    if text2 != text:
        try:
            f = codecs.open(xmlfile, mode='w', encoding='utf-8')
            f.write(text2)
            f.close()
        except Exception, e:
            sys.stderr.write("Unable to write to file: " + xmlfile + "\n")
            continue

    
# Give the user a chance to see what has changed
sys.stderr.write("\n\n" + str(totBadChanges) + "\ttotal invalid ZW characters removed.\n" + str(totStdChanges) + "\tclusters standardized.")
# sys.stdin.read(1)
