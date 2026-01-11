from pikepdf import Pdf, Encryption, Permissions

def encrypt_pdf(input_path, output_path, password, permissions, encryption_level):
    """
    Encrypts a PDF file.

    Args:
        input_path (str): The path to the input PDF file.
        output_path (str): The path to save the encrypted PDF file.
        password (str): The password to lock the PDF.
        permissions (dict): A dictionary of permissions to apply.
        encryption_level (int): The encryption level (128 or 256).
    """
    
    perm = Permissions(
        print_highres=permissions.get('print', False),
        extract=permissions.get('copy', False),
        modify_assembly=permissions.get('modify', False),
    )

    if encryption_level == 256:
        enc = Encryption(
            user=password,
            owner=password,
            R=6, # AES-256
            allow=perm
        )
    else: # 128 bit
        enc = Encryption(
            user=password,
            owner=password,
            R=4, # AES-128
            allow=perm
        )

    with Pdf.open(input_path) as pdf:
        pdf.save(
            output_path,
            encryption=enc
        )