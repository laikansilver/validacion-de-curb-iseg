# Validación de CURP contra RENAPO 🇲🇽

Sistema profesional para validar CURPs (Clave Única de Registro de Población) contra RENAPO usando la API de **Circulo de Crédito**.

## ⚡ Uso Rápido

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar credenciales (una sola vez)
# Editar: config/config_cdc.json

# 3. Validar un CURP
python validar.py MERE020526HMNRZDA2
```

### Output esperado
```
✅ ¡CURP VÁLIDO Y ENCONTRADO EN RENAPO!

CURP                      : PRUEBA40200HMNMSR01
Apellido Paterno          : PRUEBA
Apellido Materno          : PRUEBA
Nombres                   : JUAN
Sexo                      : H
Fecha de Nacimiento       : 18/06/1990
Nacionalidad              : MEX
Entidad de Nacimiento     : MN
Estado CURP               : RCN
```

---

## 📁 Estructura del Proyecto

```
.
├── validar.py                    # Entrada principal ⭐
├── requirements.txt              # Dependencias
├── config/
│   └── config_cdc.json          # 🔐 Credenciales (editar aquí)
├── certs/
│   ├── pri_key.pem              # Clave privada
│   ├── certificate.pem          # Certificado del usuario
│   └── cdc_cert_*.pem           # Certificado del CDC
├── src/
│   ├── core/
│   │   ├── cliente_cdc.py        # Cliente API
│   │   └── validador_curp.py     # Validador avanzado
│   └── scripts/
│       └── validar_curp_simple.py
├── tests/
│   └── test_autenticacion.py     # Prueba de conexión
└── docs/
    ├── ESTRUCTURA.md             # Documentación detallada
    └── (OpenAPI, Postman, etc.)
```

👉 **Para más detalles**: Ver [docs/ESTRUCTURA.md](docs/ESTRUCTURA.md)

---

## 🔧 Configuración

### 1. Credenciales de Circulo de Crédito

Editar `config/config_cdc.json`:

```json
{
  "cdc": {
    "api_key": "Tu Consumer Key aquí",
    "private_key_b64": "Tu clave privada en base64",
    "base_url": "https://services.circulodecredito.com.mx/sandbox/v1"
  }
}
```

Obtener credenciales:
1. Crear cuenta en https://developer.circulodecredito.com.mx
2. Registrar aplicación
3. Generar certificado (ver [docs/ESTRUCTURA.md](docs/ESTRUCTURA.md))
4. Copiar valores a `config/config_cdc.json`

### 2. Cambiar a Producción

```json
"base_url": "https://services.circulodecredito.com.mx/v1"  // Sin /sandbox
```

---

## 🧪 Testing

### Verificar conexión y autenticación
```bash
python tests/test_autenticacion.py
```

Si todo funciona, verás:
```
✅ ¡AUTENTICACIÓN EXITOSA!
```

---

## 💻 Uso en Código

### Validar un CURP
```python
from src.core.cliente_cdc import CirculoDeCredito

client = CirculoDeCredito(
    api_key="YOUR_API_KEY",
    private_key_b64="YOUR_PRIVATE_KEY"
)

exitoso, respuesta = client.validate_curp("MERE020526HMNRZDA2")

if exitoso:
    datos = client.extract_data(respuesta)
    print(datos)
```

### Procesar múltiples CURPs
```python
from src.core.cliente_cdc import CirculoDeCredito

client = CirculoDeCredito(api_key, private_key)

curps = ["MERE020526HMNRZDA2", "PERE030615HMNMRA05", ...]

for curp in curps:
    exitoso, respuesta = client.validate_curp(curp)
    if exitoso:
        datos = client.extract_data(respuesta)
        # Procesar datos...
