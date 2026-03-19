#!/usr/bin/env python3
"""
Script para probar la autenticación con Circulo de Crédito API
Usa ECDSA con secp384r1 para generar firmas
"""

import requests
import base64
import json
import uuid
from datetime import datetime
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend

# Configuración
API_KEY = "RDQpKk92ufPp3vaZzTJ9NTmGRNlgARmk"
BASE_URL = "https://services.circulodecredito.com.mx/sandbox/v1"
# Intentar con el endpoint de validación de identidad
SECURITY_TEST_ENDPOINT = f"{BASE_URL}/identityData/identity-data/validations"

# Clave privada (formateada)
PRIVATE_KEY_B64 = "MIG2AgEAMBAGByqGSM49AgEGBSuBBAAiBIGeMIGbAgEBBDBycqpcOuhO2WfmR5MHlIW49SERWZMf0nvjzzAzyuoY/Bw49C9seDl0rkWpXcGsQxihZANiAATbw3BYH/O/XJ3Ombf6MjfbXe6gx4pwI7csu7OMJvWhxozxudLAHLWX9K/qmmJfV4Cs/sOH/4noCDeaFzRV/X4WmtAaDQgAtDKWB6GwoQJcnzglxKUptHxL6pZ3PHZSAP8="

def generate_signature(payload_str, private_key_b64):
    """
    Genera firma ECDSA-SHA256 del payload usando la clave privada
    """
    try:
        # Decodificar clave privada de base64
        private_key_der = base64.b64decode(private_key_b64)
        
        # Cargar la clave privada
        private_key = serialization.load_der_private_key(
            private_key_der,
            password=None,
            backend=default_backend()
        )
        
        # Generar firma
        signature = private_key.sign(
            payload_str.encode('utf-8'),
            ec.ECDSA(hashes.SHA256())
        )
        
        # Codificar firma en base64
        signature_b64 = base64.b64encode(signature).decode('utf-8')
        return signature_b64
    except Exception as e:
        print(f"❌ Error generando firma: {e}")
        return None

def test_security_endpoint():
    """
    Prueba el endpoint de validación de identidad (RENAPO)
    """
    print("=" * 70)
    print("🔐 PRUEBA DE AUTENTICACIÓN - CIRCULO DE CRÉDITO API")
    print("=" * 70)
    print()
    
    # Payload para RENAPO con todos los campos requeridos
    request_id = str(uuid.uuid4())
    payload = {
        "requestId": request_id,
        "referencia": "001",  # Solo dígitos
        "infoProvider": "RENAPO",  # Debe ser string: RENAPO, INE, SEP, DEBUG
        "curp": "MERE020526HMNRZDA2"  # CURP de prueba
    }
    payload_str = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
    
    print(f"📤 Endpoint: {SECURITY_TEST_ENDPOINT}")
    print(f"📋 Payload: {payload_str}")
    print()
    
    # Generar firma
    print("🔑 Generando firma ECDSA-SHA256...")
    signature = generate_signature(payload_str, PRIVATE_KEY_B64)
    
    if not signature:
        print("❌ No se pudo generar la firma")
        return False
    
    print(f"✅ Firma generada correctamente")
    print(f"   Longitud: {len(signature)} caracteres")
    print()
    
    # Headers
    headers = {
        "x-api-key": API_KEY,
        "x-signature": signature,
        "Content-Type": "application/json"
    }
    
    print("📡 Enviando request...")
    print(f"   Headers: x-api-key={API_KEY[:10]}..., x-signature={signature[:20]}...")
    print()
    
    try:
        response = requests.post(
            SECURITY_TEST_ENDPOINT,
            json=payload,
            headers=headers,
            timeout=10
        )
        
        print(f"📨 Response Status: {response.status_code}")
        print(f"📨 Response Headers: {dict(response.headers)}")
        print()
        
        try:
            response_data = response.json()
            print(f"📨 Response Body:")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
        except:
            print(f"📨 Response Body (texto): {response.text}")
        
        print()
        
        if response.status_code == 200:
            print("✅ ¡AUTENTICACIÓN EXITOSA!")
            print("   Las credenciales y firma están configuradas correctamente.")
            return True
        else:
            print(f"⚠️  Response code {response.status_code}")
            if response.status_code == 401:
                print("   Error de autenticación. Verifica las credenciales.")
            elif response.status_code == 403:
                print("   Error de autorización.")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Timeout: La solicitud tardó demasiado tiempo")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Error de conexión: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_security_endpoint()
    exit(0 if success else 1)
