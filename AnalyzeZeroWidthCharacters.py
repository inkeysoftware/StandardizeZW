# coding=utf-8
from ScriptureObjects import ScriptureText
from CommonZWC import *
import re
import sys
import codecs
import os
import shutil
import difflib

# AnalyzeZeroWidthCharacters
# By Dan Em & Anita B
# Version: 0.7

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

    global clusFilename, clusallFilename, invalidReport, formTally, thisVirama, f, clusFile, clusallFile, notVirama, v, virama, listWords, cl, clDict

    # Prepare the ClusterCorrections file for writing
    try:
        clusFile = codecs.open(clusFilename, mode='w', encoding='utf-8')
        clusFile.write(u'\uFEFFRoot\tCluster\tClusterShow\tCount\tCorrect\tCorrectShow\tExamples\r\n') # BOM and column headings
        
    except Exception, e:
        sys.stderr.write("Unable to write to file: " + clusFilename + "\n")
        return 0
          
    try:
        
        scr = ScriptureText(Project)     # Open input project
         
        listWords = {}
        
        # Loop through scripture books 
        for reference, text in scr.allBooks(Books):  
        
            # Ignore any invalid ZW characters. 
            text2 = ignoreanyInvalidzw(text)

                                 
            # Keep track of invalid ZW characters needing removed, so we can report on that at the end.
            invalidCt = countChanges(text, text2)
            if (invalidCt > 0):
                invalidReport += "\t" + reference[:-4] + ":\t" + str(invalidCt) + "\n"
                        
            # Find the examples and the clusters
            for example in re.findall('[\p{L}\p{M}\p{Cf}]+', text2):    # for every word in the text
                for cl in re.findall(cluster, example):                 #    for each cluster in that word, remember this word as an example of it.
                    if cl not in listWords:                             
                        listWords[cl] = [example]
                    else:
                        # if example not in list values - append unique values
                        if example not in listWords[cl]:
                            listWords[cl].append(example) 
                
                    # Count occurrences of each form of each cluster
                    base = re.sub(zw, '', cl)       # The base form is a simple stack form
                    
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
    
    # Read AllClusterCorrections file (if it exists) into clDict.
    # For each cluster form of each base combination, clDict remembers the Correct and Examples values, and also the new count if it exists in formTally.
    # Also, give formTally a zero count for any form found in AllClusterCorrections that was not found in the current text.
    try:
        if os.path.isfile(clusallFilename):
            clusallFile = codecs.open(clusallFilename, encoding='utf-8')
            allfilecontents = clusallFile.read()
            allfileLines = re.split(r' *[\r\n]+[\s\r\n]*', allfilecontents)   # Split file on newlines (eating any leading or trailing spaces)
            allfields = re.split(r'\t', allfileLines[0])                      # Split header line on tabs
            count = 0 
            
            for x in range(1, len(allfileLines)):                          # For each of the remaining lines,
                allfields = re.split(r' *\t *', allfileLines[x])              # Split line on tabs into fields.
                if len(allfields)> 3:
                    cl = allfields[1]
                    base = re.sub(zw, '', cl)
                    if base not in clDict:
                        clDict[base] = {}
                    if base in formTally and cl in formTally[base]:     # If this form exists in the current text
                        count = formTally[base][cl]                     #   set count and examples according to what is found in current text
                        examples = getExamples(cl)
                    else:
                        count = 0                                       # Otherwise, set count to zero, and retain former examples.
                        examples = allfields[6]
                        if base in formTally:                           # and give formTally a zero count for this form.
                            formTally[base][cl] = 0
                        else:
                            formTally[base] = {cl : 0}                            
                    clDict[base][cl] = [allfields[4], examples, count]     # = [Correct, Examples, Count]
                              
            clusallFile.close()

    except Exception, e:
        sys.stderr.write("Error processing AllClusterCorrections file: " + clusallFilename + "\n")
        return 0 # Error

    return 1
    
#__________________________________________________________________________________
def getExamples(bCluster):
# Return a list of example words of a specified cluster form.
# This list should contain at most ExampleCount words. (ExampleCount is a parameter from the check's options.)
# The items in the list should ideally be representative of a wide range of examples rather than merely variations on the same word.

    global listWords      # hash of lists  
    global ExampleCount   # user-specified option

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

   
#__________________________________________________________________________________
##### MAIN PROGRAM #####

formTally = {} # A hash array of hash arrays to tally the frequency count for each form of each combination of consonants
clusCt = 0
invalidReport = ""
clDict = {} # Dictionary to store from Allclustercorrections file

clusString = []

