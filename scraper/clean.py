#!/usr/bin/python3 -tt
import re
import sys
import getopt
import urllib.request

class Entry:
    """ Represents an entry in the database
    """
    def __init__(self,entryType,key,subentries):
        """ Constructor for the entry class,
            entryType is Article, Book and so on, key is the unique identifier and subentries is a dict of the data in the entry
            A special case is a "String" (entryType) entry which is used to copy abbreviations using this datastructure.
        """
        self.entryType = entryType
        self.key = key
        self.subentries = subentries

    def solveConflict(self,ourKey,theirData):
        """ Utility method to solve a conflict between two subinfo data
            Very simple, takes the shortest of both (used to prefer abbreviations to full journal names)
        """
        ourData = self.subentries[ourKey]
        #If this is an author key, we take the longest of both (to get the most names, and in the correct direction)
        #TODO: This is not actually very good, as it favors strangely formatted author names
        # if ourKey == b'author' or ourKey == b'Author':
        #     if len(ourData) > len(theirData):
        #         return ourData
        #     else:
        #         return theirData
        # else: #Otherwise we return the shortest of both data
        if len(ourData) < len(theirData):
            return ourData
        else:
            return theirData

    def merge(self,otherEntry):
        """ Merges two entries into one
        """
        # print('MERGING:')
        # print(self)
        # print(otherEntry)
        merged_subentries = dict(self.subentries)
        for (key,val) in otherEntry.subentries.items():
            if not key in merged_subentries.keys(): #The easy case, we just add the info
                # print('Simple merging of key: ' + repr(key))
                merged_subentries[key] = val
            elif merged_subentries[key] == val: #The other easy case, duplicate of subinfo
                # print('Duplicated subinfo for key: ' + repr(key))
                pass #We do nothing because the info is already in the merged_subentries dict
            else:
                # print('CONFLICT for key: ' + repr(key))
                mergedData = self.solveConflict(key,val)
                # print(' -> Solved conflict, chose: ' + repr(mergedData))
                merged_subentries[key] = mergedData
        
        #print('Result of merge:')
        mergedEntry = Entry(self.entryType,self.key,merged_subentries)
        #print(mergedEntry)
        return mergedEntry

    def cleanEntry(self):
        """ Remove some 'useless' fields from this entry (destructive method)
        """
        useless_fields = [b'Date-added', b'Date-modified', b'Owner', b'Timestamp', b'__markedentry', b'Bdsk-file-1', b'Bdsk-file-2', b'Bdsk-file-3', b'Bdsk-url-1', b'Bdsk-url-2', b'Bdsk-url-3', b'Local-url', b'Manep_group', b'Manep_project', b'Peer_review']
        for key in useless_fields:
            self.subentries.pop(key,None) #This removes key (if it exists) from the subentries dict

    def completeDoiField(self):
        """ If the doi field is not already present for this entry, try to search the web using the title to get the doi number
        """
        #TODO: This does not work, we would need to spoof a ua, but might not be worth the effort
        # if rb'doi' in self.subentries or rb'Doi' in self.subentries: #We do nothing if the doi is already entered
        #     return
        # key = [x for x in self.subentries.keys() if x in [rb'Title', rb'title']]
        # if not key: #If no title is specfied, we can't really search
        #     return
        # key = key[0] #Key should now hold title (or Title)
        # print(key)
        # searchurl = 'http://www.google.com/search?q='
        # searchurl += str(self.subentries[key],'utf-8')
        # searchurl = searchurl.replace('{','')
        # searchurl = searchurl.replace('}','')
        # searchurl = searchurl.replace(' ','+')
        # print(searchurl)
        # with urllib.request.urlopen(searchurl) as response:
        #        html = response.read()
        #        print('\n\n\n')
        #        print(html)

    def returnAsText(self):
        """ Returns a rbString representing this entry as text
            This method is used to write the cleaned entries to a file
        """
        out = b"\n\n@" + self.entryType + rb"{" + self.key + rb","
        for (key,val) in self.subentries.items():
            out += b"\n\t" + key + rb" = " + val + rb","
        out = out[:-1] #We remove the last comma
        out += b'\n}'
        return out

    def __str__(self):
        ss = 'Entry: Type: ' + repr(self.entryType) + '\n       Key: ' + str(self.key,'utf-8') + '\n       Subentries: ' + repr(self.subentries)
        return ss

