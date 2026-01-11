from pyhanko.sign import signers, fields
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign.fields import SigSeedSubFilter

def sign_pdf(input_path, output_path, pfx_path, password):
    """
    Sign a PDF using a PFX/P12 certificate.
    
    Args:
        input_path (str): Path to the input PDF.
        output_path (str): Path to save the signed PDF.
        pfx_path (str): Path to the .p12/.pfx certificate file.
        password (str): Password for the certificate.
    """
    signer = signers.SimpleSigner.load_pkcs12(
        pfx_file=pfx_path,
        passphrase=password.encode() if password else None
    )
    
    with open(input_path, 'rb') as inf:
        w = IncrementalPdfFileWriter(inf)
        fields.append_signature_field(
            w, fields.SigFieldSpec(sig_field_name='Signature1')
        )
        
        with open(output_path, 'wb') as outf:
            signers.sign_pdf(
                w, signers.PdfSignatureMetadata(field_name='Signature1'),
                signer=signer, output=outf,
            )
