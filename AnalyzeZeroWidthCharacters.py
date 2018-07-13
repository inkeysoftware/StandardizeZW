# coding=utf-8
from ScriptureObjects import ScriptureText
from CommonZWC import *
import re
import sys
import codecs
import os
import shutil
import difflib

#__________________________________________________________________________________
# INITIALIZE OTHER CONSONANTS AND VARIABLES:

clusFilename = SettingsDirectory + Project + "\\ClusterCorrections.TXT"    # New output to support multiple valid forms
clusallFilename = SettingsDirectory + Project + "\\AllClusterCorrections.TXT"    # New output to support multiple valid forms

#__________________________________________________________________________________
def weightedCt(cl, base):
# Add a fraction (depending on form) to frequency tally as a tie-breaker.
    if cl == base:
        return 1.2      # 2nd highest priority for STACKED form
        
    dform = re.sub('(' + virama + ')', r'\1' + u'\u200d', base)
    if cl == dform:
        return 1.3      # Highest priority given for JOINED form
    
    cform = re.sub('(' + virama + ')', r'\1' + u'\u200c', base)
    if cl == cform:
        return 1.1      # 3rd priority for NON-JOINED form
        
    return 1.0          # Lowest priority for mixed form (may occur with 2 or more viramas)
    
#__________________________________________________________________________________
def initialize():
# Open file for output, and read all books to tally the frequency of each form of each cons combination.
# Return true if successful.

    global clusFilename, clusallFilename, invalidReport, formTally, bases, thisVirama, f, clusFile, clusallFile, notVirama, v, virama, listWords, cl

    try:
        clusFile = codecs.open(clusFilename, mode='w', encoding='utf-8')
        clusFile.write(u'\uFEFFRoot\tCluster\tClusterShow\tCount\tCorrect\tCorrectShow\tExamples\r\n') # BOM and column headings
        
    except Exception, e:
        sys.stderr.write("Unable to write to file: " + clusFilename + "\n")
        return 0
    
          
    try:
        scr = ScriptureText(Project)     # Open input project
         
        listWords = {}
        
                
        for reference, text in scr.allBooks(Books):  
        
            # Ignore any invalid ZW characters. THE REGEXES IN THIS CODE SHOULD MATCH WHAT'S IN THE STANDARDIZE SCRIPT!
            text2 = ignoreanyInvalidzw(text)
                                 
            # Keep track of invalid ZW characters removed, so we can report on that at the end.
            invalidCt = countChanges(text, text2)
            if (invalidCt > 0):
                invalidReport += "\t" + reference[:-4] + ":\t" + str(invalidCt) + "\n"
                        
            # Find the examples and the clusters
            for example in re.findall('[\p{L}\p{M}\p{Cf}]+', text2):
                for cl in re.findall(cluster, example):
                    if cl not in listWords:
                        listWords[cl] = [example]
                    else:
                        # if example not in list values - append unique values
                        if example not in listWords[cl]:
                            listWords[cl].append(example) 
                
                    # Count occurrences of each form of each cluster
                    base = re.sub(zw, '', cl)       # The base form is the simple stacked form
                   
                    if base in formTally:
                        if cl in formTally[base]:
                            formTally[base][cl] += 1
                        else:
                            formTally[base][cl] = weightedCt(cl, base)
                    else:
                        formTally[base] = {cl : weightedCt(cl, base)}
                        
    except Exception, e:
        sys.stderr.write("Error looping through Scripture books.")
        return 0
    
    return 1    

def examples(bCluster):
    global listWords      
    global ExampleCount

    s = sorted(listWords[bCluster])
    ls = len(s)
    if ExampleCount >= ls:  # If they want more examples than we have, give all we have.
        return ', '.join(s)
        
    ExampleCount = max(ExampleCount,2)
    
    # Create a list containing the examples that were first, last, and equally-spaced between first and last.
    e = s[0:1]  # First item
    for i in range(1,ExampleCount):
        e.append(s[int(0.5 + (ls-1.0)/(ExampleCount-1.0) * i)]) # ExampleCount-1 additional items
    return ', '.join(e)