def getEntries(filename):
    #The first group is the key, the second group is the rest (which we need to parse to get the subentries)
    #We match the @String to skip the defs at beggining of bib file.
    entryregex = re.compile(rb'@String|@(\w*?){(.*?),(.*?)\n\s*}',
                        re.DOTALL | re.IGNORECASE)
    #This regex is used to extract subentries from the second group of the previous regex, The first group is the key the second is the value.
    #subentryregex = re.compile(rb'\n\s*(.*?)\s*?=\s*(.*?),?\r',
    #subentryregex = re.compile(rb'\n\s*(\w*?)\s*?=\s*({.*?}),?\r',
    #subentryregex = re.compile(rb'\n\s*(\S*?)\s*?=\s*(\{?.*?\}?),?\r',
    subentryregex = re.compile(rb'\n\s*(\S*?)\s*?=\s*((?:\{.*?\}|.*?)),?\r',
                        re.DOTALL | re.IGNORECASE)

    allEntries = []
    with open(filename, 'rbU') as f:
        #allEntries = regex.findall(f.read())
        for match in entryregex.finditer(f.read()):
            #We skip the typedefs at the beginning
            if(match.group()==rb'@String'):
                continue
            entryType = match.group(1)
            key = match.group(2)
            rawsubentries = match.group(3)
            subentries = dict()
            #We now build a dict with the subentries
            # print('Processing entry: ')
            # print('key: ' + str(key,'utf-8'))
            # print('rawsubs: ' + repr(rawsubentries))
            for subent in subentryregex.finditer(rawsubentries):
                #print(subent.group(1)) 
                #print(subent.group(2)) 
                subentries[subent.group(1)] = subent.group(2)
            #print(subentries)
            allEntries.append(Entry(entryType,key,subentries))

    # for entry in allEntries:
    #     print(entry)
    
    return allEntries

def usage():
    """ Prints the usage of this script
    """
    print('Usage: ./clean.py -i <inputfile> -o <outputfile>')

def main(argv):
    """ Runs the cleaning procedure on the input file and produces an out-file
    """
    input_file = ''
    output_file = ''
    try:
        opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
    except getopt.GetoptError:
        print('Unknown option')
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            usage()
            sys.exit()
        elif opt in ("-i", "--ifile"):
            input_file = arg
        elif opt in ("-o", "--ofile"):
            output_file = arg

    if input_file == '' or output_file == '':
        print('Error: Please enter both an input and an output destination')
        usage()
        sys.exit(1)

    #We begin by copying all @String statements at the beggining of the output file
    with open(output_file, 'wb') as outf:
        with open(input_file, 'rbU') as inf:
            for line in inf:
                match = re.search(rb'@String',line)
                if match:
                    outf.write(line)

    #We get all entries of the bibfile
    entries = getEntries(input_file)

    #We sort the entries to facilitate removal of duplicates
    entries.sort(key=lambda x: x.key)

    #Now we can iterate the list and remove duplicates
    cleanedEntries = []
    while len(entries) > 0:
        topEntry = entries.pop()
        duplicata = [topEntry]
        while len(entries)>0 and topEntry.key == entries[-1].key:
            duplicata.append(entries.pop())
        #print('Found ' + str(len(duplicata)-1) + ' duplicata of key: ' + repr(topEntry.key))
        while len(duplicata) > 1:
            e1 = duplicata.pop()
            e2 = duplicata.pop()
            duplicata.append(e1.merge(e2))
        cleanedEntries.append(duplicata.pop())

#    for ee in cleanedEntries:
#        print('--------------------------')
#        #print(str(ee.returnAsText(),'utf-8'))
#        print(ee)
#        print(str(ee.returnAsText()))

    #We also clean some 'useless' fields from each entry
    for ee in cleanedEntries:
        ee.cleanEntry()

    with open(output_file, 'ab') as outf:
        for ee in reversed(cleanedEntries): #We iterate in reversed order to have the list sorted at the end
            outf.write(ee.returnAsText())

    nEntry = 4563
    print(cleanedEntries[nEntry])
    cleanedEntries[nEntry].completeDoiField()

    print("Done !")

if __name__ == '__main__':
    main(sys.argv[1:])

