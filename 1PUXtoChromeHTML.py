# Python 3.8+

import json, sys, getopt
from zipfile import ZipFile
from time import strftime, localtime
import jinja2 #Template engine
import base64
import os

#pip install PyMuPDF
import fitz # imports the pymupdf library

class line:
    def __init__(self, name, url, username, password, note, otherfields):
        self.name = name
        self.url = url
        self.username = username
        self.password = password
        self.note = note
        self.otherfields = otherfields
    def __str__(self):
        return 'name:%s, url:%s, username:%s, password:%s, note:%s' % (self.name, self.url, self.username, self.password, self.note)

def readFile(ifile, verbose):
    with ZipFile(ifile) as file:
        #load all the "files"
        filelist = {}
        for filename in file.namelist():
            if filename.startswith("files/"):
                with file.open(filename) as binfile:
                    filelist[filename.replace("files/", "")] = binfile.read()
                
        with file.open("export.data") as dfile:
            json_file = dfile.read()

    return readJSON(json_file, filelist, verbose)

def readJSON(file_data: str, filelist, verbose):
    data = json.loads(file_data)

    list = {}

    for account in data["accounts"]:
        print(f"Processing account: {account['attrs']['name']}")

        for vault in account["vaults"]:
            folder = vault["attrs"]["name"]
            print(f"Processing folder: {folder}")
            
            for item in vault["items"]:

                # 1Password sometimes puts items inside an object with duplicated keys
                #if "item" in vault["items"][0]:
                #    iterable = vault.items[0].values()

                #for item in iterable:
                if verbose:
                    print(item)
                    print("\033[93mWARNING! This is verbose output!\033[0m")
                    print("\033[93mThere may be private information in this output!\033[0m")
                    print("\033[93mRemove any sensitive information before sharing!\033[0m")

                # Root level items
                favorite = item["favIndex"] if "favIndex" in item else 0

                # Overview Subsection
                if "overview" not in item:
                    print("\033[93mWARNING! Overview is empty! Skipping item\033[0m")
                    continue

                overview = item["overview"]
                name = overview["title"] if "title" in overview else ""
                login_uri = overview["url"] if "url" in overview else ""

                # Details Subsection
                details = item["details"] if "details" in item else {}
                notes = details["notesPlain"] if "notesPlain" in details else ""
                notes.replace("\n", "<br>")


                login_username, login_password = "", ""
                for field in details["loginFields"]:
                    if "designation" not in field:
                        continue
                    if field["designation"] == "username":
                        login_username = field["value"]
                    if field["designation"] == "password":
                        login_password = field["value"]

                otherfields = []
                for section in details["sections"]:
                    fields = section["fields"]
                    if len(fields) == 0:
                        continue
                    for field in fields:
                        value = field["value"]
                        if "totp" in value:
                            otherfields.append((field["title"], "totp", value["totp"])) 
                        elif "file" in value:
                            #load image from disk and save the base64 content to create a self contained html file
                            #
                            filename = value["file"]['documentId'] + '__' + value["file"]['fileName']

                            if filename in filelist:
                                file_name, file_extension = os.path.splitext(filename)

                                #Check for PDF, if so, convert to png
                                if file_extension == ".pdf":
                                    file_extension = ".png"

                                    doc = fitz.open("pdf", filelist[filename])

                                    page = doc.load_page(0)
                                    pix = page.get_pixmap()
                                    filelist[filename] = pix.tobytes(output='png')
                                    
                                    doc.close()

                                otherfields.append((field["title"],"file", str(base64.b64encode(bytes(filelist[filename])), 'UTF-8'), file_extension.replace('.', '')))
                            else:
                                print(f"Could not find file in loaded file list: {filename}")
                        elif "date" in value:
                            otherfields.append((field["title"],"date", strftime('%Y-%m-%d %H:%M:%S', localtime(value["date"])))) 
                        elif "email" in value:
                            otherfields.append((field["title"],"email_address", value["email"]["email_address"]))
                        elif "concealed" in value:
                            otherfields.append((field["title"],"", value["concealed"]))
                        elif "address" in value:
                            otherfields.append((field["title"],"address", value["address"]["street"] + ', ' + value["address"]["city"] + ', ' + value["address"]["country"] + ', ' + value["address"]["zip"] + ', ' + value["address"]["state"]))
                            continue
                        elif "phone" in value:
                            otherfields.append((field["title"],"phone", value["phone"]))
                        elif "url" in value:
                            otherfields.append((field["title"],"url", value["url"]))
                        else: 
                            otherfields.append((field["title"],"string", value["string"]))

                if name != None:
                    if folder in list:
                        list[folder].append(line(name, login_uri, login_username, login_password, notes, otherfields))
                    else :
                        list[folder] = []
                        list[folder].append(line(name, login_uri, login_username, login_password, notes, otherfields))
                        
    return list

def writeHLML(lst, file, verbose):

    results_filename = "OutputTemplate.in.html"
    templateLoader = jinja2.FileSystemLoader(searchpath="./")
    templateEnv = jinja2.Environment(loader=templateLoader)
    results_template = templateEnv.get_template(results_filename)

    test_name = "Python Challenge"

    context = {
        "items": lst,
        "vault_name": test_name,
    }

    with open(file, mode="w", encoding="utf-8") as results:
        results.write(results_template.render(context))
        print(f"... wrote {file}")

def main(argv):
    inputfile = ''
    outputfile = ''
    verbose = False

    try:
        acount = len(argv)
        if acount < 4:
            raise getopt.GetoptError("invalid arguments")
        opts, args = getopt.getopt(argv, "i:o:v", ["ifile", "ofile", "verbose"])
    except getopt.GetoptError:
        print("1PUXtoChromeCSV -i <inputfile> -o <outputfile> [-v]")
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg
        elif opt in ("-v", "--verbose"):
            verbose = True
    
    if verbose == True:
        print("Reading %s" % (inputfile))

    inputdata = readFile(inputfile, verbose)

    if verbose == True:
        for line in inputdata:
            print(line)

    print("%i records imported" % (len(inputdata)))

    if verbose == True:
        print("Writing %s" % (outputfile))

    writeHLML(inputdata, outputfile, verbose)

    print ("%i records saved")
    

if __name__ == "__main__":
    main(sys.argv[1:])
