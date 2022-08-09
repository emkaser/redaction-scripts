# imports
import fitz
import re

# Code from https://www.geeksforgeeks.org/pdf-redaction-using-python/

class Redactor:
   
    # static methods work independent of class object
    @staticmethod
    def get_sensitive_data(lines):
       
        """ Function to get all the lines """
         
        # email regex
        EMAIL_REG = r"([\w\.\d]+\@[\w\d]+\.[\w\d]+)"
        for line in lines:
           
            # matching the regex to each line
            if re.search(EMAIL_REG, line, re.IGNORECASE):
                search = re.search(EMAIL_REG, line, re.IGNORECASE)
                 
                # yields creates a generator
                # generator is used to return
                # values in between function iterations
                yield search.group(1)
 
    # constructor
    def __init__(self, path):
        self.path = path
 
    def redaction(self):
       
        """ main redactor code """
         
        # opening the pdf
        doc = fitz.open(self.path)
        print(doc)
         
        # iterating through pages
        for page in doc:
            print(page)
           
            # _wrapContents is needed for fixing
            # alignment issues with rect boxes in some
            # cases where there is alignment issue
            #page.wrapContents()
             
            # getting the rect boxes which consists the matching email regex
            sensitive = self.get_sensitive_data(page.getText("text")
                                                .split('\n'))
            for data in sensitive:
                areas = page.searchFor(data)
                 
                # drawing outline over sensitive datas
                [page.addRedactAnnot(area, fill = (0, 0, 0)) for area in areas]
                 
            # applying the redaction
            page.apply_redactions()
             
        # saving it to a new pdf
        doc.save('newPDF.pdf')
        print("Successfully redacted")
 
# driver code for testing
if __name__ == "__main__":
   
    # replace it with name of the pdf file
    path = "PDFtoredact.pdf"
    redactor = Redactor(path)
    redactor.redaction()