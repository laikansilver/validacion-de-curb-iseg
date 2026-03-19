#!/usr/bin/env python3
"""Genera par de llaves ECDSA secp384r1 para firmar peticiones a CirculoDeCrédito."""

import os
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec


def generate_keys(output_dir: str = ".") -> None:
    """Genera par de llaves privada/pública en formato PEM."""
    print("Generando par de llaves ECDSA (secp384r1)...\n")

    # Generar llave privada
    private_key = ec.generate_private_key(ec.SECP384R1(), default_backend())

    # Generar certificado autofirmado
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from datetime import datetime, timedelta

    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, u"MX"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"CDMX"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, u"Mexico"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"CDC"),
            x509.NameAttribute(NameOID.COMMON_NAME, u"CDC"),
        ]
    )

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=365))
        .sign(private_key, hashes.SHA256(), default_backend())
    )

    # Guardar llave privada
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pri_key_path = os.path.join(output_dir, "pri_key.pem")
    with open(pri_key_path, "wb") as f:
        f.write(private_pem)
    print(f"✓ Llave privada: {pri_key_path}")

    # Guardar certificado (llave pública)
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    cert_path = os.path.join(output_dir, "certificate.pem")
    with open(cert_path, "wb") as f:
        f.write(cert_pem)
    print(f"✓ Certificado (llave pública): {cert_path}\n")

    # Extraer valores para Postman (sin dos puntos ni saltos de línea)
    print("=" * 70)
    print("VALORES PARA POSTMAN/CODIGO")
    print("=" * 70 + "\n")

    # Private key en formato para variable
    private_key_value = private_key.private_numbers()
    private_key_hex = hex(private_key_value.private_value)[2:].zfill(96)  # 384 bits = 96 hex chars
    print("1. Variable 'private_key' (sin dos puntos ni saltos de linea):")
    print(f"   {private_key_hex}\n")

    # Public key en formato para variable
    public_key = private_key.public_key()
    public_key_value = public_key.public_numbers()
    x_hex = hex(public_key_value.x)[2:].zfill(96)
    y_hex = hex(public_key_value.y)[2:].zfill(96)
    public_key_hex = "04" + x_hex + y_hex  # Formato no comprimido
    print("2. Variable 'cdc_public_key' (sin dos puntos ni saltos de linea):")
    print(f"   {public_key_hex}\n")

    print("=" * 70)
    print("INSTRUCCIONES")
    print("=" * 70)
    print("""
1. Copia el certificado (certificate.pem) a tu aplicación en API HUB:
   - Ve a https://developer.circulodecredito.com.mx/
   - Mi cuenta/Apps → Tu app → Certificados
   - Carga certificate.pem

2. En tu código/ambiente, usa:
   - private_key: [valor de arriba]
   - cdc_public_key: [valor de arriba]

3. El script validador_curp.py ya soporta firma automática:
   python validador_curp.py --curp TU_CURP \\
     --cdc \\
     --cdc-base-url "https://services.circulodecredito.com.mx/sandbox/v1/identityData" \\
     --cdc-api-key "RDQpKk92ufPp3vaZzTJ9NTmGRNlgARmk" \\
     --cdc-username "NO_NECESARIO_SANDBOX" \\
     --cdc-password "NO_NECESARIO_SANDBOX" \\
     --cdc-auto-sign \\
     --cdc-private-key "[valor-private-key-de-arriba]"
    """)


if __name__ == "__main__":
    generate_keys()
