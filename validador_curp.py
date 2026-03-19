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
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date
from typing import Optional


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


def build_provider(api_url: Optional[str], api_token: Optional[str]) -> ExistenceProvider:
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

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.input_csv and not args.output_csv:
        print("Error: si usas --input-csv debes indicar --output-csv.", file=sys.stderr)
        return 2

    provider = build_provider(args.api_url, args.api_token)

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
