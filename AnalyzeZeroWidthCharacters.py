# coding=utf-8
from ScriptureObjects import ScriptureText
import re
import sys
import codecs

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

hoh = {}

infile = SettingsDirectory + Project + "\\WORDLIST.XML"
outfile = SettingsDirectory + Project + "\\Standard_Clusters.TXT"

# Return true if input is valid
def validInput():
    global outfile, hoh, bases, thisVirama, f, infile, notVirama, v, virama

    # if len(Parameter1) == 0:
        # sys.stderr.write("You must enter the full path and filename of the exported wordlist file to read.\n")
        # return 0

    # if len(outfile) == 0:
        # sys.stderr.write("You must enter the full path and filename of the output file to create/overwrite.\n")
        # return 0

    try:
        f = codecs.open(outfile, mode='w', encoding='utf-8')
        f.write(u'\uFEFF\r\n') # BOM
    except Exception, e:
        sys.stderr.write("Unable to write to file: " + Parameters + "\n")
        return 0
      
    try:
        scr = ScriptureText(Project)     # Open input project
        if Project == OutputProject:
            scrOut = scr    
        else:
            scrOut = ScriptureText(OutputProject)    # Open separate output project
              
        for reference, text in scr.allBooks(Books):  # TODO: Check that allBooks() here means "all selected books".
            text = re.sub(notVirama + u'[\u200c\u200d]+', r'\1', text)  # Remove any ZW that doesn't follow virama
            text = re.sub('(' + v + virama + ')' + u'[\u200c\u200d]+', r'\1', text) # Remove ZW that follows virama that follows a vowel.
                                # TODO: Figure out which other bad ZW characters may be left in the text, and delete them too.
            clusters = re.findall(cluster, text)
            for cl in clusters:
                base = re.sub(zw, '', cl)
                if base in hoh:
                    if cl in hoh[base]:
                        ct += 1
                        hoh[base][cl] += ct
                    else:
                        ct = 1
                        hoh[base][cl] = ct
                else:
                    ct = 1
                    hoh[base] = {cl : ct}
                    
    except Exception, e:
        sys.stderr.write("Error looping through Scripture books.")
        return 0
    
    return 1    
    
clusCt = 0
if validInput():
##    f.write("Root\tS\tS Ct\tJ\tJ Ct\tN\tN Ct\tOther\tType\tCt\r\n")
    for base in sorted(hoh.iterkeys()):
        clusCt += 1
        root = re.sub(virama, '', base)
        cform = re.sub('(' + virama + ')', r'\1' + u'\u200c', base)
        dform = re.sub('(' + virama + ')', r'\1' + u'\u200d', base)
        # f.write(root + "\t" + base + "\t")
        # if base in hoh[base]:
            # f.write(str(hoh[base][base]))
            # del hoh[base][base]
        # f.write("\t" + dform + "\t")
        # if dform in hoh[base]:
            # f.write(str(hoh[base][dform]))
            # del hoh[base][dform]
        # f.write("\t" + cform + "\t")
        # if cform in hoh[base]:
            # f.write(str(hoh[base][cform]))
            # del hoh[base][cform]
        # for cl in sorted(hoh[base].iterkeys()):
            # typ = re.sub(virama + u'\u200C', 'N', cl)
            # typ = re.sub(virama + u'\u200D', 'J', typ)
            # typ = re.sub(virama, 'S', typ)
            # typ = re.sub(u'[\u200D\u200C]', 'x', typ)
            # typ = re.sub(r'[^NJSx]', '', typ)
            # f.write("\t" + cl + "\t" + typ + "\t" + str(hoh[base][cl]))
        maxCt = 0
        bestCl = ''
        if dform in hoh[base]:
            if hoh[base][dform] > maxCt:
                maxCt = hoh[base][dform]
                bestCl = dform
            del hoh[base][dform]
        if base in hoh[base]:
            if hoh[base][base] > maxCt:
                maxCt = hoh[base][base]
                bestCl = base
            del hoh[base][base]
        if cform in hoh[base]:
            if hoh[base][cform] > maxCt:
                maxCt = hoh[base][cform]
                bestCl = cform
            del hoh[base][cform]
        for cl in sorted(hoh[base].iterkeys()):
            if hoh[base][cl] > maxCt:
                maxCt = hoh[base][cl]
                bestCl = cl

        f.write(bestCl + "\r\n")
        
if (clusCt>0):
    ##sys.stderr.write(str(clusCt) + " clusters written to " + outfile + "\n\nPaste the contents of this file into a spreadsheet for analysis.\nFrom this you can create a STANDARD_CLUSTERS.TXT file to be used with the <Standardize Zero-Width Characters> tool,\nand an INVALID_CLUSTERS.TXT file to be used with the <Generate Zero-Width Spelling Rules> tool.")
    sys.stderr.write(str(clusCt) + " clusters written to " + outfile + "\n\n")
