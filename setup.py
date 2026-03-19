#!/usr/bin/env python3
"""
Script de configuración inicial del proyecto
Ayuda a preparar el entorno para usar el validador de CURP
"""

import json
import sys
from pathlib import Path


def check_structure():
    """Verifica que la estructura del proyecto esté correcta"""
    print("=" * 70)
    print("🔍 VERIFICANDO ESTRUCTURA DEL PROYECTO")
    print("=" * 70)
    print()
    
    required_dirs = [
        "src/core",
        "src/scripts",
        "config",
        "certs",
        "tests",
        "docs",
        "data"
    ]
    
    all_ok = True
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"✅ {dir_name}/")
        else:
            print(f"❌ {dir_name}/ - NO ENCONTRADO")
            all_ok = False
    
    print()
    
    required_files = [
        "src/core/cliente_cdc.py",
        "src/scripts/validar_curp_simple.py",
        "config/config_cdc.json",
        "requirements.txt",
        "validar.py",
    ]
    
    for file_name in required_files:
        file_path = Path(file_name)
        if file_path.exists():
            print(f"✅ {file_name}")
        else:
            print(f"❌ {file_name} - NO ENCONTRADO")
            all_ok = False
    
    print()
    return all_ok


def check_config():
    """Verifica la configuración"""
    print("=" * 70)
    print("🔐 VERIFICANDO CONFIGURACIÓN")
    print("=" * 70)
    print()
    
    config_file = Path("config/config_cdc.json")
    if not config_file.exists():
        print("❌ No se encontró config/config_cdc.json")
        return False
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        api_key = config.get("cdc", {}).get("api_key", "")
        private_key = config.get("cdc", {}).get("private_key_b64", "")
        base_url = config.get("cdc", {}).get("base_url", "")
        
        if api_key and not api_key.startswith("TU_"):
            print(f"✅ API Key: {api_key[:10]}...") 
        else:
            print("⚠️  API Key no configurada")
        
        if private_key and not private_key.startswith("TU_"):
            print(f"✅ Private Key: {len(private_key)} caracteres")
        else:
            print("⚠️  Private Key no configurada")
        
        if base_url:
            print(f"✅ Base URL: {base_url}")
        else:
            print("⚠️  Base URL no configurada")
        
        print()
        
        if api_key and private_key and base_url:
            return True
        else:
            print("⚠️  Configuración incompleta")
            return False
            
    except json.JSONDecodeError:
        print("❌ Error: config_cdc.json no es un JSON válido")
        return False


def check_certs():
    """Verifica que los certificados existan"""
    print("=" * 70)
    print("🔑 VERIFICANDO CERTIFICADOS")
    print("=" * 70)
    print()
    
    certs_dir = Path("certs")
    if not certs_dir.exists():
        print("❌ No se encontró directorio certs/")
        return False
    
    required_certs = [
        "pri_key.pem",
        "certificate.pem",
    ]
    
    all_ok = True
    for cert_file in required_certs:
        cert_path = certs_dir / cert_file
        if cert_path.exists():
            size = cert_path.stat().st_size
            print(f"✅ {cert_file} ({size} bytes)")
        else:
            print(f"⚠️  {cert_file} - NO ENCONTRADO (opcional)")
            all_ok = False
    
    # Buscar certificado del CDC
    cdc_certs = list(certs_dir.glob("cdc_cert_*.pem"))
    if cdc_certs:
        print(f"✅ Certificado CDC: {cdc_certs[0].name}")
    else:
        print("⚠️  Certificado CDC - NO ENCONTRADO (opcional)")
    
    print()
    return True


def print_summary():
    """Imprime un resumen del estado"""
    print("=" * 70)
    print("📊 RESUMEN")
    print("=" * 70)
    print()
    print("✅ Estructura de proyecto está correcta")
    print()
    print("👉 Próximos pasos:")
    print()
    print("1. Configurar credenciales (si no está hecho):")
    print("   Editar: config/config_cdc.json")
    print()
    print("2. Instalar dependencias:")
    print("   pip install -r requirements.txt")
    print()
    print("3. Probar autenticación:")
    print("   python tests/test_autenticacion.py")
    print()
    print("4. Validar un CURP:")
    print("   python validar.py MERE020526HMNRZDA2")
    print()
    print("📚 Ver documentación:")
    print("   docs/ESTRUCTURA.md")
    print("   README_NEW.md")
    print()


def main():
    """Función principal"""
    print()
    print("🚀 SETUP INICIAL - VALIDADOR DE CURP")
    print()
    
    structure_ok = check_structure()
    print()
    
    config_ok = check_config()
    print()
    
    certs_ok = check_certs()
    print()
    
    if structure_ok and config_ok and certs_ok:
        print("=" * 70)
        print("✅ ¡TODO ESTÁ LISTO!")
        print("=" * 70)
        print()
        print_summary()
    else:
        print("=" * 70)
        print("⚠️  PENDIENTE DE CONFIGURACIÓN")
        print("=" * 70)
        print()
        if not config_ok:
            print("1. Configurar: config/config_cdc.json")
        if not certs_ok:
            print("2. Agregar certificados en: certs/")
        print()
        print("Consultar: docs/ESTRUCTURA.md para instrucciones")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
