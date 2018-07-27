# Commonzwc.py

import re
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

def ignoreanyInvalidzw(text):
    # Ignore any invalid ZW characters. THE REGEXES IN THIS CODE SHOULD MATCH WHAT'S IN THE STANDARDIZE SCRIPT!
    text2 = re.sub(notVirama + u'[\u200c\u200d]+', r'\1', text)  # Remove any ZW that doesn't follow virama
    text2 = re.sub('(' + nonCons + optNukta + virama + ')' + u'[\u200c\u200d]+', r'\1', text2) # Remove ZW that follows a weird virama that follows a non-Consonant.
    return text2    

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

