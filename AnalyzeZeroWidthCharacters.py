# coding=utf-8
from ScriptureObjects import ScriptureText
from CommonZWC import countChanges
import re
import sys
import codecs
import os
import shutil
import difflib

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

# Initialization variable
default = 0

#__________________________________________________________________________________
# INITIALIZE OTHER CONSONANTS AND VARIABLES:


clusFilename = SettingsDirectory + Project + "\\ClusterStatus.TXT"    # New output to support multiple valid forms


#__________________________________________________________________________________
def showAll(s):
# Return a version of the string that shows [zwj] and [zwnj] in place of invisible characters
    return re.sub(u'\u200c', '[zwnj]', re.sub(u'\u200d', '[zwj]', s))

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

    global clusFilename, invalidReport, formTally, bases, thisVirama, f, clusFile, notVirama, v, virama, listWords, cl

    try:
        clusFile = codecs.open(clusFilename, mode='w', encoding='utf-8')
        clusFile.write(u'\uFEFFRoot\tCluster\tClusterShow\tCount\tCorrect\tCorrectShow\tExamples\r\n') # BOM and column headings
        #TODO: Add an Examples column header
    except Exception, e:
        sys.stderr.write("Unable to write to file: " + clusFilename + "\n")
        return 0
      
    try:
        scr = ScriptureText(Project)     # Open input project
        
        
        listWords = {}
        
        for reference, text in scr.allBooks(Books):  
        
            # Ignore any invalid ZW characters. THE REGEXES IN THIS CODE SHOULD MATCH WHAT'S IN THE STANDARDIZE SCRIPT!
            text2 = re.sub(notVirama + u'[\u200c\u200d]+', r'\1', text)  # Remove any ZW that doesn't follow virama
            text2 = re.sub('(' + nonCons + optNukta + virama + ')' + u'[\u200c\u200d]+', r'\1', text2) # Remove ZW that follows a weird virama that follows a non-Consonant.
                                
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


# def examples(bCluster):
    # global listWords      
    # global ExampleCount
    # s = sorted(listWords[bCluster])
    # ls = len(s)
    # increment = int(ls/ExampleCount) + (ls % ExampleCount > 0)  # increment is rounded up
    # increment = max(increment, 1) # must not be zero
    # return ', '.join(s[0:ls:increment])  # Might get slightly different than ExampleCount items
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
    
# def examplesList(cCluster):
    # global ExampleCount
    # sampleList = re.split(',',examples(cCluster))
       
    # finalList = []

    # Logic issue: This might exclude close matches even though we have less than ExampleCount items in the list to begin with.
    # Also, if none are "close" enough (0.6 ratio by default), this will return a list of the *first* ExampleCount items. e.g. All at the beginning of the alphabet.
    # To use difflib effectively here, I think we'd have to remove the item that is most similar to another item, and repeat until the list has only ExampleCount items remaining.
    
    # for example in sampleList:
        # if len(finalList) == ExampleCount:
            # return finalList
        # else:
            # finalList.append(example);
            # for each in difflib.get_close_matches(example,sampleList):
                # sampleList.remove(each)
           
    # return finalList

##### MAIN PROGRAM #####

formTally = {} # A hash array of hash arrays to tally the frequency count for each form of each combination of consonants
clusCt = 0
rootCt = 0
invalidReport = ""


if initialize():
    for base in sorted(formTally.iterkeys()):
        root = re.sub(virama, '', base)
        sortedForms = sorted(formTally[base].iterkeys(), key=lambda a: formTally[base][a], reverse=True) # Sort from most frequent to least
        
        if ExcludeSingle == "No" or len(sortedForms) > 1:
        
            # First write out best form
            bestForm = sortedForms[0]
            bestFormShow = showAll(bestForm)
                    
            #clusFile.write(root + "\t" + bestForm + "\t" + bestFormShow + "\t" + str(int(formTally[base][bestForm])) + "\t" + "\t" + "\t" + tamedEglist(bestForm,5)) 
            # clusFile.write(root + "\t" + bestForm + "\t" + bestFormShow + "\t" + str(int(formTally[base][bestForm])) + "\t" + "\t" + "\t")
            clusFile.write(root + "\t" + bestForm + "\t" + bestFormShow + "\t" + str(int(formTally[base][bestForm])) + "\t" + "\t" + "\t" + examples(bestForm)) 
            # clusFile.write(', '.join(examplesList(bestForm)))
            clusFile.write("\r\n")
            clusCt += 1
            rootCt += 1
            
            # Now write out all remaining forms
            for x in range(1, len(sortedForms)):
                # clusFile.write(root + "\t" + sortedForms[x] + "\t" + showAll(sortedForms[x]) + "\t" + str(int(formTally[base][sortedForms[x]])) + "\t" + bestForm + "\t" + bestFormShow + "\t" + examplesList(sortedForms[x])) # should return a string
                clusFile.write(root + "\t" + sortedForms[x] + "\t" + showAll(sortedForms[x]) + "\t" + str(int(formTally[base][sortedForms[x]])) + "\t" + bestForm + "\t" + bestFormShow + "\t" + examples(sortedForms[x])) 
                clusFile.write("\r\n") 
                clusCt += 1
                
            clusFile.write("\r\n")
        
# Report on number of clusters written
if (clusCt>0):
    sys.stderr.write(str(clusCt) + " forms of " + str(rootCt) + " consonant combinations written to " + clusFilename + "\n")
    
# Report on invalid ZW characters, if found
if (len(invalidReport) > 0):
    sys.stderr.write("\nAlso note: Using the STANDARDIZE tool to remove invalid ZW characters will fix this many issues:\n" + invalidReport + "\n")
    
clusFile.close()

# Copy the XLSX file to the project folder, if available and not already there.
try:
    xl1 = SettingsDirectory + "\\cms\\FormattedClusterStatus.xlsx" 
    xl2 = SettingsDirectory + Project + "\\FormattedClusterStatus.xlsx" 
    if os.path.isfile(xl1) and not os.path.isfile(xl2):
        shutil.copyfile(xl1, xl2)
except Exception, e:
    sys.stderr.write("Did not copy xlsx file\n")