if initialize(): # if sucessfully read data from the books

    # Update count and examples in AllClusterCorrections file
    if os.path.isfile(clusallFilename):
        clusallFile = codecs.open(clusallFilename, mode='w', encoding='utf-8')
        clusallFile.write(u'\uFEFFRoot\tCluster\tClusterShow\tCount\tCorrect\tCorrectShow\tExamples\r\n') # BOM and column headings
    
        for base in sorted(clDict.iterkeys()):
            root = re.sub(virama, '', base)     # root is a display form that has just the letters without viramas or ZW chars
            for cl in sorted(clDict[base], key=lambda a: clDict[base][a][2], reverse=True):  # Sort by count (largest to smallest)
                clusallFile.write(root + "\t" + cl + "\t" + showAll(cl) + "\t" + str(int(clDict[base][cl][2])) + "\t" + clDict[base][cl][0] + "\t" + showAll(clDict[base][cl][0]) + "\t" + clDict[base][cl][1] + "\r\n")
            clusallFile.write("\r\n")   
        clusallFile.close()
    
    # Build ClusterCorrections file
    for base in sorted(formTally.iterkeys()):
        root = re.sub(virama, '', base)
        sortedForms = sorted(formTally[base].iterkeys(), key=lambda a: formTally[base][a], reverse=True) # Sort from most frequent to least
        
        if ExcludeSingle == "Yes" and len(sortedForms) == 1:  # Skip single-cluster forms if configured to do so
            continue
       
        newRules = {}   # For the current base, maps Cluster -> Correct, according to what we'd write to the ClusterCorrections file.
        oldRules = {}   # For the current base, maps Cluster -> Correct, according to what was in the AllClusterCorrections file.
                        # If these end up with the same contents, we won't need to write to the ClusterCorrections file.
        if base in clDict:
            for cl in clDict[base].iterkeys():      # Fill oldRules from clDict
                oldRules[cl] = clDict[base][cl][0]
        
        # First handle the best form
        bestForm = sortedForms[0]  # For now, bestForm is the most frequent form. This may change if we implement rule-and-exception-based options.
        if base in clDict and bestForm in clDict[base] and clDict[base][bestForm][0] != "": # If a previously-made decision replaces this with a different form, that's the best form.
            bestForm = clDict[base][bestForm][0]
        bestFormShow = showAll(bestForm)
        
        newRules[bestForm] = ""     # bestForm is always marked as valid (i.e. empty column)
        clusString = [root + "\t" + bestForm + "\t" + bestFormShow + "\t" + str(int(formTally[base][bestForm]))  + "\t" + "\t" + "\t"] # Output all columns except Examples
        if base in clDict and bestForm in clDict[base]: # If bestForm was in clDict, no need to run getExamples again. Just retrieve from clDict. (More efficient)
            clusString.append(clDict[base][bestForm][1] + "\r\n")
        else:               
            clusString.append(getExamples(bestForm) + "\r\n")   # Otherwise, get examples.
        clusCt += 1
        
        # Now handle all remaining forms, whether found in the text or not.
        for thisForm in sortedForms:
            if thisForm == bestForm:
                continue
           
            clusString.append(root + "\t" + thisForm + "\t" + showAll(thisForm) + "\t" + str(int(formTally[base][thisForm])) + "\t") # Root, Cluster, ClusterShow, Count
            if base in clDict and thisForm in clDict[base]: # If this form was already in AllClusterCorrections, use the same Correct, CorrectShow, and Examples.
                clusString.append(clDict[base][thisForm][0] + "\t" + showAll(clDict[base][thisForm][0]) + "\t" + clDict[base][thisForm][1] + "\r\n") 
                newRules[thisForm] = clDict[base][thisForm][0]
            else:                                           # Otherwise, propose bestForm as the Correct replacement
                clusString.append(bestForm + "\t" + bestFormShow + "\t" + getExamples(thisForm) + "\r\n")
                newRules[thisForm] = bestForm
            clusCt += 1
        
        # Write to file if the oldRules in AllClusterCorrections doesn't match with the new rules to propose in ClusterCorrections.
        if newRules != oldRules:
            for lineItem in clusString:
                clusFile.write(lineItem)
            clusFile.write("\r\n")
    
clusFile.close()

        
# Report on number of clusters written
if (clusCt>0):
    sys.stderr.write(str(clusCt) + " forms of " + str(len(formTally)) + " consonant combinations written to " + clusFilename + "\n")
    
# Report on invalid ZW characters, if found
if (len(invalidReport) > 0):
    sys.stderr.write(" \nAlso note: Using the STANDARDIZE tool to remove invalid ZW characters will fix this many issues:\n" + invalidReport + "\n")
    

# Copy the XLSX file to the project folder, if available and not already there.
try:
    xl1 = SettingsDirectory + "\\cms\\FormattedClusterStatus.xlsx" 
    xl2 = SettingsDirectory + Project + "\\FormattedClusterStatus.xlsx" 
    if os.path.isfile(xl1) and not os.path.isfile(xl2):
        shutil.copyfile(xl1, xl2)
except Exception, e:
    sys.stderr.write("Did not copy xlsx file\n")