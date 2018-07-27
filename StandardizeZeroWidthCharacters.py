# coding=utf-8
from ScriptureObjects import ScriptureText
from CommonZWC import *
import re
import sys
import codecs
import glob, os
import shutil

# StandardizeZeroWidthCharacters 
# VERSION 0.7
# See accompanying Help file for purpose and usage.

# Phase 1: Removes ZWNJ/ZWJ found in invalid positions.
# Phase 2: Applies cluster corrections found in ClusterCorrections.txt to the text.

# TODO: We need to figure out how to handle SpellingStatus.xml. These changes should apply at least to the words marked as correct spellings, 
# and also to corrections provided for incorrect spellings. If there are words that are marked as incorrect spellings, we shouldn't apply this to them,
# because they may be listed as incorrect *because* of ZW characters; Standardizing these might result in the correct spelling being treated as
# incorrect. 

# TODO: See if there's a way to apply this to the user's own Notes file, so that notes won't become detached from the word/context they are attached to when the spelling there changes. (Not essential, but would be nice.)

#__________________________________________________________________________________
# INITIALIZE OTHER CONSONANTS AND VARIABLES:

infile = SettingsDirectory + Project + "\\ClusterCorrections.TXT"  # The input filename

allclinfile = SettingsDirectory + Project + "\\AllClusterCorrections.TXT"    # New input to store previous changes

#__________________________________________________________________________________
def loadFromFile():
# Initializes the correction hash by reading the input file.
# Returns true if sucessful.

    global infile, allclinfile, correction, allCluster, alldata, clusallFile, examplemap, dict_items, clDict
    
    # Read contents of AllClusterCorrections into Corrections and write into clDict
    buildDict(allclinfile)
     
    # Read the contents of the input file into filecontents
    buildDict(infile)
    
    return 1    
    
    
def buildDict(filename):

    global  clusallFile, clDict, correction
    
    fileread = 0
    try:
        if os.path.isfile(filename):
            clusallFile = codecs.open(filename, encoding='utf-8')
            allfilecontents = clusallFile.read()
            fileread = 1
        
    except Exception, e:
        sys.stderr.write("Unable to read or write to file: " + filename + "\n")
        return 0
    
    try:   
       
        if (fileread):   
            
            allfileLines = re.split(r' *[\r\n]+[\s\r\n]*', allfilecontents)   # Split file on newlines (eating any leading or trailing spaces)
            allfields = re.split(r'\t', allfileLines[0])                      # Split header line on tabs
            
            if allfields[1] != 'Cluster' or allfields[4] != "Correct":        # Make sure the headers match what we're expecting
                sys.stderr.write("Unexpected format in file: " + filename + "\nPlease re-create this file using the Analyze Zero-Width Characters tool.")
                return 0
            
            for x in range(1, len(allfileLines)):                             # For each of the remaining lines,
                allfields = re.split(r' *\t *', allfileLines[x])              # Split line on tabs into fields.
                
                if len(allfields)>=3:
                    base = allfields[0]
                    cl = allfields[1]
                    
                    if base not in clDict:
                        clDict[base] = {}
                           
                    clDict[base][cl] = allfileLines[x]
                
                    if len(allfields) >= 5 and re.match(r'[\p{L}\p{M}\p{Cf}]+$', allfields[4]):   # If there is a replacement field (consisting only of word-forming characters)
                        if re.sub(u'[\u200c\u200d]', '', allfields[1]) == re.sub(u'[\u200c\u200d]', '', allfields[4]):    # If cluster and its replacement differ only by ZW characters
                            correction[allfields[1]] = allfields[4]                                                       # map the invalid cluster to its replacement.
                        else:
                            sys.stderr.write("Ignoring excessive correction of " + repr(allfields[1]) + " to " + repr(allfields[4]) + "\n") # This tool must only make ZW changes!
            
            clusallFile.close()

    except Exception, e:
        sys.stderr.write("Unable to process cluster file" + filename + "\n")
        return 0 # Error
    
    
    return fileread
    

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
def makeChanges(fileContents, bookName):
# Apply changes to the provided fileContents, returning them as a string.
# Display the number of changes made for this book (which is identified by bookName, such as LUK or TermRenderings.xml)

    global RemoveBadZWs, StandardizeClusters, notVirama, totBadChanges, totStdChanges, printedHeadingAlready
    phase1Text = fileContents
    changeBadCt = 0     # Tally how many changes are made in this book by Phase 1, removing bad ZW characters.
    changeStdCt = 0     # Tally how many changes are made in this book by Phase 2, standardizing ZW characters.
    
    # Phase 1: Remove ZW characters from places we don't think they should ever appear.
    if RemoveBadZWs=="Yes":     # If user has opted to use Phase 1:
        phase1Text = ignoreanyInvalidzw(phase1Text)
        #phase1Text = re.sub(notVirama + u'[\u200c\u200d]+', r'\1', phase1Text)  # Remove any ZW that doesn't follow virama
        #phase1Text = re.sub('(' + nonCons + optNukta + virama + ')' + u'[\u200c\u200d]+', r'\1', phase1Text) # Remove ZW that follows a weird virama that follows a non-Consonant.

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

   
# Write into the Allclustercorrections file
def writetoFile():

    global clusallFile, clDict, allCluster, allclinfile
  
    try:
        clusallFile = codecs.open(allclinfile, mode='w', encoding='utf-8')
        clusallFile.write(u'\uFEFFRoot\tCluster\tClusterShow\tCount\tCorrect\tCorrectShow\tExamples\r\n') # BOM and column headings
                   
    except Exception, e:
        sys.stderr.write("Unable to write to file:" + allclinfile + "\n")
        return 0
     
    try: 
        for root in sorted(clDict.iterkeys()):
            for eachcluster in sorted(clDict[root]):
                if root in clDict and eachcluster in clDict[root]:
                    cols = re.split(r'\t', clDict[root][eachcluster])
                    
                    clusallFile.write(cols[0] + "\t" + cols[1] + "\t" + cols[2] + "\t" + cols[3] + "\t" + cols[4] + "\t" + showAll(cols[4]) + "\t" + cols[6])
                    clusallFile.write("\r\n")
                    
            clusallFile.write("\r\n")
        clusallFile.close()   
    
    except Exception, e:
        sys.stderr.write(allclinfile)
        return 0 # Error
        
    
        
      
    return 1
    
    
#__________________________________________________________________________________
##### MAIN PROGRAM #####

# Initialize Paratext project(s)
scr = ScriptureText(Project)     # Open input project
if Project == OutputProject:
    scrOut = scr
else:
    scrOut = ScriptureText(OutputProject)    # Open separate output project

correction = {}             # Maps from an invalid form of a cluster to its correction
allCluster = {}             # store all valid and invalid cluster combinations
clDict = {}
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

# Create or append AllClusterCorrections file
if not writetoFile():
    sys.stderr.write("Unable to create AllClusterCorrections file.\n")

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

#clusallFile.close()
   
# Show the user the total tally of changes
sys.stderr.write("\n\n" + str(totBadChanges) + "\ttotal invalid ZW characters removed.\n" + str(totStdChanges) + "\tclusters standardized.")

