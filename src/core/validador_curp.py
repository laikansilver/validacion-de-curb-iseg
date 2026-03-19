#!/usr/bin/env python3
"""Validador de CURP.

Funciones:
- Valida formato y reglas basicas de una CURP.
- Valida fecha de nacimiento y digito verificador.
- Consulta existencia contra un endpoint oficial configurable (si se proporciona).
- Procesa una CURP individual o un CSV con columna "curp".
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import uuid
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date
from typing import Optional

try:
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False


CURP_PATTERN = re.compile(
    r"^[A-Z][AEIOUX][A-Z]{2}"
    r"\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])"
    r"[HM]"
    r"(AS|BC|BS|CC|CL|CM|CS|CH|DF|DG|GT|GR|HG|JC|MC|MN|MS|NT|NL|OC|PL|QT|QR|SP|SL|SR|TC|TS|TL|VZ|YN|ZS|NE)"
    r"[B-DF-HJ-NP-TV-Z]{3}[A-Z\d]\d$"
)

# Tabla oficial usada para calcular el digito verificador CURP.
CHAR_TO_VALUE = {ch: idx for idx, ch in enumerate("0123456789ABCDEFGHIJKLMN\u00d1OPQRSTUVWXYZ")}


@dataclass
class ValidationResult:
    curp: str
    formato_valido: bool
    fecha_valida: bool
    digito_verificador_valido: bool
    estructuralmente_valida: bool
    existe_oficialmente: Optional[bool]
    detalle_existencia: str


class ExistenceProvider:
    """Interfaz para consultar existencia de CURP en una fuente externa."""

    def check(self, curp: str) -> tuple[Optional[bool], str]:
        raise NotImplementedError


class NoExistenceProvider(ExistenceProvider):
    """Provider por defecto: no hace consulta externa."""

    def check(self, curp: str) -> tuple[Optional[bool], str]:
        return None, "No se configuro verificacion oficial."


class HttpExistenceProvider(ExistenceProvider):
    """Consulta existencia de CURP contra API HTTP configurable.

    Contrato esperado de respuesta JSON:
      {"exists": true, "message": "CURP encontrada"}
    """

    def __init__(self, base_url: str, token: Optional[str] = None, timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    def check(self, curp: str) -> tuple[Optional[bool], str]:
        query = urllib.parse.urlencode({"curp": curp})
        url = f"{self.base_url}?{query}"
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        req = urllib.request.Request(url=url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return None, f"Error HTTP en consulta oficial: {exc.code}"
        except urllib.error.URLError as exc:
            return None, f"Error de red en consulta oficial: {exc.reason}"
        except json.JSONDecodeError:
            return None, "Respuesta no valida (no es JSON)."

        exists = payload.get("exists")
        message = payload.get("message", "Consulta oficial realizada.")

        if isinstance(exists, bool):
            return exists, str(message)

        return None, "La API no devolvio un campo booleano 'exists'."


class CirculoCreditoExistenceProvider(ExistenceProvider):
    """Consulta existencia de CURP via Identity Data API de Circulo de Credito.

    Endpoint esperado:
      POST {base_url}/identity-data/validations

    Headers esperados por el proveedor:
      - x-api-key
      - x-signature (si auto_sign=True, se genera automaticamente)
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        signature: Optional[str] = None,
        auto_sign: bool = False,
        private_key_hex: Optional[str] = None,
        timeout: int = 15,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.username = username
        self.password = password
        self.signature = signature
        self.auto_sign = auto_sign
        self.private_key_hex = private_key_hex
        self.timeout = timeout

        if auto_sign and not private_key_hex:
            raise ValueError("auto_sign requiere private_key_hex")

    def _sign_payload(self, payload: bytes) -> str:
        """Genera firma ECDSA SHA256 del payload (x-signature)."""
        if not HAS_CRYPTOGRAPHY:
            raise RuntimeError("Se requiere 'cryptography' para auto_sign. Instala: pip install cryptography")

        private_value = int(self.private_key_hex, 16)
        private_key = ec.derive_private_key(private_value, ec.SECP384R1(), default_backend())

        signature_bytes = private_key.sign(payload, ec.ECDSA(hashes.SHA256()))

        signature_hex = signature_bytes.hex()
        return signature_hex

    def check(self, curp: str) -> tuple[Optional[bool], str]:
        url = f"{self.base_url}/identity-data/validations"
        body = {
            "infoProvider": "RENAPO",
            "curp": curp,
            "requestId": str(uuid.uuid4()),
        }
        payload = json.dumps(body, ensure_ascii=True).encode("utf-8")

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
        }

        if self.auto_sign:
            try:
                signature_hex = self._sign_payload(payload)
                headers["x-signature"] = signature_hex
            except Exception as e:
                return None, f"Error al firmar payload: {str(e)}"
        elif self.signature:
            headers["x-signature"] = self.signature

        if self.username:
            headers["username"] = self.username
        if self.password:
            headers["password"] = self.password

        req = urllib.request.Request(url=url, data=payload, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            try:
                error_payload = json.loads(exc.read().decode("utf-8"))
                if isinstance(error_payload, dict):
                    estatus = error_payload.get("estatus")
                    mensaje = error_payload.get("mensaje", "Error desconocido")

                    if estatus in {"404", "404.1"}:
                        return False, f"RENAPO indica no encontrada: {mensaje}"

                    details = json.dumps(error_payload)
                    return None, f"Error API (estatus {estatus}): {mensaje} | {details}"

                if isinstance(error_payload, str):
                    return None, f"Error API ({exc.code}): {error_payload}"
            except Exception:
                pass

            return None, f"Error HTTP en consulta oficial: {exc.code}"
        except urllib.error.URLError as exc:
            return None, f"Error de red en consulta oficial: {exc.reason}"
        except json.JSONDecodeError:
            return None, "Respuesta no valida (no es JSON)."

        code = response_payload.get("code")
        message = response_payload.get("message")
        data = response_payload.get("data", {})

        if code == 200 and message == "Success":
            if isinstance(data, dict):
                curp_result = data.get("resultCURPS", {})
                if isinstance(curp_result, dict):
                    status = curp_result.get("statusCurp")
                    if status:
                        return True, f"RENAPO exitoso (status: {status})."
            return True, "RENAPO exitoso."

        if code in {404, "404", "404.1"}:
            return False, "RENAPO reporta CURP no encontrada."

        return None, f"RENAPO devolvio codigo {code}: {message}"


def normalize_curp(curp: str) -> str:
    return curp.strip().upper()


def infer_birth_date(curp: str) -> Optional[date]:
    """Infere fecha de nacimiento usando YYMMDD y caracter de siglo (posicion 17)."""
    try:
        yy = int(curp[4:6])
        mm = int(curp[6:8])
        dd = int(curp[8:10])
    except (TypeError, ValueError):
        return None

    # Si el caracter diferenciador (17) es digito, se asume 1900-1999.
    # Si es letra, se asume 2000-2099.
    differentiator = curp[16]
    century = 1900 if differentiator.isdigit() else 2000

    try:
        return date(century + yy, mm, dd)
    except ValueError:
        return None


def compute_verification_digit(curp17: str) -> Optional[int]:
    if len(curp17) != 17:
        return None

    total = 0
    for idx, ch in enumerate(curp17):
        value = CHAR_TO_VALUE.get(ch)
        if value is None:
            return None

        weight = 18 - (idx + 1)
        total += value * weight

    digit = 10 - (total % 10)
    if digit == 10:
        digit = 0

    return digit


def validate_curp(curp: str, provider: ExistenceProvider) -> ValidationResult:
    curp = normalize_curp(curp)

    formato_valido = bool(CURP_PATTERN.match(curp))
    fecha_valida = False
    digito_verificador_valido = False

    if formato_valido:
        fecha_valida = infer_birth_date(curp) is not None
        expected_digit = compute_verification_digit(curp[:17])
        if expected_digit is not None and curp[-1].isdigit():
            digito_verificador_valido = int(curp[-1]) == expected_digit

    estructuralmente_valida = formato_valido and fecha_valida and digito_verificador_valido

    existe_oficialmente = None
    detalle_existencia = "Se omite consulta oficial porque la CURP no paso validaciones estructurales."

    if estructuralmente_valida:
        existe_oficialmente, detalle_existencia = provider.check(curp)

    return ValidationResult(
        curp=curp,
        formato_valido=formato_valido,
        fecha_valida=fecha_valida,
        digito_verificador_valido=digito_verificador_valido,
        estructuralmente_valida=estructuralmente_valida,
        existe_oficialmente=existe_oficialmente,
        detalle_existencia=detalle_existencia,
    )


def print_result(result: ValidationResult) -> None:
    print(f"CURP: {result.curp}")
    print(f"- Formato valido: {result.formato_valido}")
    print(f"- Fecha valida: {result.fecha_valida}")
    print(f"- Digito verificador valido: {result.digito_verificador_valido}")
    print(f"- Estructuralmente valida: {result.estructuralmente_valida}")
    print(f"- Existe oficialmente: {result.existe_oficialmente}")
    print(f"- Detalle existencia: {result.detalle_existencia}")


def process_csv(input_csv: str, output_csv: str, provider: ExistenceProvider) -> None:
    with open(input_csv, "r", encoding="utf-8", newline="") as infile:
        reader = csv.DictReader(infile)
        if not reader.fieldnames or "curp" not in {f.lower() for f in reader.fieldnames}:
            raise ValueError("El CSV debe tener una columna llamada 'curp'.")

        curp_column_name = next(name for name in reader.fieldnames if name.lower() == "curp")

        rows_out = []
        for row in reader:
            curp = row.get(curp_column_name, "")
            result = validate_curp(curp, provider)
            row_out = dict(row)
            row_out.update(
                {
                    "formato_valido": result.formato_valido,
                    "fecha_valida": result.fecha_valida,
                    "digito_verificador_valido": result.digito_verificador_valido,
                    "estructuralmente_valida": result.estructuralmente_valida,
                    "existe_oficialmente": result.existe_oficialmente,
                    "detalle_existencia": result.detalle_existencia,
                }
            )
            rows_out.append(row_out)

    fieldnames = list(rows_out[0].keys()) if rows_out else ["curp", "formato_valido", "fecha_valida", "digito_verificador_valido", "estructuralmente_valida", "existe_oficialmente", "detalle_existencia"]

    with open(output_csv, "w", encoding="utf-8", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_out)


def build_provider(
    api_url: Optional[str],
    api_token: Optional[str],
    cdc_enabled: bool,
    cdc_base_url: Optional[str],
    cdc_api_key: Optional[str],
    cdc_username: Optional[str],
    cdc_password: Optional[str],
    cdc_signature: Optional[str],
    cdc_auto_sign: bool = False,
    cdc_private_key: Optional[str] = None,
) -> ExistenceProvider:
    if cdc_enabled:
        if not cdc_api_key:
            raise ValueError("Falta --cdc-api-key para Círculo de Crédito")

        if cdc_auto_sign and not cdc_private_key:
            raise ValueError("--cdc-auto-sign requiere --cdc-private-key")

        return CirculoCreditoExistenceProvider(
            base_url=cdc_base_url or "https://services.circulodecredito.com.mx/sandbox/v1/identityData",
            api_key=cdc_api_key,
            username=cdc_username,
            password=cdc_password,
            signature=cdc_signature,
            auto_sign=cdc_auto_sign,
            private_key_hex=cdc_private_key,
        )

    if api_url:
        return HttpExistenceProvider(base_url=api_url, token=api_token)

    return NoExistenceProvider()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Valida CURP (estructura + existencia oficial configurable).")

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--curp", help="CURP individual a validar.")
    mode.add_argument("--input-csv", help="Archivo CSV de entrada con columna 'curp'.")

    parser.add_argument("--output-csv", help="Ruta CSV de salida (obligatorio si usas --input-csv).")
    parser.add_argument("--api-url", help="URL del endpoint oficial/proxy para validar existencia. Ej: https://mi-api/curp/exists")
    parser.add_argument("--api-token", help="Token Bearer para autenticar contra la API.")

    parser.add_argument("--cdc", action="store_true", help="Usa Identity Data API de Círculo de Crédito para validar existencia por RENAPO.")
    parser.add_argument("--cdc-base-url", help="Base URL del API de Círculo de Crédito (default: sandbox).")
    parser.add_argument("--cdc-api-key", help="Valor del header x-api-key (Consumer Key).")
    parser.add_argument("--cdc-username", help="Valor del header username (opcional).")
    parser.add_argument("--cdc-password", help="Valor del header password (opcional).")
    parser.add_argument("--cdc-signature", help="Valor del header x-signature (si prefieres no auto-firmar).")
    parser.add_argument("--cdc-auto-sign", action="store_true", help="Genera x-signature automaticamente (requiere --cdc-private-key).")
    parser.add_argument("--cdc-private-key", help="Llave privada en formato hex (sin dos puntos, generada con generar_llaves.py).")

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.input_csv and not args.output_csv:
        print("Error: si usas --input-csv debes indicar --output-csv.", file=sys.stderr)
        return 2

    provider = build_provider(
        api_url=args.api_url,
        api_token=args.api_token,
        cdc_enabled=args.cdc,
        cdc_base_url=args.cdc_base_url,
        cdc_api_key=args.cdc_api_key,
        cdc_username=args.cdc_username,
        cdc_password=args.cdc_password,
        cdc_signature=args.cdc_signature,
        cdc_auto_sign=args.cdc_auto_sign,
        cdc_private_key=args.cdc_private_key,
    )

    try:
        if args.curp:
            result = validate_curp(args.curp, provider)
            print_result(result)
        else:
            process_csv(args.input_csv, args.output_csv, provider)
            print(f"Proceso terminado. Resultado en: {args.output_csv}")
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
