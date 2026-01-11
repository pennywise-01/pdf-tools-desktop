import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography import x509
from cryptography.x509.oid import NameOID
import datetime
import os
from src.features.sign_pdf import sign_pdf
import fitz

@pytest.fixture
def create_dummy_pfx(tmp_path):
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"California"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u"San Francisco"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"My Company"),
        x509.NameAttribute(NameOID.COMMON_NAME, u"mysite.com"),
    ])
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.now(datetime.timezone.utc)
    ).not_valid_after(
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=10)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
        critical=False,
    ).sign(key, hashes.SHA256())

    pfx_path = tmp_path / "test.pfx"
    password = b"password"
    
    p12 = serialization.pkcs12.serialize_key_and_certificates(
        b"test",
        key,
        cert,
        None,
        serialization.BestAvailableEncryption(password)
    )
    with open(pfx_path, "wb") as f:
        f.write(p12)
        
    return str(pfx_path), "password"

@pytest.fixture
def create_dummy_pdf(tmp_path):
    pdf_path = tmp_path / "test.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Hello, World!")
    doc.save(str(pdf_path))
    doc.close()
    return str(pdf_path)

def test_sign_pdf(create_dummy_pdf, create_dummy_pfx, tmp_path):
    pfx_path, password = create_dummy_pfx
    output_path = tmp_path / "signed.pdf"
    
    sign_pdf(create_dummy_pdf, str(output_path), pfx_path, password)
    
    assert os.path.exists(output_path)
    
    # Verify signature existence
    doc = fitz.open(output_path)
    # get_sigflags returns integer. 1 = signatures exist, 3 = signatures exist and append-only
    assert doc.get_sigflags() > 0 
    doc.close()
