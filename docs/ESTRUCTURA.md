# 📁 Estructura del Proyecto: Validación de CURP

## Descripción General
Sistema profesional para validar CURPs contra RENAPO usando la API de **Circulo de Crédito**.

---

## 📂 Estructura de Directorios

```
validacion de curb iseg/
│
├── 📄 validar.py                          # Punto de entrada principal ⭐
├── 📄 README.md                           # Documentación principal
│
├── 📁 src/                                # Código fuente
│   ├── 📁 core/                           # Lógica principal
│   │   ├── cliente_cdc.py                 # Cliente API de Circulo de Crédito
│   │   └── validador_curp.py              # Validador CURP (original)
│   │
│   └── 📁 scripts/                        # Scripts ejecutables
│       └── validar_curp_simple.py         # Wrapper simplificado para validación
│
├── 📁 config/                             # Archivos de configuración
│   └── config_cdc.json                    # Credenciales y configuración API
│
├── 📁 certs/                              # Certificados y claves
│   ├── pri_key.pem                        # Clave privada del usuario (secp384r1)
│   ├── certificate.pem                    # Certificado del usuario
│   └── cdc_cert_1031105411.pem           # Certificado de Circulo de Crédito
│
├── 📁 tests/                              # Pruebas y validación
│   └── test_autenticacion.py              # Script de prueba Authentication
│
├── 📁 docs/                               # Documentación
│   ├── ESTRUCTURA.md                      # Este archivo
│   ├── API-HUB_simulacion.postman*        # Colecciones Postman
│   ├── Security_Test.postman*             # Pruebas de seguridad
│   └── identityData-sandbox-v1.yaml       # OpenAPI specification
│
└── 📁 data/                               # Datos (entrada/salida)
    └── (Para archivos CSV, resultados, etc.)
```

---

## 🚀 Uso Rápido

### Opción 1: Desde la raíz (recomendado)
```bash
python validar.py MERE020526HMNRZDA2
```

### Opción 2: Script directo
```bash
cd src/scripts
python validar_curp_simple.py MERE020526HMNRZDA2
```

---

## 📋 Descripción de Carpetas

### `src/` - Código Fuente
Contiene toda la lógica de la aplicación, organizada en subcarpetas:

- **`core/`**: 
  - `cliente_cdc.py`: Cliente Python para conectar con API de Circulo de Crédito
  - `validador_curp.py`: Validador avanzado con soporte múltiples métodos

- **`scripts/`**: 
  - `validar_curp_simple.py`: Interfaz simplificada con rutas automáticas

### `config/` - Configuración
- `config_cdc.json`: Almacena credenciales:
  - Consumer Key (x-api-key)
  - Clave privada (para firmas ECDSA)
  - URL base del API

⚠️ **NOTA**: No versionar este archivo en Git si contiene credenciales reales.

### `certs/` - Certificados y Claves
Almacena material criptográfico para autenticación ECDSA:
- `pri_key.pem`: Clave privada (secp384r1) para generar firmas
- `certificate.pem`: Certificado del usuario
- `cdc_cert_XXXXXXX.pem`: Certificado público de Circulo de Crédito

### `tests/` - Pruebas
- `test_autenticacion.py`: Script para probar conectividad y autenticación
  ```bash
  python tests/test_autenticacion.py
  ```

### `docs/` - Documentación
- `ESTRUCTURA.md`: Este archivo
- Archivos OpenAPI YAML con especificación de API
- Colecciones Postman para testing manual

### `data/` - Datos
Directorio para:
- Archivos CSV de entrada con CURPs
- Resultados de validaciones
- Reportes

---

## 🔧 Configuración

### 1. Editar credenciales
```json
// config/config_cdc.json
{
  "cdc": {
    "api_key": "TU_CONSUMER_KEY",
    "private_key_b64": "TU_CLAVE_PRIVADA_BASE64",
    "base_url": "https://services.circulodecredito.com.mx/sandbox/v1"
  }
}
```

### 2. Cambiar a producción
```json
"base_url": "https://services.circulodecredito.com.mx/v1"  // Sin /sandbox
```

---

## 📊 Flujo de Validación

```
validar.py (entrada)
    ↓
src/scripts/validar_curp_simple.py (procesamiento)
    ↓
src/core/cliente_cdc.py (comunicación API)
    ↓
config/config_cdc.json (credenciales)
    ↓
certs/*.pem (autenticación ECDSA)
    ↓
Circulo de Crédito API → RENAPO
    ↓
Resultado (datos del CURP)
```

---

## 🔐 Seguridad

### Autenticación ECDSA
- Curva: secp384r1
- Algoritmo: SHA256withECDSA
- Headers requeridos:
  - `x-api-key`: Consumer Key
  - `x-signature`: Firma ECDSA del payload

### Mejores Prácticas
1. ✅ No versionar `config_cdc.json` si tiene credenciales reales
2. ✅ Guardar claves privadas en variables de entorno (en producción)
3. ✅ Usar secrets manager para credenciales
4. ✅ Rotar certificados periódicamente

---

## 🧪 Testing

### Prueba de autenticación
```bash
cd tests
python test_autenticacion.py
```

Debería mostrar:
```
✅ AUTENTICACIÓN EXITOSA
✅ ¡CURP VÁLIDO Y ENCONTRADO EN RENAPO!
```

### Probar con CURP específico
```bash
python validar.py PERE020526HMNRZDA2
```

---

## 📦 Dependencias

```
requests>=2.32.5      # HTTP client
cryptography>=46.0.5  # ECDSA signatures
```

### Instalar
```bash
pip install -r requirements.txt
```

---

## 🔄 Workflows Comunes

### Validar un CURP
```bash
python validar.py MERE020526HMNRZDA2
```

### Validar CSV
```bash
# Próximamente: script para procesar archivo CSV
```

### Obtener detalles
```python
from src.core.cliente_cdc import CirculoDeCredito
client = CirculoDeCredito(api_key, private_key_b64)
success, response = client.validate_curp(curp)
data = client.extract_data(response)
```

---

## 📝 Notas

- Todos los scripts asumen ejecución desde la **raíz del proyecto**
- La configuración se carga automáticamente desde `config/config_cdc.json`
- API está en ambiente **SANDBOX** por defecto
- Para producción, contactar a Circulo de Crédito

---

## ✅ Checklist de Configuración

- [ ] Credenciales del CDC en `config/config_cdc.json`
- [ ] Certificados en `certs/`
- [ ] Probar con `python tests/test_autenticacion.py`
- [ ] Validar CURP: `python validar.py <CURP>`
- [ ] Listo para producción

---

## 📧 Soporte

Para issues o preguntas:
1. Verificar `config/config_cdc.json` está correctamente configurado
2. Ejecutar `python tests/test_autenticacion.py`
3. Revisar logs en la consola
