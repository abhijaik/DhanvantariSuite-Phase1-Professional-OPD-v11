"""
Dhanvantari Clinic ERP - SSL/TLS Certificate Generator
Generates high-security self-signed TLS 1.3/1.2 certificates for local and LAN HTTPS deployment.
Complies with HIPAA Technical Safeguards (45 CFR § 164.312(e)(1) - Transmission Security).
"""
import os
import sys
import datetime
from pathlib import Path
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import ipaddress

def generate_self_signed_cert(
    cert_dir: str = "certs",
    cert_name: str = "clinic_cert.pem",
    key_name: str = "clinic_key.pem",
    days_valid: int = 365,
    common_name: str = "localhost"
):
    out_dir = Path(cert_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    cert_path = out_dir / cert_name
    key_path = out_dir / key_name
    
    if cert_path.exists() and key_path.exists():
        print(f"[INFO] Existing SSL certificates found at:\n  Cert: {cert_path}\n  Key:  {key_path}")
        return str(cert_path), str(key_path)

    print("[INFO] Generating high-entropy 2048-bit RSA private key...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    print("[INFO] Generating X.509 v3 certificate with TLS 1.3 / SAN support...")
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "IN"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Maharashtra"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Dhanvantari Clinic ERP"),
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])

    alt_names = [
        x509.DNSName("localhost"),
        x509.DNSName("*.localhost"),
        x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
        x509.IPAddress(ipaddress.IPv4Address("0.0.0.0")),
    ]

    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=days_valid))
        .add_extension(
            x509.SubjectAlternativeName(alt_names),
            critical=False,
        )
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        )
        .sign(private_key, hashes.SHA256())
    )

    # Save private key
    with open(key_path, "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    # Save certificate
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print(f"[SUCCESS] TLS Certificates created successfully:\n  Cert: {cert_path}\n  Key:  {key_path}")
    return str(cert_path), str(key_path)

if __name__ == "__main__":
    generate_self_signed_cert()
