# coding=utf-8
from ScriptureObjects import ScriptureText
import re
import sys
import codecs
import glob, os

# StandardizeZeroWidthCharacters 
# VERSION 0.5
# See accompanying Help file for purpose and usage.

# Phase 1: Removes ZWNJ/ZWJ found in invalid positions.
# Phase 2: Applies cluster corrections found in ClusterStatus.txt to the text.

# TODO: We need to figure out how to handle SpellingStatus.xml. These changes should apply at least to the words marked as correct spellings, 
# and also to corrections provided for incorrect spellings. If there are words that are marked as incorrect spellings, we shouldn't apply this to them,
# because they may be listed as incorrect *because* of ZW characters; Standardizing these might result in the correct spelling being treated as
# incorrect. 

# TODO: See if there's a way to apply this to the user's own Notes file, so that notes won't become detached from the word/context they are attached to when the spelling there changes. (Not essential, but would be nice.)

#__________________________________________________________________________________
# INITIALIZE CONSTANTS WITH REGEX STRINGS:

# consonants
cCodes = u'\u0915-\u0939\u0958-\u095f\u097b-\u097f' + u'\u0995-\u09b9\u09ce\u09dc-\u09df\u09f0-\u09f1' + u'\u0a15-\u0a39\u0a59-\u0a5f' + u'\u0a95-\u0ab9' + u'\u0b15-\u0b39\u0b5c-\u0b5f\u0b71' + u'\u0b95-\u0bb9' + u'\u0c15-\u0c39\u0c58\u0c59' + u'\u0c95-\u0cb9\u0cde' + u'\u0d15-\u0d39\u0d7a-\u0d7f'
c = '[' + cCodes + ']'          # c = set of all consonant characters, from each Indic script
nonCons = '[^' + cCodes + ']'   # nonCons = set of all characters that are not Indic consonants. 

# nukta
nuktaCodes = u'\u093c\u09bc\u0a3c\u0abc\u0b3c\u0bbc\u0c3c\u0cbc\u0d3c' # includes some yet-to-be adopted nuktas.
optNukta = '[' + nuktaCodes + ']*' # zero or more nukta characters

# The character class of all scripts' viramas, and the class of everything that is NOT a virama.
viramaCodes = u'\u094d\u09cd\u0a4d\u0acd\u0b4d\u0bcd\u0c4d\u0ccd\u0d4d'
virama = '[' + viramaCodes + ']'
notVirama = '([^' + viramaCodes + '])'

# zw = any number of optional ZWJ or ZWNJ
zw = u'[\u200c\u200d]*'

# cluster: This is our definition of an orthographic consonant cluster
cluster =  '(?:' + c + optNukta + virama + zw + ')+(?:' + c + optNukta + ')?'

#__________________________________________________________________________________
# INITIALIZE OTHER CONSONANTS AND VARIABLES:

infile = SettingsDirectory + Project + "\\ClusterStatus.TXT"  # The input filename

#__________________________________________________________________________________
def loadFromFile():
# Initializes the correction hash by reading the input file.
# Returns true if sucessful.

    global infile, correction

    # Read the contents of the input file into filecontents
    try:
        f = codecs.open(infile, encoding='utf-8')
        filecontents = f.read()
    except Exception, e:
        sys.stderr.write("Unable to open file: " + infile + "\nPlease create this file using the Analyze Zero-Width Characters tool.")
        return 0

    # Parse the filecontents to get cluster mappings
    try:
        fileLines = re.split(r' *[\r\n]+[\s\r\n]*', filecontents)   # Split file on newlines (eating any leading or trailing spaces)
        fields = re.split(r'\t', fileLines[0])                      # Split header line on tabs
        if fields[1] != 'Cluster' or fields[4] != "Correct":        # Make sure the headers match what we're expecting
            sys.stderr.write("Unexpected format in file: " + infile + "\nPlease re-create this file using the Analyze Zero-Width Characters tool.")
            return 0
            
        for x in range(1, len(fileLines)):                          # For each of the remaining lines,
            fields = re.split(r' *\t *', fileLines[x])              # Split line on tabs into fields.
            if len(fields) >= 5 and re.match(r'[\p{L}\p{M}\p{Cf}]+$', fields[4]):   # If there is a replacement field (consisting only of word-forming characters)
                if re.sub(u'[\u200c\u200d]', '', fields[1]) == re.sub(u'[\u200c\u200d]', '', fields[4]):    # If cluster and its replacement differ only by ZW characters
                    correction[fields[1]] = fields[4]                                                       # map the invalid cluster to its replacement.
                else:
                    sys.stderr.write("Ignoring excessive correction of " + repr(fields[1]) + " to " + repr(fields[4]) + "\n") # This tool must only make ZW changes!
            
    except Exception, e:
        sys.stderr.write("Problem reading file: " + infile + "\n")
        return 0 # Error

    return 1    # Success