def buildDict():

    global  clusallFilename, clusallFile, clDict
    
    fileread = 0
    try:
        if os.path.isfile(clusallFilename):
            clusallFile = codecs.open(clusallFilename, encoding='utf-8')
            allfilecontents = clusallFile.read()
            fileread = 1
        
    except Exception, e:
        sys.stderr.write("Unable to read or write to file: " + clusallFilename + "\n")
        return 0
    
    try:    
        if (fileread):   
            
            allfileLines = re.split(r' *[\r\n]+[\s\r\n]*', allfilecontents)   # Split file on newlines (eating any leading or trailing spaces)
            allfields = re.split(r'\t', allfileLines[0])                      # Split header line on tabs
            count = 0 
            
            for x in range(1, len(allfileLines)):                          # For each of the remaining lines,
                allfields = re.split(r' *\t *', allfileLines[x])              # Split line on tabs into fields.
                if len(allfields)> 3:
                    base = allfields[0]
                    cl = allfields[1]
                    
                    if base not in clDict:
                        clDict[base] = {}
                           
                    clDict[base][cl] = [allfields[4], allfields[6]]
                                
            clusallFile.close()

    except Exception, e:
        sys.stderr.write("Unable to process all cluster file")
        return 0 # Error
    
    
    return fileread

##### MAIN PROGRAM #####

formTally = {} # A hash array of hash arrays to tally the frequency count for each form of each combination of consonants
clusCt = 0
invalidReport = ""
clDict = {}

if initialize():
    # Build allclusters dictionary from allclustercorrections file
    buildDict()
    
    
    for base in sorted(formTally.iterkeys()):
        
        root = re.sub(virama, '', base)
        sortedForms = sorted(formTally[base].iterkeys(), key=lambda a: formTally[base][a], reverse=True) # Sort from most frequent to least
        
        if ExcludeSingle == "No" or len(sortedForms) > 1:
            
            # First write out best form
            bestForm = sortedForms[0]
            bestFormShow = showAll(bestForm)
                       
            if base in clDict and bestForm in clDict[base]:
                clusFile.write(root + "\t" + bestForm + "\t" + showAll(bestForm) + "\t" + str(int(formTally[base][bestForm])) + "\t" + clDict[base][bestForm][0] + "\t" + showAll(clDict[base][bestForm][0]) + "\t" + (examples(bestForm) if formTally[base][bestForm] else clDict[base][bestForm][1])) 
                del clDict[base][bestForm]
            else:   
                clusFile.write(root + "\t" + bestForm + "\t" + bestFormShow + "\t" + str(int(formTally[base][bestForm])) + "\t" + "\t" + "\t" + examples(bestForm)) 
            
            clusFile.write("\r\n")
                
            clusCt += 1
            
            # Now write out all remaining forms from sortedForms found in text
            for x in range(1, len(sortedForms)):
                thisForm = sortedForms[x]
                if base in clDict and thisForm in clDict[base]:
                    clusFile.write(root + "\t" + thisForm + "\t" + showAll(thisForm) + "\t" + str(int(formTally[base][thisForm])) + "\t" + clDict[base][thisForm][0] + "\t" + showAll(clDict[base][thisForm][0]) + "\t" + (examples(thisForm) if formTally[base][thisForm] else clDict[base][thisForm][1])) 
                    del clDict[base][thisForm]
                    
                else:     
                    clusFile.write(root + "\t" + thisForm + "\t" + showAll(thisForm) + "\t" + str(int(formTally[base][thisForm])) + "\t" + bestForm + "\t" + bestFormShow + "\t" + examples(thisForm)) 
                clusFile.write("\r\n") 
                clusCt += 1
                
            # Finally, write out any forms that existed in AllCorrections but which no longer exist in the text
            if base in clDict:
                for thisForm in clDict[base]:
                    clusFile.write(root + "\t" + thisForm + "\t" + showAll(thisForm) + "\t" + "0" + "\t" + clDict[base][thisForm][0] + "\t" + showAll(clDict[base][thisForm][0]) + "\t" + clDict[base][thisForm][1])
                   
            clusFile.write("\r\n")
        
# Report on number of clusters written
if (clusCt>0):
    sys.stderr.write(str(clusCt) + " forms of " + str(len(formTally)) + " consonant combinations written to " + clusFilename + "\n")
    
# Report on invalid ZW characters, if found
if (len(invalidReport) > 0):
    sys.stderr.write(" \nAlso note: Using the STANDARDIZE tool to remove invalid ZW characters will fix this many issues:\n" + invalidReport + "\n")
    
clusFile.close()


# Copy the XLSX file to the project folder, if available and not already there.
try:
    xl1 = SettingsDirectory + "\\cms\\FormattedClusterStatus.xlsx" 
    xl2 = SettingsDirectory + Project + "\\FormattedClusterStatus.xlsx" 
    if os.path.isfile(xl1) and not os.path.isfile(xl2):
        shutil.copyfile(xl1, xl2)
except Exception, e:
    sys.stderr.write("Did not copy xlsx file\n")