```

---

## 🔐 Seguridad

### Almacenar Credenciales (Producción)

❌ **NO hacer:**
```python
api_key = "RDQpKk92ufPp3vaZzTJ9NTmGRNlgARmk"  # ¡INSEGURO!
```

✅ **HACER:**
```python
import os
api_key = os.getenv("CDC_API_KEY")
```

### .gitignore recomendado
```
config/config_cdc.json      # ¡Nunca versionar credenciales!
certs/                      # Certificados privados
.env
*.pem
```

---

## 📊 Información Retornada

Cuando valida un CURP, obtienes:

```python
{
    "curp": "PRUEBA40200HMNMSR01",
    "apellidoPaterno": "PRUEBA",
    "apellidoMaterno": "PRUEBA",
    "nombres": "JUAN",
    "sexo": "H",                           # H=Hombre, M=Mujer
    "fechaNacimiento": "18/06/1990",
    "nacionalidad": "MEX",
    "entidadNacimiento": "MN",             # Clave de entidad (SL=Sinaloa, etc.)
    "statusCurp": "RCN"                    # Estado del CURP
}
```

---

## 🚀 Casos de Uso

### 1. Validación Individual
```bash
python validar.py MERE020526HMNRZDA2
```

### 2. Validación Batch (CSV)
```python
import csv
from src.core.cliente_cdc import CirculoDeCredito

client = CirculoDeCredito(api_key, private_key)

with open('data/curps.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        exitoso, respuesta = client.validate_curp(row['curp'])
        row['valido'] = 'SI' if exitoso else 'NO'
```

### 3. API REST (Flask/FastAPI)
```python
from flask import Flask, jsonify, request
from src.core.cliente_cdc import CirculoDeCredito

app = Flask(__name__)
client = CirculoDeCredito(api_key, private_key)

@app.route('/validar/<curp>', methods=['GET'])
def validar(curp):
    exitoso, respuesta = client.validate_curp(curp)
    datos = client.extract_data(respuesta) if exitoso else None
    return jsonify({
        'encontrado': exitoso,
        'datos': datos
    })
```

---

## 📝 Logs y Debugging

Ver detalles de la respuesta:
```python
import json
exitoso, respuesta = client.validate_curp(curp)
print(json.dumps(respuesta, indent=2, ensure_ascii=False))
```

---

## ⚠️ Errores Comunes

| Error | Causa | Solución |
|-------|-------|----------|
| `401.3 - Unauthorized` | Credenciales inválidas | Verificar `config/config_cdc.json` |
| `"CURP no encontrado"` | El CURP no existe en RENAPO | Verificar formato y datos |
| `Timeout` | API lenta o sin conexión | Reintentar, verificar internet |
| `400.x - Bad Request` | Payload incorrecto | Revisar formato del CURP |

---

## 📚 Documentación Adicional

- [Estructura Detallada](docs/ESTRUCTURA.md)
- [Especificación OpenAPI](docs/identityData-sandbox-v1.yaml)
- [Colecciones Postman](docs/Security_Test.postman_collection.json)

---

## 🤝 Contribuir

1. Fork el proyecto
2. Crear una rama (`git checkout -b feature/mi-feature`)
3. Commit cambios (`git commit -m 'Agregar feature'`)
4. Push a la rama (`git push origin feature/mi-feature`)
5. Abrir Pull Request

---

## ✅ Checklist Inicial

- [ ] Instalar `pip install -r requirements.txt`
- [ ] Obtener credenciales del CDC
- [ ] Configurar `config/config_cdc.json`
- [ ] Ejecutar `python tests/test_autenticacion.py`
- [ ] Validar un CURP: `python validar.py MERE020526HMNRZDA2`
- [ ] ¡Listo para usar!

---

## 📧 Soporte

Para problemas:
1. Ejecutar: `python tests/test_autenticacion.py`
2. Revisar: `config/config_cdc.json`
3. Consultar: [docs/ESTRUCTURA.md](docs/ESTRUCTURA.md)

---

**Desarrollado con ❤️ para validación confiable de CURPs**
