"""Batch PDF Redactor

This script parses searchable (i.e. OCR-readable) PDFs to identify strings for redaction.
It creates a "quad" around the specified area in the PDF and permanently deletes text 
within that area, replacing it with a black rectangle.

Using the optional argument "replace" will save a new redacted copy of the file and delete
the unredacted original. If no argument is used, the script will automatically save a new 
file with "_redacted" in the file name alongside the original.

This script requires an installation of PyMuPDF in your Python environment: https://github.com/pymupdf/PyMuPDF#installation

Script usage: python path/to/script path/to/dir/for/redaction [replace]
"""
import fitz #This is the import for PyMuPDF
import os
import sys
import csv
from datetime import datetime

date = datetime.now().strftime("%Y%m%d")
header = ['File', 'Date_redacted', 'Notes']

dir = sys.argv[1]
try:
    if sys.argv[2]:
        optional_arg = sys.argv[2]
except IndexError:
    optional_arg = 'null'

def find_files_in_dir(dir):
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

    for entry in os.scandir(dir):
        if entry.is_dir():
            yield from find_files_in_dir(entry.path)
        else:
            filename = str(entry.name)
            try:
                if filename.startswith(("Application-", "Judge-")):
                    if filename.endswith(".pdf"):
                        if filename.endswith("_redacted.pdf"):
                            continue
                        else:
                            yield entry
            except TypeError:
                continue


def find_redaction_log(dir):
    """Scans a directory and identifies a CSV redaction log created by this script
    
    Parameters
    -----------
    dir : str
        The file path of the directory to scan

    Returns
    -----------
    string
        The file path of the CSV redaction log in the directory
    """

    with os.scandir(dir) as d:
        for entry in d:
            if 'redactionlog' in str(entry):
                redact_log = entry.path
                return str(redact_log)

def log_file(file, error=None):
    """Adds a filepath, timestamp, and optional error field to the redaction log.
    
    Parameters
    -----------
    file : str
        The path of the file the script is trying to redact
    
    error: str
        Text to appear in the "Notes" field of the redaction log

    Returns
    -----------
    None
    """
    data = []
    data.append(file)
    data.append(datetime.now().strftime("%Y-%m-%d"))
    data.append({error})
    writer.writerow(data)

def redaction(file):
    """Opens a file, locates the text to redact by identifying starting and ending strings, 
    and then redacts it. If the "overwrite" argument is used, overwrites the existing PDF 
    with the changes. If no argument, creates a new file with "_redacted" in the file name.
    
    Adapted from code: https://www.geeksforgeeks.org/pdf-redaction-using-python/ 

    [[Future issue: PyMuPDF can only iterate by page and will throw errors on substrings that
    are split. Future solution could be regex that doesn't rely on starting/ending strings being
    on the same page, or a function that combines all text without breaks before searching it.]]

    Parameters
    -----------
    file : path attribute of os.DirEntry object
        The path attribute of an object yielded by the find_files_in_dir() iterator
    
    Returns
    -----------
    file: path attribute of os.DirEntry object
        The path attribute of a file object that has been successfully redacted
        
    """

    doc = fitz.open(os.path.join(dir, file))

    file_stat = 'Unredacted'

    for page in doc:
        text = page.get_text()

        # Change these substrings to search the PDF text and find the specific redaction area
        start_redact = "Login and Password information if needed\n"
        end_redact1 = "\nStory Link 1"
        end_redact2 = "\nVideo Upload 1"
        end_redact3 = "\nPublication, "

        result = None

        if end_redact1 in text:
            error = "CHECK FILE: Potential redaction found but not completed"
            try:
                result = text[text.index(start_redact)+len(start_redact):text.index(end_redact1)]
            except ValueError:
                #print(f'\t> {error}')
                log_file(file, error)
                result = None

        if end_redact2 in text:
            try:
                result = text[text.index(start_redact)+len(start_redact):text.index(end_redact2)]
            except ValueError:
                #print(f'\t> {error}')
                log_file(file, error)
                result = None

        if end_redact3 in text:
            try:
                result = text[text.index(start_redact)+len(start_redact):text.index(end_redact3)]
            except ValueError:
                #print(f'\t> {error}')
                log_file(file, error)
                result = None

        if result != None:
            if result.lower() not in ['n/a', 'na']:
                for rect in page.search_for(result):
                    page.add_redact_annot(rect, fill=(0,0,0))
              
                page.apply_redactions()
                file_stat = 'Redacted'

    if file_stat == 'Redacted':
        new = file.split(".pdf")[0]
        newname = f"{new}_redacted.pdf"
        doc.save(newname)
        #print(f'\t> REDACTED')
        return file


def batch_redact(dir):
    """Iterates through a directory, calling the redaction() function for each
    appropriate file, printing the result to the terminal, and logging both 
    successful redactions and attempts with errors in the CSV redaction log.

    Parameters
    -----------
    dir : str
        The file path of the directory containing the files to be redacted
    
    Returns
    -----------
    files: list
        A list of redacted files
        
    """ 

    files = []
    count = 0
    for entry in find_files_in_dir(dir):
        count += 1
        filepath = entry.path
        #print(f'\n{count}) {filepath}')

        try:
            f = redaction(filepath)
        except Exception:
            error = 'ERROR - needs review'
            log_file(filepath, error)

        if f != None:
            log_file(f)
            files.append(f)

    return files


if __name__ == "__main__":

    redact_log = find_redaction_log(dir)
    if redact_log:
        logfile = redact_log.rsplit('\\', 1)[-1]
        print(f'\nA file called "{logfile}" already exists in this location. If any additional redactions are made, they will be logged in this file.')
          
    else:
        redact_log = f'{dir}\\redactionlog_{date}.csv'
        with open(redact_log, "w", encoding="utf-8", newline='') as log:
            writer = csv.writer(log, delimiter=',')
            writer.writerow(header)  

    with open(redact_log, "a", encoding="utf-8", newline='') as log:
        writer = csv.writer(log, delimiter=',')

        if optional_arg.lower() == "replace":
            confirm = input(f'\nYou have chosen to create new redacted files and delete the originals. This action cannot be undone.\n\nType Y to continue and N to quit: ')
            if confirm.lower() == 'y':
                for sensitive_file in batch_redact(dir):
                    os.remove(sensitive_file)
                else: 
                    exit()

        if optional_arg == 'null':
            confirm = input(f'\nRedacted copies will be saved alongside the unredacted originals.\n\nType Y to continue and N to quit: ')
            if confirm.lower() == 'y':
                batch_redact(dir)
            else: 
                exit()
