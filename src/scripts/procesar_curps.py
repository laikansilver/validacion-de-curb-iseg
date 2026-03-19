#!/usr/bin/env python3
"""
Procesador de múltiples CURPs desde archivo CSV o XLSX
Valida cada CURP y indica cuáles son válidos y cuáles no
"""

import csv
import sys
import json
from pathlib import Path
from datetime import datetime
from openpyxl import load_workbook

# Agregar ruta para imports
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
from cliente_cdc import CirculoDeCredito

# Cargar configuración
config_path = Path("config/config_cdc.json")
with open(config_path, 'r') as f:
    config = json.load(f)

cdc_config = config.get("cdc", {})
client = CirculoDeCredito(
    api_key=cdc_config.get("api_key"),
    private_key_b64=cdc_config.get("private_key_b64"),
    base_url=cdc_config.get("base_url")
)


def validar_lote_curps(archivo_csv: str) -> dict:
    """
    Procesa un CSV con múltiples CURPs y valida cada uno
    
    Espera columna 'curp' en el CSV
    """
    print("=" * 80)
    print("📊 PROCESADOR DE MÚLTIPLES CURPs")
    print("=" * 80)
    print()
    
    archivo = Path(archivo_csv)
    if not archivo.exists():
        print(f"❌ Error: No se encontró el archivo '{archivo_csv}'")
        return None
    
    print(f"📂 Archivo: {archivo.name}")
    print()
    
    # Listas para resultados
    validos = []
    invalidos = []
    errores = []
    
    # Leer CSV
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            if reader.fieldnames and 'curp' not in reader.fieldnames:
                print(f"❌ Error: El CSV debe tener una columna 'curp'")
                print(f"   Columnas encontradas: {', '.join(reader.fieldnames)}")
                return None
            
            total = 0
            for idx, row in enumerate(reader, 1):
                curp = row.get('curp', '').strip().upper()
                
                if not curp:
                    print(f"⏭️  Fila {idx}: VACÍO - omitida")
                    continue
                
                total = idx
                print(f"🔍 [{idx}] Validando: {curp}...", end="", flush=True)
                
                # Validar
                exitoso, respuesta = client.validate_curp(curp)
                
                if exitoso:
                    datos = client.extract_data(respuesta)
                    if datos and datos.get("curp"):
                        print(" ✅ REGISTRADO")
                        validos.append({
                            "numero": idx,
                            "curp_solicitado": curp,
                            "datos": datos,
                            "respuesta_completa": respuesta
                        })
                    else:
                        print(" ❌ NO ENCONTRADO")
                        invalidos.append({
                            "numero": idx,
                            "curp": curp,
                            "razon": "CURP no registrado ante el gobierno"
                        })
                else:
                    print(f" ❌ ERROR")
                    errores.append({
                        "numero": idx,
                        "curp": curp,
                        "error": respuesta.get("error", str(respuesta))
                    })
        
        print()
        print("=" * 80)
        print("📋 RESUMEN DE RESULTADOS")
        print("=" * 80)
        print()
        
        print(f"Total procesados:       {total}")
        print(f"✅ Registrados:         {len(validos)}")
        print(f"❌ No registrados:      {len(invalidos)}")
        print(f"⚠️  Errores:            {len(errores)}")
        print()
        
        return {
            "total": total,
            "validos": validos,
            "invalidos": invalidos,
            "errores": errores
        }
        
    except csv.Error as e:
        print(f"❌ Error al leer CSV: {e}")
        return None
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return None


def guardar_resultados(resultados: dict, nombre_salida: str = None):
    """Guarda los resultados en archivos"""
    if not resultados:
        return
    
    # Generar nombre de archivo si no se proporciona
    if not nombre_salida:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_salida = f"validaciones_{timestamp}"
    
    # Crear directorio de resultados
    resultado_dir = Path("data/resultados")
    resultado_dir.mkdir(parents=True, exist_ok=True)
    
    # Guardar JSON completo
    archivo_json = resultado_dir / f"{nombre_salida}.json"
    with open(archivo_json, 'w', encoding='utf-8') as f:
        # Separar datos para no incluir respuesta completa en JSON
        datos_guardar = {
            "total": resultados["total"],
            "resumen": {
                "validos": len(resultados["validos"]),
                "invalidos": len(resultados["invalidos"]),
                "errores": len(resultados["errores"])
            },
            "validos": [
                {
                    "numero": v["numero"],
                    "curp_solicitado": v["curp_solicitado"],
                    "datos": v["datos"]
                }
                for v in resultados["validos"]
            ],
            "invalidos": resultados["invalidos"],
            "errores": resultados["errores"]
        }
        json.dump(datos_guardar, f, indent=2, ensure_ascii=False)
    
    # Guardar CSV con resultados
    archivo_csv = resultado_dir / f"{nombre_salida}.csv"
    with open(archivo_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Encabezado
        writer.writerow([
            "Número",
            "CURP Solicitado",
            "Estado",
            "CURP Retornado",
            "Nombres",
            "Apellido Paterno",
            "Apellido Materno",
            "Sexo",
            "Fecha Nacimiento",
            "Entidad Nacimiento",
            "Nacionalidad",
            "Detalles"
        ])
        
        # Válidos
        for v in resultados["validos"]:
            datos = v["datos"]
            writer.writerow([
                v["numero"],
                v["curp_solicitado"],
                "✅ REGISTRADO",
                datos.get("curp"),
                datos.get("nombres"),
                datos.get("apellidoPaterno"),
                datos.get("apellidoMaterno"),
                datos.get("sexo"),
                datos.get("fechaNacimiento"),
                datos.get("entidadNacimiento"),
                datos.get("nacionalidad"),
                ""
            ])
        
        # Inválidos
        for inv in resultados["invalidos"]:
            writer.writerow([
                inv["numero"],
                inv["curp"],
                "❌ NO REGISTRADO",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                inv.get("razon")
            ])
        
        # Errores
        for err in resultados["errores"]:
            writer.writerow([
                err["numero"],
                err["curp"],
                "⚠️ ERROR",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                err.get("error")
            ])


def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print("Uso: python procesar_curps.py <archivo.csv> [nombre_salida]")
        print()
        print("Ejemplo:")
        print("  python procesar_curps.py data/curps.csv")
        print("  python procesar_curps.py data/curps.csv resultados_mayo")
        print()
        print("Formato esperado del CSV:")
        print("  curp")
        print("  MERE020526HMNRZDA2")
        print("  PERE030615HMNMRA05")
        print("  ...")
        sys.exit(1)
    
    archivo = sys.argv[1]
    nombre_salida = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Procesar
    resultados = validar_lote_curps(archivo)
    
    if resultados:
        guardar_resultados(resultados, nombre_salida)


if __name__ == "__main__":
    main()
