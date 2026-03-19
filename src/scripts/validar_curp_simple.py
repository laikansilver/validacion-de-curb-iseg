#!/usr/bin/env python3
"""
Wrapper simplificado para validar CURPs contra RENAPO
Usa la configuración de config/config_cdc.json
"""

import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
from cliente_cdc import CirculoDeCredito


def load_config(config_file: str = "config/config_cdc.json") -> dict:
    """Carga la configuración desde JSON"""
    config_path = Path(config_file)
    if not config_path.exists():
        # Intentar desde la raíz del proyecto
        config_path = Path(__file__).parent.parent.parent / config_file
    if not config_path.exists():
        print(f"Error: No se encontró {config_file}")
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        return json.load(f)


def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print("Uso: python validar_curp_simple.py <CURP>")
        print()
        print("Ejemplo:")
        print("  python validar_curp_simple.py MERE020526HMNRZDA2")
        sys.exit(1)
    
    curp = sys.argv[1].upper()
    
    # Validación básica de formato CURP
    if len(curp) != 18:
        print(f"❌ CURP debe tener 18 caracteres. Recibido: {len(curp)}")
        sys.exit(1)
    
    # Cargar configuración
    config = load_config()
    cdc_config = config.get("cdc", {})
    
    # Crear cliente
    client = CirculoDeCredito(
        api_key=cdc_config.get("api_key"),
        private_key_b64=cdc_config.get("private_key_b64"),
        base_url=cdc_config.get("base_url")
    )
    
    # Validar
    print("=" * 70)
    print("🔍 VALIDANDO CURP CONTRA RENAPO")
    print("=" * 70)
    print()
    print(f"CURP: {curp}")
    print()
    
    exitoso, respuesta = client.validate_curp(curp)
    
    if not exitoso:
        print(f"❌ Error: {respuesta.get('error', respuesta)}")
        sys.exit(1)
    
    # Extraer datos
    datos = client.extract_data(respuesta)
    
    if not datos or not datos.get("curp"):
        print("❌ El CURP no fue encontrado en RENAPO")
        print()
        print("Respuesta completa:")
        print(json.dumps(respuesta, indent=2, ensure_ascii=False))
        sys.exit(1)
    
    # Mostrar resultados
    print("✅ ¡CURP VÁLIDO Y ENCONTRADO EN RENAPO!")
    print()
    print("=" * 70)
    print("📋 DATOS DEL REGISTRO:")
    print("=" * 70)
    
    for clave, valor in datos.items():
        etiqueta = {
            "curp": "CURP",
            "apellidoPaterno": "Apellido Paterno",
            "apellidoMaterno": "Apellido Materno",
            "nombres": "Nombres",
            "sexo": "Sexo",
            "fechaNacimiento": "Fecha de Nacimiento",
            "nacionalidad": "Nacionalidad",
            "entidadNacimiento": "Entidad de Nacimiento",
            "statusCurp": "Estado CURP"
        }.get(clave, clave)
        
        print(f"  {etiqueta:25} : {valor}")
    
    print()
    print("=" * 70)
    sys.exit(0)


if __name__ == "__main__":
    main()