#__________________________________________________________________________________
def prefCluster(matchobj):
# Provides the standardized replacement wherever a cluster pattern has been matched.
# This function is called as the replacement parameter of re.sub() in makeChanges().

    global correction

    if matchobj.group(0) in correction: # if there is a correction for this form,
        return correction[matchobj.group(0)]    # return it.
    else:
        return matchobj.group(0)    # otherwise, return the form unchanged.

#__________________________________________________________________________________
def countChanges(aStr, bStr):  
# Returns a tally of the differences between two strings, and ensures that the only differences are ZWJ/ZWNJ.
# Alerts us that we have a bug if we've actually made changes other than to ZW chars.

    global abort
    a = 0               # index as we walk through aStr
    b = 0               # index as we walk through bStr
    aLen = len(aStr)
    bLen = len(bStr)
    changes = 0         # tally of changes encountered
    zws = u'\u200c\u200d'  # the ZW chars
    while 1:            
        if a == aLen and b == bLen:  # If we've reached the end of both strings at the same time,
            return changes           #   return the number of changes tallied so far.
        if a == aLen or b == bLen:   # If we've reached the end of one string before the other,
            return changes + aLen - a + bLen - b  # return number of changes so far plus number of leftover uncompared chars.
            # TODO: Verify that the leftover chars are indeed all ZW chars, not the result of accidental deletion of the end of a string!
            
        if aStr[a] == bStr[b]:       # If both strings contain the same character at this comparison point,
            a += 1                   #     increment our index in both strings
            b += 1                   #     and continue to the next pair.
            continue
        if ((aStr[a] in zws) and (bStr[b] in zws)): # If both strings contain a ZW char, but they are different from each other,
            changes += 1                            #     add one to the changes tally,
            a += 1                                  #     increment our index in both strings,
            b += 1                                  #     and continue to the next pair.
            continue
        if aStr[a] in zws:    # If our index position in aStr contains a ZW,
            changes += 1      #    add one to the changes tally,
            a += 1            #    increment our position in aStr,
            continue          #    and continue to the next pair.
        if bStr[b] in zws:    # Likewise for bStr.
            changes += 1
            b += 1
            continue
        # If none of these were the case, the strings differ by something other than a ZW character! Check what we did wrong!! (Did user sneak an excessive correction beyond ZW changes past us?)
        sys.stderr.write("ERROR: This script was only supposed to affect ZW characters, but it was about to make other changes: " + repr(aStr[a]) + "!" + repr(bStr[b]) + "\n")
        return -1
    return 0

