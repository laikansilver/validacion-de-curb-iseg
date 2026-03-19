#!/usr/bin/env python3
"""Diagnostico para la integracion con Circulo de Credito Identity Data API."""

import json
import sys
import urllib.error
import urllib.request


def test_conectividad(base_url: str) -> bool:
    """Valida que la URL sea alcanzable."""
    print(f"[1/4] Probando conectividad a {base_url}...")
    try:
        req = urllib.request.Request(url=base_url, method="HEAD")
        urllib.request.urlopen(req, timeout=5)
        print("    ✓ Conectividad OK\n")
        return True
    except urllib.error.URLError as e:
        print(f"    ✗ Error de red: {e.reason}\n")
        return False
    except Exception as e:
        print(f"    ✗ Error: {e}\n")
        return False


def test_autenticacion(
    base_url: str, api_key: str, username: str, password: str, signature: str = None
) -> tuple[bool, dict]:
    """Prueba la autenticacion con un payload minimo."""
    print(f"[2/4] Probando autenticacion...")

    url = f"{base_url}/queries"
    payload = json.dumps({
        "externalId": "00000000-0000-0000-0000-000000000000",
        "renapoQuery": {
            "curp": "AAAA000000AAAAAAA0"  # CURP de prueba invalida (no importa el contenido)
        },
    }).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "username": username,
        "password": password,
    }
    if signature:
        headers["x-signature"] = signature

    print(f"    Headers (sin valores sensibles): {list(headers.keys())}\n")

    req = urllib.request.Request(url=url, data=payload, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
            print("    ✓ Autenticacion OK (respuesta 200)\n")
            return True, result
    except urllib.error.HTTPError as exc:
        print(f"    ✗ Error HTTP {exc.code}")
        try:
            error_payload = json.loads(exc.read().decode("utf-8"))
            errors = error_payload.get("errors", [])
            if errors:
                for err in errors:
                    code = err.get("code")
                    msg = err.get("message")
                    print(f"       Código: {code} | Mensaje: {msg}")
            print()
        except Exception:
            print(f"       (No se pudo leer payload de error)\n")
        return False, {}
    except urllib.error.URLError as exc:
        print(f"    ✗ Error de red: {exc.reason}\n")
        return False, {}


def validar_credenciales(api_key: str, username: str, password: str) -> bool:
    """Valida que las credenciales no esten vacias."""
    print("[3/4] Validando formato de credenciales...")
    issues = []

    if not api_key or not api_key.strip():
        issues.append("  · x-api-key esta vacio")
    if not username or not username.strip():
        issues.append("  · username esta vacio")
    if not password or not password.strip():
        issues.append("  · password esta vacio")

    if issues:
        print("    Problemas encontrados:")
        for issue in issues:
            print(issue)
        print()
        return False

    print("    ✓ Credenciales presentes\n")
    return True


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Diagnostica la conexion con Circulo de Credito")
    parser.add_argument("--cdc-base-url", required=True, help="Base URL del API")
    parser.add_argument("--cdc-api-key", required=True, help="x-api-key")
    parser.add_argument("--cdc-username", required=True, help="username")
    parser.add_argument("--cdc-password", required=True, help="password")
    parser.add_argument("--cdc-signature", help="x-signature (opcional)")

    args = parser.parse_args()

    print("=" * 70)
    print("DIAGNOSTICO: Circulo de Credito Identity Data API")
    print("=" * 70 + "\n")

    # Paso 1: Conectividad
    if not test_conectividad(args.cdc_base_url):
        print("[!] No se puede continuar sin conectividad.")
        return 1

    # Paso 2: Validar formato de credenciales
    if not validar_credenciales(args.cdc_api_key, args.cdc_username, args.cdc_password):
        print("[!] Faltan credenciales.")
        return 1

    # Paso 3: Probar autenticacion
    success, response = test_autenticacion(
        args.cdc_base_url, args.cdc_api_key, args.cdc_username, args.cdc_password, args.cdc_signature
    )

    if not success:
        print("[!] PROBLEMA DETECTADO:")
        print("    Si recibiste 401.3 -> El producto NO está asignado a tu aplicación")
        print("    Si recibiste 401.2 -> Las credenciales (username/password) son incorrectas")
        print("    Si recibiste 401.1 -> El x-api-key es incorrecto\n")
        print("[Próximos pasos]")
        print("    1. Ve a https://developer.circulodecredito.com.mx/user/login")
        print("    2. Entra a 'Mis aplicaciones' → tu app → 'Editar'")
        print("    3. Verifica que 'Identity Data API' este activado")
        print("    4. Copia credenciales (Consumer Key = x-api-key)\n")
        return 1

    print("[4/4] Interpretando respuesta...")
    code = response.get("code")
    message = response.get("message")
    print(f"    Código: {code}")
    print(f"    Mensaje: {message}\n")

    print("=" * 70)
    print("✓ DIAGNOSTICO COMPLETADO: La autenticacion y conectividad estan OK")
    print("=" * 70)
    print("\nAhora puedes usar el validador con confianza:\n")
    print(f"python validador_curp.py --curp TU_CURP \\")
    print(f"  --cdc \\")
    print(f"  --cdc-base-url '{args.cdc_base_url}' \\")
    print(f"  --cdc-api-key 'TU_X_API_KEY' \\")
    print(f"  --cdc-username 'TU_USERNAME' \\")
    print(f"  --cdc-password 'TU_PASSWORD'")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
