# coding=utf-8
from ScriptureObjects import ScriptureText
import re
import sys
import codecs
import glob, os

# StandardizeZeroWidthCharacters 
# VERSION 0.3
# See accompanying Help file for purpose and usage.

## THE FOLLOWING OPTIONS HAVE BEEN REMOVED FROM THE CMS FILE FOR NOW:

# \optionName ResetAllZW
# \optionLocalizedName Reset all ZWJ and ZWNJ?
# \optionDescription Chose Yes if you wish to reset *all* ZWJ and ZWNJ characters in the text, including any that are in clusters not listed in the CLUSTERS.TXT file.
# \optionDefault No

# \optionName DefaultToResetAllZW
# \optionLocalizedName Reset to what?
# \optionDescription (Only used if you select YES above.) What is the default form for any cluster NOT listed in the STANDARD_CLUSTERS.TXT file. Valid options: NONE, ZWJ, ZWNJ
# \optionDefault ZWJ

# This tool does not currently assume that the Standard_Clusters.txt file contains a comprehensive list of every possible cluster found in the data.
# If the file contains only a partial list, non-matching clusters will not be standardized.
# This tool does not assume that there will be only one standard form of a particular cluster, though the current version of AnalyzeZeroWidthCharacters
# generates Standard_Clusters.txt with only the most common form of each cluster.

# TODO: We need to figure out how to handle SpellingStatus.xml. These changes should apply at least to the words marked as correct spellings, 
# and also to corrections provided for incorrect spellings. If there are words that are marked as incorrect spellings, we shouldn't apply this to them,
# because they may be listed as incorrect *because* of ZW characters; Standardizing these might result in the correct spelling being treated as
# incorrect. 

# TODO: See if there's a way to apply this to the user's own Notes file, so that notes won't become detached from the word/context they are attached to when the spelling there changes. (Not essential, but would be nice.)

#__________________________________________________________________________________
# INITIALIZE CONSTANTS WITH REGEX STRINGS:

# c = set of all consonant characters, from each Indic script
c = '[' + u'\u0915-\u0939\u0958-\u095f\u097b-\u097f' + u'\u0995-\u09b9\u09ce\u09dc-\u09df\u09f0-\u09f1' + u'\u0a15-\u0a39\u0a59-\u0a5f' + u'\u0a95-\u0ab9' + u'\u0b15-\u0b39\u0b5c-\u0b5f\u0b71' + u'\u0b95-\u0bb9' + u'\u0c15-\u0c39\u0c58\u0c59' + u'\u0c95-\u0cb9\u0cde' + u'\u0d15-\u0d39\u0d7a-\u0d7f' + ']'

# v = set of all vowel characters
v = '[' + u'\u0904-\u0914\u093e-\u094c' + ']'  # TO DO: Need to add other scripts, only DEV so far

# optional nukta
optNukta = u'[\u093c\u09bc\u0a3c\u0abc\u0b3c\u0bbc\u0c3c\u0cbc\u0d3c]*' # includes some yet-to-be adopted nuktas.

# The character class of all scripts' viramas, and the class of everything that is NOT a virama.
virama = u'[\u094d\u09cd\u0a4d\u0acd\u0b4d\u0bcd\u0c4d\u0ccd\u0d4d]'
notVirama = u'([^\u094d\u09cd\u0a4d\u0acd\u0b4d\u0bcd\u0c4d\u0ccd\u0d4d])'

# zw = any number of optional ZWJ or ZWNJ
zw = u'[\u200c\u200d]*'

# cluster: This is our definition of an orthographic consonant cluster
cluster =  '(?:' + c + optNukta + zw + virama + zw + ')+(?:' + c + optNukta + ')?' 

#__________________________________________________________________________________
# INITIALIZE OTHER CONSONANTS AND VARIABLES:

# The input filename
infile = SettingsDirectory + Project + "\\STANDARD_CLUSTERS.TXT"

pref = {}  # For a cluster, maps from the "base" form (without ZW chars) to the "preferred" form (with whatever ZW chars are preferred)
valid = set()  # The set of all valid clusters provided in the input file.

#__________________________________________________________________________________
def loadFromFile():
# Initializes the above two objects (pref, valid) by reading the input file.
# Returns true if sucessful.

    global infile, pref, valid
    # global ResetAllZW

    # Read the contents of the input file into filecontents
    try:
        f = codecs.open(infile, encoding='utf-8')
        filecontents = f.read()
    except Exception, e:
        sys.stderr.write("Unable to open file: " + infile + "\nPlease create this file containing the standardized forms of clusters.")
        return 0

    # Parse the filecontents to initialize the 'pref' hash and the 'valid' set.
    try:
        for cluster in re.split(r'[\s\r\n]+', filecontents):  # Split file up into clusters on linebreaks or any whitespace.
            if cluster == '':                                 # Ignore any leading or trailing whitespace in the file.
                continue
            valid.add(cluster)  # Add this cluster to the set of valid clusters
            base = re.sub(u'[\u200c\u200d]+', '', cluster) # Define base as the form of this cluster without any ZW chars.
            
            # HANDLING of ResetAllZW OPTION TEMPORARILY REMOVED
            ## If already in dict, we have a duplicate. Cancel ResetAllZW.
            # if (base in pref.keys()) and (ResetAllZW=="Yes"):
                # ResetAllZW = "No"
                # sys.stderr.write("\nWarning: ResetAllZW setting disabled due to multiple forms of same cluster specified in file: " + repr(pref[base]) + "\t" + repr(cluster) + "\n")
                
            pref[base] = cluster  # Set the preferred form of this base to be the current cluster.
                                  # If the file contains multiple forms of a given base, whichever comes last will be the preferred form.
                                  # TODO: Let's make it that whichever comes *first* will be the preferred form, so Standard_Clusters.txt
                                  # could contain one row per cluster type with additional columns for secondary acceptable-but-less-preferred
                                  # forms.
    except Exception, e:
        sys.stderr.write("Problem reading file: " + infile + "\n")
        return 0 # Error

    return 1    # Success

