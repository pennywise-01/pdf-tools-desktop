import pdfplumber
import pandas as pd
from utils.audit_log import audit_logger

def convert_pdf_to_excel(input_path, output_path):
    """
    Convert a PDF into a Microsoft Excel (`.xlsx`) file, detecting and reconstructing tables.
    """
    try:
        with pdfplumber.open(input_path) as pdf:
            with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
                found_tables = False
                for i, page in enumerate(pdf.pages):
                    tables = page.extract_tables()
                    for j, table in enumerate(tables):
                        found_tables = True
                        df = pd.DataFrame(table)
                        # Clean up None values
                        df = df.fillna('')
                        
                        sheet_name = f"Page_{i+1}_Table_{j+1}"
                        # Truncate sheet name to 31 chars as per Excel limit
                        sheet_name = sheet_name[:31]
                        
                        df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
                
                if not found_tables:
                    # Provide a fallback or user message inside the excel? 
                    # Or just fail? 
                    # Let's write text if no tables?
                    # Plan asks specifically for tables.
                    pass
        
        if not found_tables:
            return False, "No structured tables detected in the PDF."

        audit_logger.log_event("pdf_to_excel", {"input": input_path, "output": output_path})
        return True, "Converted to Excel successfully. Tables saved to separate sheets."
    except Exception as e:
        return False, str(e)
