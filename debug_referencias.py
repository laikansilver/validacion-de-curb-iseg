#!/usr/bin/env python3
"""
Prueba con diferentes referencias para ver si cambian los datos
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src" / "core"))
from cliente_cdc import CirculoDeCredito, API_KEY, PRIVATE_KEY_B64

client = CirculoDeCredito(API_KEY, PRIVATE_KEY_B64)

curp = "MERE020526HMNRZDA2"

print("=" * 80)
print(f"🧪 PROBANDO DIFERENTES REFERENCIAS CON: {curp}")
print("=" * 80)
print()

referencias = ["001", "123", "999", "000"]

for ref in referencias:
    print(f"📌 Referencia: {ref}")
    exitoso, respuesta = client.validate_curp(curp, reference=ref)
    
    if exitoso:
        datos = respuesta.get("datos", {}).get("respuestaRENAPO", {}).get("CURPStatus", {}).get("resultCURPS", {})
        print(f"   CURP Retornado: {datos.get('CURP')}")
        print(f"   Nombres:       {datos.get('nombres')}")
        print(f"   Ap. Paterno:   {datos.get('apellidoPaterno')}")
        print(f"   Ap. Materno:   {datos.get('apellidoMaterno')}")
    else:
        print(f"   ❌ Error: {respuesta}")
    
    print()
