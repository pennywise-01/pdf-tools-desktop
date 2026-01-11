import uuid
from PyQt6.QtWidgets import QMessageBox, QApplication

def show_error_dialog(parent, message, detail=None, prefix="ERR"):
    """
    Displays an error dialog with a unique error code and a copy button.
    
    Args:
        parent: The parent widget.
        message: The main error message to display.
        detail: Technical details or traceback (optional).
        prefix: A short string prefix for the error code (e.g., 'MRG' for Merge).
    """
    # Generate a unique error code
    unique_id = uuid.uuid4().hex[:6].upper()
    error_code = f"{prefix}-{unique_id}"
    
    full_text = f"Error Code: {error_code}\n\nMessage:\n{message}"
    if detail:
        full_text += f"\n\nDetails:\n{detail}"
        
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Icon.Critical)
    msg_box.setWindowTitle(f"Error {error_code}")
    msg_box.setText(f"An error occurred.")
    msg_box.setInformativeText(f"{message}\n\nCode: {error_code}")
    
    if detail:
        msg_box.setDetailedText(detail)
        
    # Add Copy Button
    copy_btn = msg_box.addButton("Copy Error", QMessageBox.ButtonRole.ActionRole)
    msg_box.addButton(QMessageBox.StandardButton.Ok)
    
    msg_box.exec()
    
    if msg_box.clickedButton() == copy_btn:
        clipboard = QApplication.clipboard()
        clipboard.setText(full_text)
        QMessageBox.information(parent, "Copied", "Error details copied to clipboard.")
