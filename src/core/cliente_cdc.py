#!/usr/bin/env python3
"""
Cliente API para Circulo de Crédito Identity Data Service
Valida CURPS en contra de RENAPO (Registro Nacional de Población)
"""

import requests
import base64
import json
import uuid
from typing import Dict, Optional, Tuple
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend


class CirculoDeCredito:
    """Cliente para consultar datos de identidad en Circulo de Crédito"""
    
    def __init__(
        self, 
        api_key: str,
        private_key_b64: str,
        base_url: str = "https://services.circulodecredito.com.mx/sandbox/v1"
    ):
        """
        Inicializa el cliente de Circulo de Crédito
        
        Args:
            api_key: Consumer Key obtenida del portal
            private_key_b64: Clave privada en base64
            base_url: URL base del API (sandbox por defecto)
        """
        self.api_key = api_key
        self.private_key_b64 = private_key_b64
        self.base_url = base_url
        self.endpoint = f"{base_url}/identityData/identity-data/validations"
        
    def _generate_signature(self, payload_str: str) -> Optional[str]:
        """Genera firma ECDSA-SHA256 del payload"""
        try:
            private_key_der = base64.b64decode(self.private_key_b64)
            private_key = serialization.load_der_private_key(
                private_key_der,
                password=None,
                backend=default_backend()
            )
            signature = private_key.sign(
                payload_str.encode('utf-8'),
                ec.ECDSA(hashes.SHA256())
            )
            return base64.b64encode(signature).decode('utf-8')
        except Exception as e:
            print(f"Error generando firma: {e}")
            return None
    
    def validate_curp(
        self, 
        curp: str,
        reference: str = "001",
        info_provider: str = "RENAPO"
    ) -> Tuple[bool, Dict]:
        """
        Valida un CURP contra RENAPO
        
        Args:
            curp: CURP a validar
            reference: Referencia de la transacción (solo dígitos)
            info_provider: Proveedor de información (RENAPO, INE, SEP, DEBUG)
            
        Returns:
            Tupla (éxito, datos_respuesta)
        """
        # Construir payload
        payload = {
            "requestId": str(uuid.uuid4()),
            "referencia": reference,
            "infoProvider": info_provider,
            "curp": curp
        }
        payload_str = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
        
        # Generar firma
        signature = self._generate_signature(payload_str)
        if not signature:
            return False, {"error": "No se pudo generar la firma"}
        
        # Headers
        headers = {
            "x-api-key": self.api_key,
            "x-signature": signature,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                self.endpoint,
                data=payload_str,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                result = {
                    "exitoso": True,
                    "codigo": data.get("code"),
                    "mensaje": data.get("message"),
                    "datos": data.get("data", {})
                }
                return True, result
            else:
                return False, {
                    "exitoso": False,
                    "status_code": response.status_code,
                    "respuesta": response.json() if response.headers.get('content-type') == 'application/json' else response.text
                }
        except requests.exceptions.Timeout:
            return False, {"error": "Timeout: La solicitud tardó demasiado"}
        except requests.exceptions.ConnectionError as e:
            return False, {"error": f"Error de conexión: {e}"}
        except Exception as e:
            return False, {"error": f"Error inesperado: {e}"}
    
    def extract_data(self, response: Dict) -> Optional[Dict]:
        """Extrae datos de la respuesta de RENAPO"""
        try:
            if not response.get("exitoso"):
                return None
            
            datos = response.get("datos", {})
            resultado_curp = datos.get("respuestaRENAPO", {}).get("CURPStatus", {}).get("resultCURPS", {})
            
            # Detectar si es datos de prueba/dummy
            curp_retornado = resultado_curp.get("CURP", "")
            es_datos_prueba = curp_retornado.startswith("PRUEBA")
            
            return {
                "curp": resultado_curp.get("CURP"),
                "apellidoPaterno": resultado_curp.get("apellidoPaterno"),
                "apellidoMaterno": resultado_curp.get("apellidoMaterno"),
                "nombres": resultado_curp.get("nombres"),
                "sexo": resultado_curp.get("sexo"),
                "fechaNacimiento": resultado_curp.get("fechNac"),
                "nacionalidad": resultado_curp.get("nacionalidad"),
                "entidadNacimiento": resultado_curp.get("cveEntidadNac"),
                "statusCurp": resultado_curp.get("statusCurp"),
                "es_datos_prueba": es_datos_prueba  # Indicador de datos dummy
            }
        except Exception as e:
            print(f"Error extrayendo datos: {e}")
            return None


# Configuración
API_KEY = "RDQpKk92ufPp3vaZzTJ9NTmGRNlgARmk"
PRIVATE_KEY_B64 = "MIG2AgEAMBAGByqGSM49AgEGBSuBBAAiBIGeMIGbAgEBBDBycqpcOuhO2WfmR5MHlIW49SERWZMf0nvjzzAzyuoY/Bw49C9seDl0rkWpXcGsQxihZANiAATbw3BYH/O/XJ3Ombf6MjfbXe6gx4pwI7csu7OMJvWhxozxudLAHLWX9K/qmmJfV4Cs/sOH/4noCDeaFzRV/X4WmtAaDQgAtDKWB6GwoQJcnzglxKUptHxL6pZ3PHZSAP8="


if __name__ == "__main__":
    # Crear cliente
    client = CirculoDeCredito(API_KEY, PRIVATE_KEY_B64)
    
    # Prueba con CURP
    print("=" * 70)
    print("🔍 VALIDANDO CURP CON RENAPO")
    print("=" * 70)
    print()
    
    curp = "MERE020526HMNRZDA2"
    print(f"CURP a validar: {curp}")
    print()
    
    exitoso, respuesta = client.validate_curp(curp)
    
    print(f"Resultado: {'✅ EXITOSO' if exitoso else '❌ FALLIDO'}")
    print()
    print("Respuesta completa:")
    print(json.dumps(respuesta, indent=2, ensure_ascii=False))
    print()
    
    if exitoso:
        datos = client.extract_data(respuesta)
        if datos:
            print("=" * 70)
            print("📋 DATOS EXTRAÍDOS:")
            print("=" * 70)
            for clave, valor in datos.items():
                print(f"  {clave:20} : {valor}")
