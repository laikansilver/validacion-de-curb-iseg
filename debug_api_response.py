#!/usr/bin/env python3
"""
Script para ver la respuesta RAW de la API sin procesar
"""
import sys
import json
from pathlib import Path

# Añadir path para importar cliente_cdc
sys.path.insert(0, str(Path(__file__).parent / "src" / "core"))

from cliente_cdc import CirculoDeCredito, API_KEY, PRIVATE_KEY_B64

# Crear cliente
client = CirculoDeCredito(API_KEY, PRIVATE_KEY_B64)

# Prueba con un CURP
curp = "MERE020526HMNRZDA2"

print("=" * 80)
print(f"🔍 RESPUESTA RAW DE LA API PARA: {curp}")
print("=" * 80)
print()

print("🧪 Probando con infoProvider='DEBUG'...")
print()

exitoso, respuesta_raw = client.validate_curp(curp, info_provider="DEBUG")

print("📊 RESPUESTA COMPLETA (RAW):")
print(json.dumps(respuesta_raw, indent=2, ensure_ascii=False))

print()
print("=" * 80)
print("📋 EXTRAYENDO ESTRUCTURA...")
print("=" * 80)
print()

if exitoso:
    # Ver la estructura completa de datos
    datos_wrapper = respuesta_raw.get("datos", {})
    print("1️⃣  DATOS WRAPPER:")
    print(json.dumps(datos_wrapper, indent=2, ensure_ascii=False))
    
    print()
    print("2️⃣  RENAPO RESPONSE:")
    respuesta_renapo = datos_wrapper.get("respuestaRENAPO", {})
    print(json.dumps(respuesta_renapo, indent=2, ensure_ascii=False))
    
    print()
    print("3️⃣  CURP STATUS:")
    curp_status = respuesta_renapo.get("CURPStatus", {})
    print(json.dumps(curp_status, indent=2, ensure_ascii=False))
    
    print()
    print("4️⃣  RESULT CURPS:")
    result_curps = curp_status.get("resultCURPS", {})
    print(json.dumps(result_curps, indent=2, ensure_ascii=False))
