import os
import sys
import pandas as pd
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QTextDocument, QPageSize
from PyQt6.QtPrintSupport import QPrinter
from utils.audit_log import audit_logger

# For COM
try:
    import comtypes.client
    COM_AVAILABLE = True
except ImportError:
    COM_AVAILABLE = False

def convert_excel_to_pdf(input_path, output_path):
    """
    Convert Excel to PDF using Pandas and PyQt6.
    """
    try:
        # Read Excel
        dfs = pd.read_excel(input_path, sheet_name=None)
        
        # Convert to HTML
        html_content = """
        <html>
        <head>
            <style>
                table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
                th, td { border: 1px solid black; padding: 5px; text-align: left; font-size: 10pt; }
                h1 { font-size: 14pt; color: #333; }
            </style>
        </head>
        <body>
        """
        
        for sheet_name, df in dfs.items():
            html_content += f"<h1>{sheet_name}</h1>"
            # Limit rows for safety? Or just dump all. 
            # If huge, this will hang.
            html_content += df.to_html(index=False, na_rep="")
            html_content += "<br>"
        
        html_content += "</body></html>"
        
        # Use Qt to print
        # Note: This typically needs to run on the main thread if it interacts with the event loop,
        # but QTextDocument is somewhat standalone. However, QApplication must exist.
        if not QApplication.instance():
            # This should not happen in the full app, but for standalone testing
             _ = QApplication(sys.argv)
        
        doc = QTextDocument()
        doc.setHtml(html_content)
        
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(output_path)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        
        doc.print(printer)
        
        audit_logger.log_event("excel_to_pdf", {"input": input_path, "output": output_path})
        return True, "Converted Excel to PDF successfully."
        
    except Exception as e:
        return False, str(e)

def convert_ppt_to_pdf(input_path, output_path):
    """
    Convert PowerPoint to PDF using Office COM automation (Windows only).
    """
    if not COM_AVAILABLE:
        return False, "comtypes library not installed."
        
    if sys.platform != 'win32':
        return False, "PowerPoint conversion only supported on Windows with Office installed."
        
    try:
        # Initialize COM
        comtypes.CoInitialize()
        
        powerpoint = comtypes.client.CreateObject("Powerpoint.Application")
        # powerpoint.Visible = 1 
        
        abs_input = os.path.abspath(input_path)
        abs_output = os.path.abspath(output_path)
        
        # Open read-only, no window
        deck = powerpoint.Presentations.Open(abs_input, WithWindow=False)
        deck.SaveAs(abs_output, 32) # 32 = ppSaveAsPDF
        deck.Close()
        powerpoint.Quit()
        
        audit_logger.log_event("ppt_to_pdf", {"input": input_path, "output": output_path})
        return True, "Converted PowerPoint to PDF successfully."
    except Exception as e:
        return False, f"PowerPoint conversion failed (Ensure Microsoft Office is installed): {str(e)}"
    finally:
         comtypes.CoUninitialize()

def convert_word_to_pdf(input_path, output_path):
    """
    Convert Word to PDF using Office COM automation (Windows only).
    """
    if not COM_AVAILABLE:
        return False, "comtypes library not installed."
        
    if sys.platform != 'win32':
        return False, "Word conversion only supported on Windows with Office installed."
        
    try:
        # Initialize COM
        comtypes.CoInitialize()
        
        word = comtypes.client.CreateObject("Word.Application")
        # word.Visible = False
        
        abs_input = os.path.abspath(input_path)
        abs_output = os.path.abspath(output_path)
        
        doc = word.Documents.Open(abs_input)
        doc.SaveAs(abs_output, 17) # 17 = wdFormatPDF
        doc.Close()
        word.Quit()
        
        audit_logger.log_event("word_to_pdf", {"input": input_path, "output": output_path})
        return True, "Converted Word to PDF successfully."
    except Exception as e:
        return False, f"Word conversion failed (Ensure Microsoft Office is installed): {str(e)}"
    finally:
         comtypes.CoUninitialize()

def convert_office_to_pdf(input_path, output_path):
    ext = os.path.splitext(input_path)[1].lower()
    if ext in ['.xlsx', '.xls']:
        return convert_excel_to_pdf(input_path, output_path)
    elif ext in ['.pptx', '.ppt']:
        return convert_ppt_to_pdf(input_path, output_path)
    elif ext in ['.docx', '.doc']:
        return convert_word_to_pdf(input_path, output_path)
    else:
        return False, "Unsupported file format."