#__________________________________________________________________________________
def makeChanges(fileContents, bookName):
# Apply changes to the provided fileContents, returning them as a string.
# Display the number of changes made for this book (which is identified by bookName, such as LUK or TermRenderings.xml)

    global RemoveBadZWs, StandardizeClusters, notVirama, totBadChanges, totStdChanges, printedHeadingAlready
    phase1Text = fileContents
    changeBadCt = 0     # Tally how many changes are made in this book by Phase 1, removing bad ZW characters.
    changeStdCt = 0     # Tally how many changes are made in this book by Phase 2, standardizing ZW characters.
    
    # Phase 1: Remove ZW characters from places we don't think they should ever appear.
    if RemoveBadZWs=="Yes":     # If user has opted to use Phase 1:
        phase1Text = re.sub(notVirama + u'[\u200c\u200d]+', r'\1', phase1Text)  # Remove any ZW that doesn't follow virama
        phase1Text = re.sub('(' + nonCons + optNukta + virama + ')' + u'[\u200c\u200d]+', r'\1', phase1Text) # Remove ZW that follows a weird virama that follows a non-Consonant.

        if phase1Text != fileContents:  # If these Phase 1 changes have made a difference:
            changeBadCt = countChanges(fileContents, phase1Text)    # Remember the tally of changes made to this book by Phase 1
            if changeBadCt == -1:
                return fileContents         # Abort changes if invalid changes were detected.
            totBadChanges += changeBadCt                            # Add to the cumulative total across all books.
            
    # Phase 2: Change ZW characters to standardize clusters.
    phase2Text = phase1Text
    if StandardizeClusters=="Yes":  # If user has opted to use Phase 2:
        phase2Text = re.sub(cluster, prefCluster, phase2Text)   # Replace every cluster with its preferred form.
        if phase2Text != phase1Text:                            # If these Phase 2 changes have made a difference:
            changeStdCt = countChanges(phase1Text, phase2Text)  #   Remember the tally of changes made to this book by Phase 2
            if changeStdCt == -1:
                return fileContents         # Abort changes if invalid changes were detected.
            totStdChanges += changeStdCt                        #   Add to the cumulative total across all books.
    
    if changeBadCt + changeStdCt > 0:                    # If there have been changes of either kind in this book:
        if printedHeadingAlready == 0:                   #   If we haven't printed the column headings yet,
            sys.stderr.write("Invalid\tNonStd\tFile\n")  #        print them now.
            printedHeadingAlready = 1                    #   Next: Print the tally of each kind of change made in this book.
        sys.stderr.write(str(changeBadCt) + "\t" + str(changeStdCt) + "\t" + bookName + "\n")
    return phase2Text


#__________________________________________________________________________________
##### MAIN PROGRAM #####

# Initialize Paratext project(s)
scr = ScriptureText(Project)     # Open input project
if Project == OutputProject:
    scrOut = scr
else:
    scrOut = ScriptureText(OutputProject)    # Open separate output project

correction = {}             # Maps from an invalid form of a cluster to its correction
totBadChanges = 0           # tally of Phase 1 changes across all books
totStdChanges = 0           # tally of Phase 2 changes across all books
printedHeadingAlready = 0   # whether we've printed the column heading already

# Disable Phase 2 if there are any errors in loading input file.
if (StandardizeClusters=="Yes" and not loadFromFile()):
    sys.stderr.write("Skipping standardizing clusters.\n")
    StandardizeClusters = "No"

# First process the scripture books that the user has selected in the input project.
# (Normally they should select "All books".)
for reference, text in scr.allBooks(Books):  
    text2 = makeChanges(text, reference[:-4])  # Perform changes to the text. (Book ID such as LUK is extracted from reference.)
    if text2 != text or Project != OutputProject:  # If text has changed, or if output project is different from input project,
        scrOut.putText(reference, text2)       #    save changed text out to file.
scrOut.save(OutputProject)  # The books present might have changed so we need to update ssf file.

# Now process any other files specified by the user. (By default, TermRenderings.xml and BookNames.xml.)
otherFiles = re.split(r'\s*,\s*', AdditionalFiles)

## REMOVED DUE TO FILE PERMISSION PROBLEMS:
## Also apply to all Notes files.
##os.chdir(SettingsDirectory + Project)
##for file in glob.glob("Notes_*.xml"):
##    otherFiles.append(file)
    
for otherFile in otherFiles:
    xmlfile = SettingsDirectory + Project + "\\" + otherFile   # Files must be in the input project folder
    try:
        f = codecs.open(xmlfile, encoding='utf-8')  # Open file for reading
        text = f.read()                             # Read contents
        text2 = makeChanges(text, otherFile)        # Perform changes to contents
        f.close()                                   # Close file
        
    except Exception, e:
        sys.stderr.write("Unable to open file: " + xmlfile + "\n")
        continue

    xmlfile = SettingsDirectory + OutputProject + "\\" + otherFile   # Files must be in the input project folder
    if text2 != text:                               # If contents have changed:
        try:
            f = codecs.open(xmlfile, mode='w', encoding='utf-8')    # Open file for overwriting
            f.write(text2)                                          # Write updated contents
            f.close()                                               # Close file
        except Exception, e:
            sys.stderr.write("Unable to write to file: " + xmlfile + "\n")
            continue

    
# Show the user the total tally of changes
sys.stderr.write("\n\n" + str(totBadChanges) + "\ttotal invalid ZW characters removed.\n" + str(totStdChanges) + "\tclusters standardized.")

