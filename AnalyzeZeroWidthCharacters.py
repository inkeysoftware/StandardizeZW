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

    global clusFilename, clusallFilename, invalidReport, formTally, thisVirama, f, clusFile, clusallFile, notVirama, v, virama, listWords, cl, clDict, check

    try:
        clusFile = codecs.open(clusFilename, mode='w', encoding='utf-8')
        clusFile.write(u'\uFEFFRoot\tCluster\tClusterShow\tCount\tCorrect\tCorrectShow\tExamples\r\n') # BOM and column headings
        
    except Exception, e:
        sys.stderr.write("Unable to write to file: " + clusFilename + "\n")
        return 0
    
          
    try:
        
        # Build allclusters dictionary from allclustercorrections file, if it exists
        check = buildDict()
      
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
                    base = re.sub(zw, '', cl)       # The base form is a simple stack form
                    root = re.sub(virama, '', base) # The root form is just the constanants without virama or zero-width.
                    
                    if root in formTally:
                        if cl in formTally[root]:
                            formTally[root][cl] += 1
                        else:
                            formTally[root][cl] = weightedCt(cl, base)
                    else:
                        formTally[root] = {cl : weightedCt(cl, base)}
        
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
                    root = allfields[0]
                    cl = allfields[1]
                    if root not in clDict:
                        clDict[root] = {}
                           
                    clDict[root][cl] = [allfields[4], allfields[6]]
                              
            clusallFile.close()

    except Exception, e:
        sys.stderr.write("Unable to process all cluster file")
        return 0 # Error
    
    
    return fileread


   
##### MAIN PROGRAM #####

formTally = {} # A hash array of hash arrays to tally the frequency count for each form of each combination of consonants
clusCt = 0
invalidReport = ""
clDict = {} # Dictionary to store from Allclustercorrections file

clusString = []

if initialize():

    if os.path.isfile(clusallFilename):
        clusallFile = codecs.open(clusallFilename, mode='w', encoding='utf-8')
        clusallFile.write(u'\uFEFFRoot\tCluster\tClusterShow\tCount\tCorrect\tCorrectShow\tExamples\r\n') # BOM and column headings
    
        for root in sorted(clDict.iterkeys()):
            for eachcluster in sorted(clDict[root]):
                if root in formTally and eachcluster in formTally[root]:
                    clusallFile.write(root + "\t" + eachcluster + "\t" + showAll(eachcluster) + "\t" + str(int(formTally[root][eachcluster])) + "\t" + clDict[root][eachcluster][0] + "\t" + showAll(clDict[root][eachcluster][0]) + "\t" + examples(eachcluster))
                else:
                    clusallFile.write(root + "\t" + eachcluster + "\t" + showAll(eachcluster) + "\t" + "0" + "\t" + clDict[root][eachcluster][0] + "\t" + showAll(clDict[root][eachcluster][0]) + "\t" + clDict[root][eachcluster][1])
                clusallFile.write("\r\n")
            clusallFile.write("\r\n")   
        clusallFile.close()
        
    for root in sorted(formTally.iterkeys()):
        oldRules = {}
        #root = re.sub(virama, '', base)
        sortedForms = sorted(formTally[root].iterkeys(), key=lambda a: formTally[root][a], reverse=True) # Sort from most frequent to least
        
        if ExcludeSingle == "No" or len(sortedForms) > 1:
           
            if root in clDict:
                for oldkeys in clDict[root].iterkeys():
                    oldRules[oldkeys] = clDict[root][oldkeys][0]
            newRules = {}
            
            # First write out best form
            bestForm = sortedForms[0]
            bestFormShow = showAll(bestForm)
            
            if root in clDict and bestForm in clDict[root]:
                
                clusString = [root + "\t" + bestForm + "\t" + showAll(bestForm) + "\t" + str(int(formTally[root][bestForm])) + "\t" + clDict[root][bestForm][0] + "\t" + showAll(clDict[root][bestForm][0]) + "\t" + (examples(bestForm) if formTally[root][bestForm] else clDict[root][bestForm][1])]
                newRules[bestForm] = clDict[root][bestForm][0]
                del clDict[root][bestForm]
                
            else:   
                clusString = [root + "\t" + bestForm + "\t" + bestFormShow + "\t" + str(int(formTally[root][bestForm])) + "\t" + "\t" + "\t" + examples(bestForm)]
                newRules[bestForm] = ""
            
            clusString.append("\r\n")
                
            clusCt += 1
            
            # Now write out all remaining forms from sortedForms found in text
            for x in range(1, len(sortedForms)):
                thisForm = sortedForms[x]
               
                if root in clDict and thisForm in clDict[root]:
                   
                    clusString.append(root + "\t" + thisForm + "\t" + showAll(thisForm) + "\t" + str(int(formTally[root][thisForm])) + "\t" + clDict[root][thisForm][0] + "\t" + showAll(clDict[root][thisForm][0]) + "\t" + (examples(thisForm) if formTally[root][thisForm] else clDict[root][thisForm][1])) 
                    newRules[thisForm] = clDict[root][thisForm][0]
                    del clDict[root][thisForm]
                    
                else:     
                    clusString.append(root + "\t" + thisForm + "\t" + showAll(thisForm) + "\t" + str(int(formTally[root][thisForm])) + "\t" + bestForm + "\t" + bestFormShow + "\t" + examples(thisForm))
                    newRules[thisForm] = bestForm
                clusString.append("\r\n") 
                clusCt += 1
                
            # Finally, write out any forms that existed in AllCorrections but which no longer exist in the text
            if root in clDict:
                for thisForm in clDict[root]:
                    
                    clusString.append(root + "\t" + thisForm + "\t" + showAll(thisForm) + "\t" + "0" + "\t" + clDict[root][thisForm][0] + "\t" + showAll(clDict[root][thisForm][0]) + "\t" + clDict[root][thisForm][1])
                    clusString.append("\r\n")
                    newRules[thisForm] = clDict[root][thisForm][0]
                   
            clusString.append("\r\n")
            
            # Write to file if the oldRules in Allclustercorrections doesn't match with the new rules.
            if newRules != oldRules:
                for lineItem in clusString:
                    clusFile.write(lineItem)
    
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