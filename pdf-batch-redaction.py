"""Batch PDF Redactor

This script parses searchable (i.e. OCR-readable) PDFs to identify strings for redaction.
It creates a "quad" around the specified area in the PDF and permanently deletes text 
within that area, replacing it with a white rectangle.

Using the optional argument "overwrite" will overwrite the existing file with the redacted 
version. Otherwise, it will automatically save a new copy with "_redacted" in the file name.

This script requires an installation of PyMuPDF in your Python environment: https://github.com/pymupdf/PyMuPDF#installation

Script usage: python path/to/script path/to/dir/for/redaction [overwrite]
"""
import fitz #This is the import for PyMuPDF
import os
import sys


dir = sys.argv[1]
overwrite = sys.argv[2]

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
        Individual os.DirEntry objects for the specified files as they are generated
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
    """Opens a file, locates the text to redact by identifying starting and ending strings, 
    and then redacts it. If the "overwrite" argument is used, overwrites the existing PDF 
    with the changes. If no argument, creates a new file with "_redacted" in the file name.
    
    Adapted from code: https://www.geeksforgeeks.org/pdf-redaction-using-python/ 

    Parameters
    -----------
    file : os.DirEntry object
        The object yielded by the find_files_in_dir() iterator for the file
    """

    doc = fitz.open(file)
    for page in doc:
        text = page.get_text()

        start_redact = "Login and Password information if needed\n"
        end_redact = "\nStory Link 1"

        try:
            result = text[text.index(start_redact)+len(start_redact):text.index(end_redact)]
            for rect in page.search_for(result):
                page.add_redact_annot(rect)
            
        except ValueError:
            print (f'{file} raised a value error - check for incomplete redaction.\n')
            continue 
            
        except TypeError:
            continue

        page.apply_redactions()
    
    if overwrite.lower() == "overwrite":
        doc.saveIncr()
        doc.close()

    else:
        new = file.split(".pdf")[0]
        newname = f"{new}_redacted.pdf"
        doc.save(newname)

if __name__ == "__main__":
    for entry in find_files_in_dir(dir):
        filepath = entry.path
        redaction(filepath)