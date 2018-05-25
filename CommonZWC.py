# Commonzwc.py

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