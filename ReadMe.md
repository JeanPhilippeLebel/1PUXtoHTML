# 1Password backup (1PUX) to HTML

This is a simple Python script to convert a 1Password export file (.1pux) to a printer-friendly HTML document.

# Features

- Printer-friendly HTML document
- Embedded images directly within the document
- All "Vaults" are exported
- Support all the data, including images and PDF (PDF will be converted to PNG on the fly)

# Requirements

- Python 3.8+
- jinja2 (Templating engine)
- fitz (PDF to png)

# Licence and inspiration

This tool is a mashup of these two scripts:

https://github.com/ShayBox/OnePasswordConverter
https://github.com/TechJosh/1PUXtoChromeCSV/blob/main/1PUXtoChromeCSV.py

Since one of the two is GPL3, this code must use GPL3 as well.