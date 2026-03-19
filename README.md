# Validador de CURP (Python)

Este programa valida CURP en dos niveles:

1. Validacion estructural (formato, fecha, digito verificador).
2. Validacion de existencia oficial por API configurable (si cuentas con una fuente autorizada).

## Requisitos

- Python 3.10+

## Uso rapido

### 1) Validar una CURP individual

```bash
python validador_curp.py --curp GODE561231HDFABC09
```

### 2) Validar lote desde CSV

El archivo de entrada debe tener una columna llamada `curp`.

```bash
python validador_curp.py --input-csv entrada.csv --output-csv salida.csv
```

### 3) Validar existencia oficial por API

Si tu institucion ya tiene API/proxy oficial para consultar CURP, puedes conectarla asi:

```bash
python validador_curp.py --curp GODE561231HDFABC09 --api-url "https://tu-api/curp/exists" --api-token "TU_TOKEN"
```

Contrato esperado del endpoint:

- Metodo: `GET`
- Query: `?curp=...`
- Respuesta JSON:

```json
{
  "exists": true,
  "message": "CURP encontrada"
}
```

## Nota importante

- La existencia real de CURP solo puede confirmarse contra una fuente oficial/autorizada.
- El script ya esta listo para integrarse con ese servicio por medio de `--api-url`.
