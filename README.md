# Validador de CURP (Python)

Este programa valida CURP en dos niveles:

1. **Validación estructural** (formato, fecha, dígito verificador).
2. **Validación de existencia oficial** por API configurable (Círculo de Crédito o endpoint personalizado).

## Requisitos

- Python 3.10+
- `cryptography` (opcional, se instala para firma digital)

## Instalación

```bash
pip install cryptography
```

## Generación de llaves (para firma con Círculo de Crédito)

Si tienes cuenta en API HUB de Círculo de Crédito, primero genera el par de llaves ECDSA:

```bash
python generar_llaves.py
```

**Esto genera:**
- `pri_key.pem` → Llave privada (GUARDA ESTO SEGURO)
- `certificate.pem` → Certificado público (carga en API HUB)
- Muestra el valor hexadecimal de `private_key` para usar en validador

**Después:**
1. Ve a https://developer.circulodecredito.com.mx/
2. Mi cuenta/Apps → Tu app → Certificados → Carga `certificate.pem`
3. Espera 1-2 minutos

## Uso rápido

### Opción 1: Validar una CURP (solo estructura)

```bash
python validador_curp.py --curp XMSA900101HDFRRN05
```

### Opción 2: Validar lote desde CSV

```bash
python validador_curp.py --input-csv entrada.csv --output-csv salida.csv
```

### Opción 3: Validar con Círculo de Crédito (Sandbox)

```bash
python validador_curp.py --curp XMSA900101HDFRRN05 \
  --cdc \
  --cdc-api-key "RDQpKk92ufPp3vaZzTJ9NTmGRNlgARmk" \
  --cdc-auto-sign \
  --cdc-private-key "7272aa5c3ae84ed967e64793079485b8f5211159931fd27be3cf3033caea18fc1c38f42f6c783974ae45a95dc1ac4318"
```

**O para lote:**

```bash
python validador_curp.py --input-csv entrada.csv --output-csv salida.csv \
  --cdc \
  --cdc-api-key "RDQpKk92ufPp3vaZzTJ9NTmGRNlgARmk" \
  --cdc-auto-sign \
  --cdc-private-key "7272aa5c3ae84ed967e64793079485b8f5211159931fd27be3cf3033caea18fc1c38f42f6c783974ae45a95dc1ac4318"
```

**Notas:**
- Usa los valores de `private_key` y `cdc_public_key` que genera `generar_llaves.py`
- Sandbox es automático; no necesitas `--cdc-base-url`
- Solo se envía a RENAPO si la CURP pasó validaciones estructurales

### Opción 4: Usar endpoint personalizado

```bash
python validador_curp.py --curp XMSA900101HDFRRN05 \
  --api-url "https://tu-api/curp/exists" \
  --api-token "TU_TOKEN"
```

## Troubleshooting

### Error 401 o 403

Usa el diagnóstico:

```bash
python diagnostico_cdc.py \
  --cdc-base-url "https://services.circulodecredito.com.mx/sandbox/v1/identityData" \
  --cdc-api-key "RDQpKk92ufPp3vaZzTJ9NTmGRNlgARmk"
```

**Causas comunes:**
- **401.3**: Producto NO habilitado en app (Mi cuenta/Apps → Editar → marcar "Identity Data")
- **403.1**: Certificado no cargado o sin sincronizar (espera 1-2 min después de cargar)
- **401.1**: x-api-key incorrecto

### Firma inválida

Verifica que:
1. El valor de `--cdc-private-key` sea exacto (sin espacios)
2. El certificado esté cargado en API HUB
3. Han pasado 1-2 minutos desde la carga

## Guía completa Círculo de Crédito

1. Crea cuenta: https://developer.circulodecredito.com.mx/
2. Registra app con "Identity Data Sandbox"
3. Copia Consumer Key
4. Ejecuta: `python generar_llaves.py`
5. Carga `certificate.pem` en Mi cuenta/Apps → Certificados
6. Valida: 
   ```bash
   python validador_curp.py --curp TU_CURP --cdc --cdc-api-key "..." --cdc-auto-sign --cdc-private-key "..."
   ```
7. Para producción: solicita acceso en https://developer.circulodecredito.com.mx/ (1-3 días)

## Notas de seguridad

- Nunca compartas: `pri_key.pem`, valor de `--cdc-private-key`, x-api-key
- Para producción: usa variables de entorno o secretos del servidor
