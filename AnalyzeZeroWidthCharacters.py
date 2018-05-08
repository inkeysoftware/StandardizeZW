# coding=utf-8
from ScriptureObjects import ScriptureText
import re
import sys
import codecs

#__________________________________________________________________________________
# INITIALIZE CONSTANTS WITH REGEX STRINGS:

# c = set of all consonant characters
c = '[' + r'\u0915-\u0939\u0958-\u095f\u097b-\u097f' + r'\u0995-\u09b9\u09ce\u09dc-\u09df\u09f0-\u09f1' + r'\u0a15-\u0a39\u0a59-\u0a5f' + r'\u0a95-\u0ab9' + r'\u0b15-\u0b39\u0b5c-\u0b5f\u0b71' + r'\u0b95-\u0bb9' + r'\u0c15-\u0c39\u0c58\u0c59' + r'\u0c95-\u0cb9\u0cde' + r'\u0d15-\u0d39\u0d7a-\u0d7f' + ']'

# v = set of all vowel characters
v = '[' + r'\u0904-\u0914\u093e-\u094c' + r'\u0b04-\u0b14\u0b3e-\u0b4c\u0b56-\u0b57' + ']'  # TO DO: Need to add other scripts, only DEV and ODI so far

# optional nukta
optNukta = r'[\u093c\u09bc\u0a3c\u0abc\u0b3c\u0bbc\u0c3c\u0cbc\u0d3c]*' # includes some yet-to-be adopted nuktas.

# virama
virama = r'[\u094d\u09cd\u0a4d\u0acd\u0b4d\u0bcd\u0c4d\u0ccd\u0d4d]'
notVirama = r'([^\u094d\u09cd\u0a4d\u0acd\u0b4d\u0bcd\u0c4d\u0ccd\u0d4d])'

# zw
zw = r'[\u200c\u200d]*'

# cluster
cluster =  '(?:' + c + optNukta + zw + virama + zw + ')+(?:' + c + optNukta + ')?'

#__________________________________________________________________________________
# INITIALIZE OTHER CONSONANTS AND VARIABLES:

formTally = {} # A hash array of hash arrays to tally the frequency count for each form of each combination of consonants

infile = SettingsDirectory + Project + "\\WORDLIST.XML"
outfile = SettingsDirectory + Project + "\\Standard_Clusters.TXT"       # Original output file, for single valid form
outfile2 = SettingsDirectory + Project + "\\ClusterStatus.TXT"    # New output to support multiple valid forms

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
        sys.stderr.write("ERROR: This script was supposed to ignore invalid ZW characters, but the comparison is failing: " + repr(aStr[a]) + "!" + repr(bStr[b]) + "\n")
    return 0


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

    global outfile, outfile2, invalidReport, formTally, bases, thisVirama, f, f2, infile, notVirama, v, virama

    # Original output
    try:
        f = codecs.open(outfile, mode='w', encoding='utf-8')
        f.write(u'\uFEFF\r\n') # BOM
    except Exception, e:
        sys.stderr.write("Unable to write to file: " + outfile + "\n")
        return 0

    # New output
    try:
        f2 = codecs.open(outfile2, mode='w', encoding='utf-8')
        f2.write(u'\uFEFFRoot\tCluster\tClusterShow\tCount\tCorrect\tCorrectShow\r\n') # BOM and column headings
        #TODO: Add an Examples column header
    except Exception, e:
        sys.stderr.write("Unable to write to file: " + outfile2 + "\n")
        return 0
      
    try:
        scr = ScriptureText(Project)     # Open input project
              
        for reference, text in scr.allBooks(Books):  
        
            # Ignore any invalid ZW characters. THE REGEXES IN THIS CODE SHOULD MATCH WHAT'S IN THE STANDARDIZE SCRIPT!
            text2 = re.sub(notVirama + u'[\u200c\u200d]+', r'\1', text)  # Remove any ZW that doesn't follow virama
            text2 = re.sub('(' + v + virama + ')' + u'[\u200c\u200d]+', r'\1', text2) # Remove ZW that follows virama that follows a vowel.
                                # TODO: Figure out which other bad ZW characters may be left in the text, and delete them too.
                                
            # Keep track of invalid ZW characters removed, so we can report on that at the end.
            invalidCt = countChanges(text, text2)
            if (invalidCt > 0):
                invalidReport += "\t" + reference[:-4] + ":\t" + str(invalidCt) + "\n"
                
            # Count occurrences of each form of each cluster
            for cl in re.findall(cluster, text2):
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
    
#__________________________________________________________________________________
##### MAIN PROGRAM #####

clusCt = 0
invalidReport = ""
if initialize():
    for base in sorted(formTally.iterkeys()):
        clusCt += 1
        root = re.sub(virama, '', base)
        # cform = re.sub('(' + virama + ')', r'\1' + u'\u200c', base)
        # dform = re.sub('(' + virama + ')', r'\1' + u'\u200d', base)

        # maxCt = 0
        # bestCl = ''
        # if dform in formTally[base]:
            # if formTally[base][dform] > maxCt:
                # maxCt = formTally[base][dform]
                # bestCl = dform
            # del formTally[base][dform]
        # if base in formTally[base]:
            # if formTally[base][base] > maxCt:
                # maxCt = formTally[base][base]
                # bestCl = base
            # del formTally[base][base]
        # if cform in formTally[base]:
            # if formTally[base][cform] > maxCt:
                # maxCt = formTally[base][cform]
                # bestCl = cform
            # del formTally[base][cform]
        # for cl in sorted(formTally[base].iterkeys()):
            # if formTally[base][cl] > maxCt:
                # maxCt = formTally[base][cl]
                # bestCl = cl

        # f.write(bestCl + "\r\n")

        sortedForms = sorted(formTally[base].iterkeys(), key=lambda a: formTally[base][a], reverse=True)

        f.write(sortedForms[0] + "\r\n")
        
        # First write out best form
        bestForm = sortedForms[0]
        bestFormShow = showAll(bestForm)
        f2.write(root + "\t" + bestForm + "\t" + bestFormShow + "\t" + str(int(formTally[base][bestForm])) + "\t\t\t") 
        f2.write("\r\n")# TODO: Append examples
        
        # Now write out all remaining forms
        for x in range(1, len(sortedForms)):
            f2.write(root + "\t" + sortedForms[x] + "\t" + showAll(sortedForms[x]) + "\t" + str(int(formTally[base][sortedForms[x]])) + "\t" + bestForm + "\t" + bestFormShow + "\t") 
            f2.write("\r\n") # TODO: Append examples
            
        f2.write("\n")
        
# Report on number of clusters written
if (clusCt>0):
    sys.stderr.write(str(clusCt) + " clusters written to " + outfile + "\n")
    
# Report on invalid ZW characters, if found
if (len(invalidReport) > 0):
    sys.stderr.write("\nAlso note: Using the STANDARDIZE tool to remove invalid ZW characters will fix this many issues:\n" + invalidReport + "\n")

