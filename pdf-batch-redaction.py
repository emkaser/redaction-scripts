# imports
import fitz
import os
import sys

dir = sys.argv[1]

def find_files_in_dir(dirpath):
    """Scans a directory tree and gets os.DirEntry objects for the specified files
    
    Adapted from code by Ben Hoyt on Stackoverflow: https://stackoverflow.com/a/33135143 

    Parameters
    -----------
    dirpath : str
        The file path of the directory to scan
    
    Returns
    -----------
    os.DirEntry object
        Inidividual os.DirEntry objects for the specified files as they are generated
        Description of os.DirEntry attributes: https://docs.python.org/3/library/os.html#os.DirEntry
    """

    for entry in os.scandir(dirpath):
        if entry.is_dir():
            yield from find_files_in_dir(entry.path)
        else:
            filename = str(entry.name)
            try:
                if filename.startswith(("Application-", "Judge-")):
                    if filename.endswith(".pdf"):
                        yield entry
            except TypeError:
                continue

def redaction(file):

    #Adapted from code: https://www.geeksforgeeks.org/pdf-redaction-using-python/

    doc = fitz.open(file)
    for page in doc:
        text = page.get_text()
        start = "Login and Password information if needed\n"
        end = "\nStory Link 1"
        #print(file)

        try:
            result = text[text.index(start)+len(start):text.index(end)]
            for rect in page.search_for(result):
                page.add_redact_annot(rect)
            
        except ValueError:
            continue 
        page.apply_redactions()
        new = file.split(".pdf")[0]
        newname = f"{new}_redacted.pdf"
        print(newname)
    doc.save(newname)

if __name__ == "__main__":
    for entry in find_files_in_dir(dir):
        filepath = entry.path
        redaction(filepath)