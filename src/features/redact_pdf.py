import fitz
import re

def redact_pdf(input_path, output_path, sensitive_text, match_case=False, redact_numbers=False, color=(0, 0, 0), preview_mode=False):
    """
    Redacts or highlights occurrences of sensitive_text in the PDF.
    
    Args:
        input_path (str): Path to input PDF.
        output_path (str): Path to save processed PDF.
        sensitive_text (str): The text to search for. Can be comma-separated.
        match_case (bool): Whether search should be case-sensitive.
        redact_numbers (bool): Whether to mask all numeric words/ids.
        color (tuple): RGB tuple (0-1) for the redaction fill.
        preview_mode (bool): If True, applies Yellow highlights instead of Redactions and does not burn.
    """
    doc = fitz.open(input_path)
    
    search_terms = []
    if sensitive_text:
        if "," in sensitive_text:
            search_terms = [term.strip() for term in sensitive_text.split(",") if term.strip()]
        else:
            if sensitive_text.strip():
                search_terms = [sensitive_text.strip()]
    
    # Flags for search_for - We will use post-filtering for reliability across versions
    # flags = 0 means case-insensitive usually
    
    found_any = False
    
    for page in doc:
        rects_to_process = []
        
        # 1. Search for specific text terms
        for term in search_terms:
            # Search is case-insensitive by default in many versions or with flags=0
            # We get ALL matches (case insensitive), then filter if needed
            text_instances = page.search_for(term)
            
            if match_case:
                # Filter strictly
                strict_instances = []
                for rect in text_instances:
                    # Clip text from the found rectangle
                    # We expand it slightly to ensure we catch edges or if font renders weirdly?
                    # Actually standard rect usually finds the text content.
                    # Use "text" output.
                    extracted = page.get_text("text", clip=rect).strip()
                    if term in extracted:
                        strict_instances.append(rect)
                rects_to_process.extend(strict_instances)
            else:
                rects_to_process.extend(text_instances)
            
        # 2. Search for numbers if requested (using words approach for simplicity)
        if redact_numbers:
            # get_text("words") returns list of (x0, y0, x1, y1, "word", block_no, line_no, word_no)
            words = page.get_text("words")
            for w in words:
                text_content = w[4]
                # Check if text contains digits (e.g. "ID:123456" or "123")
                # Using regex to see if it has at least one digit is a broad but safe interpretation 
                # for "anything like id number etc".
                # However, users might not want to redact "Page 1".
                # A common heuristic for "sensitive numbers" is usually:
                # - Pure digits (12345)
                # - Mix of digits and dashes/symbols (123-456)
                # Let's check if it contains a digit.
                if any(char.isdigit() for char in text_content):
                     rects_to_process.append(fitz.Rect(w[0], w[1], w[2], w[3]))

        # Process found rectangles
        if rects_to_process:
            found_any = True
            for rect in rects_to_process:
                if preview_mode:
                    # Add Highlight text annotation (Yellow)
                    annot = page.add_highlight_annot(rect)
                    annot.set_colors(stroke=(1, 1, 0)) # Yellow
                    annot.update()
                else:
                    # Add Redaction annotation
                    page.add_redact_annot(rect, fill=color)
        
        # Apply redactions if not preview mode
        if not preview_mode and rects_to_process:
            page.apply_redactions()
            
    doc.save(output_path)
    doc.close()
    
    return found_any