#__________________________________________________________________________________
def prefCluster(matchobj):
# Provides the standardized replacement wherever a cluster pattern has been matched.
# This function is called as the replacement parameter of re.sub() in makeChanges().

    global pref, valid

    # if the cluster is in the valid set, return it unchanged.
    if matchobj.group(0) in valid: 
        return matchobj.group(0)

    base = re.sub(u'[\u200c\u200d]+', '', matchobj.group(0))  # Find the base form of the cluster.
    if base in pref.keys():     # If there is a preferred form for this base, return that.
        return pref[base]
    else:
        return matchobj.group(0)  # Otherwise, return the cluster unchanged.

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
        # If none of these were the case, the strings differ by something other than a ZW character! Check what we did wrong!!
        sys.stderr.write("ERROR: This script was only supposed to affect ZW characters, but it was about to make other changes: " + repr(aStr[a]) + "!" + repr(bStr[b]) + "\n")
        sys.exit()
    return 0

#__________________________________________________________________________________
def makeChanges(fileContents, bookName):
# Apply changes to the provided fileContents, returning them as a string.
# Display the number of changes made for this book (which is identified by bookName, such as LUK or TermRenderings.xml)

    global RemoveBadZWs, StandardizeClusters, notVirama, totBadChanges, totStdChanges, printedHeadingAlready
    phase1Text = fileContents
    changeBadCt = 0     # Tally how many changes are made in this book by Phase 1, removing bad ZW characters.
    changeStdCt = 0     # Tally how many changes are made in this book by Phase 2, standardizing ZW characters.
    
    # HANDLING of ResetAllZW OPTION TEMPORARILY REMOVED
    ## For later features
    # if ResetAllZW == "Yes":
        # newText = re.sub(u'[\u200c\u200d]+', '', newText)
        # if zwOpt == "ZWJ":
            # newText = re.sub('(' + virama + ')', r'\1' + u'\u200d', newText)
        # elif zwOpt == "ZWNJ":
             # newText = re.sub('(' + virama + ')', r'\1' + u'\u200c', newText)

    # Phase 1: Remove ZW characters from places we don't think they should ever appear.
    if RemoveBadZWs=="Yes":     # If user has opted to use Phase 1:
        phase1Text = re.sub(notVirama + u'[\u200c\u200d]+', r'\1', phase1Text)  # Remove any ZW that doesn't follow virama
        phase1Text = re.sub('(' + v + virama + ')' + u'[\u200c\u200d]+', r'\1', phase1Text) # Remove ZW that follows virama that follows a vowel.
                                # TODO: Figure out which other bad ZW characters may be left in the text, and delete them too.
        if phase1Text != fileContents:  # If these Phase 1 changes have made a difference:
            changeBadCt = countChanges(fileContents, phase1Text)    # add to the tally of changes made to this book by Phase 1
            totBadChanges += changeBadCt                            # and also add to the cumulative total across all books.
            
    # Phase 2: Change ZW characters to standardize clusters.
    phase2Text = phase1Text
    if StandardizeClusters=="Yes":  # If user has opted to use Phase 2:
        phase2Text = re.sub(cluster, prefCluster, phase2Text)   # Replace every cluster with its preferred form.
        if phase2Text != phase1Text:                            # If these Phase 2 changes have made a difference:
            changeStdCt = countChanges(phase1Text, phase2Text)  #   add to the tally of changes made to this book by Phase 2
            totStdChanges += changeStdCt                        #   and also add to the cumulative total across all books.
    
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

totBadChanges = 0           # tally of Phase 1 changes across all books
totStdChanges = 0           # tally of Phase 2 changes across all books
printedHeadingAlready = 0   # whether we've printed the column heading already

# HANDLING of zwOpt OPTION TEMPORARILY REMOVED
# zwOpt = DefaultToResetAllZW.upper()

# Disable Phase 2 if there are any errors in loading input file.
if (StandardizeClusters=="Yes" and not loadFromFile()):
    sys.stderr.write("Skipping standardizing clusters.\n")
    StandardizeClusters = "No"

# First process the scripture books that the user has selected in the input project.
# (Normally they should select "All books".)
for reference, text in scr.allBooks(Books):  # TODO: Check that allBooks() here means "all selected books".
    text2 = makeChanges(text, reference[:-4])  # Perform changes to the text. (Book ID such as LUK is extracted from reference.)
    if text2 != text:                          # If text has changed, (TODO: Or if output project is different from input project?)
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

