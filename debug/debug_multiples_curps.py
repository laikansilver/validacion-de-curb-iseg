#!/usr/bin/env python3
"""
Prueba con múltiples CURPs diferentes para ver si todos retornan datos iguales
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src" / "core"))
from cliente_cdc import CirculoDeCredito, API_KEY, PRIVATE_KEY_B64

client = CirculoDeCredito(API_KEY, PRIVATE_KEY_B64)

curps_a_probar = [
    "MERE020526HMNRZDA2",
    "PERE030615HMNMRA05", 
    "JORE001201HMNRSAA7",
    "AAAA000101HMNRRR00",  # CURP de prueba totalmente artificial
]

print("=" * 80)
print("🧪 PROBANDO MÚLTIPLES CURPs DIFERENTES")
print("=" * 80)
print()

for curp in curps_a_probar:
    print(f"📌 CURP: {curp}")
    exitoso, respuesta = client.validate_curp(curp)
    
    if exitoso:
        datos = respuesta.get("datos", {}).get("respuestaRENAPO", {}).get("CURPStatus", {}).get("resultCURPS", {})
        print(f"   Resultado: {datos.get('CURP')}")
        print(f"   Nombres:   {datos.get('nombres')}")
        print(f"   Status:    {datos.get('statusCurp')}")
    else:
        print(f"   ❌ Error")
    
    print()
