#!/Library/Frameworks/Python.framework/Versions/3.8/bin/python3

# This script scrapes the academia.edu website to extract an academic work list

import re
import json
import urllib.request
import pprint
import os # Needed to store files always in same dir as script
from dateutil.parser import parse

class Work:
    """ Represents an academic work on the academia page
        The fields mimic what can be read from the academa json.
    """
    def __init__(self,raw_json):
        """ Reads the json from raw_json """
        try:
            self.workJSON = json.loads(raw_json)
        except Exception as e:
            print("Error parsing following json:")
            print(raw_json)
            print(e)
            self.workJSON = None
            return
        # else:
            # print('Read json as: ')
            # print(self.workJSON)

    def getAttrib(self, attrib):
        """ Safe accessor, returns None if requested attrib not in json """
        if self.workJSON is None:
            return None
        elif attrib not in self.workJSON:
            return None
        else:
            return self.workJSON[attrib]

    def getPublicationYear(self):
        """Return publication year or zero if no metadata found"""
        meta = self.getAttrib("metadata");
        
        if meta is None:
            return 0

        if "publication_date" not in meta or "year" not in meta["publication_date"]:
            return 0;

        return int(meta["publication_date"]["year"])

    def toMarkdownListEntry(self):
        """ Writes a table-entry in markdown to represent this work """
        assert(self.workJSON is not None)
        #[Success Button Text](#link){: .btn .btn--success}
        out = '| ' + '[academia link]' + '(' + self.getAttrib('internal_url') + ')' + '{: .btn .btn--inverse}'
        out += ' | ' + self.getAttrib('title')

        #If we can find a download url, add a button
        atta = self.getAttrib("downloadable_attachments")
        print("Attachments for: " + str(self.getAttrib('title')) + ": " + str(atta))
        dl_url = None
        if atta is not None and len(atta) == 1 and "download_url" in atta[0]:
            dl_url = atta[0]["download_url"]

        if dl_url is not None:
            out += ' | ' + '[download]' + '(' + dl_url + ')' + '{: .btn .btn--inverse}'

        out += ' |'
        return out

    def __str__(self):
        return pprint.pformat(self.workJSON)

    # Methods needed for set
    # We use a set when reading works, to make sure that there
    # are no duplicates
    def __eq__(self, other):
        if isinstance(other, Work):
            #We have perfect hashing
            return self.__hash__() == other.__hash__()
        else:
            return False
    def __ne__(self, other):
        return (not self.__eq__(other))
    def __hash__(self):
        if self.workJSON is not None:
            return self.workJSON['id']
        else:
            return 0


def scrapeWorks(base_url, username):
    """ Returns a list of scraped works from the academia website. """
    works = set()
    with urllib.request.urlopen(base_url + username) as response:
        for line in response.readlines():
            #print(line)
            match = re.search(rb'workJSON: (.*),\n', line)
            if match:
                #print(match.group(1))
                #We parse the json (by using Work constructor) and add the
                #resulting work object to the list of all scraped works
                works.add(Work(match.group(1)))

    return works

def main():
    #The folder the scraper script is currently located in.  We store the output
    #files relative to this.
    script_folder = os.path.basename(os.path.dirname(os.path.realpath(__file__)))

    username = 'MarieDGarnier' #The username we want to scrape data from
    #username = 'SeidererAnna' #The username we want to scrape data from
    academia_base_url = 'https://univ-paris8.academia.edu/'

    print("Scraping academia website at: " + academia_base_url + " for username: " + username)

    #We scrape a list of works from the academia website
    works = scrapeWorks(academia_base_url, username)

    #Now we only keep books and articles, and also order them by date.
    books = [w for w in works if (w.getAttrib('document_type') == 'book')]
    papers = [w for w in works if (w.getAttrib('document_type') == 'paper')]

    #We sort articles and books by upload date
    #papers.sort(key = lambda x : parse(x.getAttrib('created_at')), reverse=True)
    #books.sort(key = lambda x : parse(x.getAttrib('created_at')), reverse=True)

    #We sort articles and books by publication year.
    papers.sort(key = lambda x : x.getPublicationYear(), reverse=True);
    books.sort(key = lambda x : x.getPublicationYear(), reverse=True);

    print("Writing output files...")

    #Finally we write them to two external files which will be included in
    #the research page by Jekyll
    with open(script_folder + "/" + "scraped_books.md","w") as f:
        for book in books:
            f.write(book.toMarkdownListEntry())
            f.write('\n')

    with open(script_folder + "/" + "scraped_papers.md","w") as f:
        for paper in papers:
            f.write(paper.toMarkdownListEntry())
            f.write('\n')

    print("Successfully wrote scraped results to scraped_books.md and scraped_papers.md")

if __name__ == '__main__':
    main()
