# 🎯 Configurar SOLO el Endpoint API (Sin Frontend)

## El Problema
Amplify está sirviendo el frontend en `/api/`. Necesitas configurar SOLO la función Lambda como endpoint.

## ✅ Solución: Configurar la Función Lambda Directamente

### Paso 1: Crear/Editar la Función en Amplify Console

1. Ve a tu app en Amplify: https://console.aws.amazon.com/amplify
2. Selecciona tu app `n-gram-lang-detector`
3. En el menú lateral izquierdo, ve a **"Functions"**
4. Si no existe, click en **"Add function"** → **"Create new function"**
5. Si ya existe, click en la función para editarla

### Paso 2: Configurar la Función

**Nombre:** `detectLanguage`  
**Runtime:** `Python 3.11`  
**Handler:** `index.handler`

**Código (index.py):**
Copia el contenido de `amplify/backend/function/detectLanguage/src/index.py`

**Archivos a subir:**
- `detect_lang_v2.py`
- `ngram_extractor.py`
- Carpeta `models/` con los 4 archivos JSON:
  - `model_es.json`
  - `model_en.json`
  - `model_es_disc.json`
  - `model_en_disc.json`

**Configuración:**
- **Timeout:** 30 segundos (o más si los modelos son grandes)
- **Memory:** 512 MB (o 1024 MB si es necesario)

### Paso 3: Configurar Rewrites en Amplify

1. En tu app de Amplify, ve a **"Rewrites and redirects"**
2. Agrega esta regla:

```
Source address: /api/detect
Target address: /api/detectLanguage
Type: Function
Function name: detectLanguage
```

O si prefieres usar la ruta completa:

```
Source address: /api/detectLanguage
Target address: /api/detectLanguage
Type: Function
Function name: detectLanguage
```

### Paso 4: Desplegar

1. Guarda todos los cambios
2. Amplify desplegará automáticamente
3. Espera a que termine el deployment

## 🔗 Usar el Endpoint

Una vez desplegado, tu endpoint estará en:

```
POST https://main.d3onzu7wv6rk8i.amplifyapp.com/api/detectLanguage
```

O si configuraste el rewrite:

```
POST https://main.d3onzu7wv6rk8i.amplifyapp.com/api/detect
```

## 📝 Ejemplo de Uso

### cURL:
```bash
curl -X POST https://main.d3onzu7wv6rk8i.amplifyapp.com/api/detectLanguage \
  -H "Content-Type: application/json" \
  -d '{"text": "Hola mundo", "spanglish_threshold": 40.0}'
```

### JavaScript:
```javascript
const response = await fetch('https://main.d3onzu7wv6rk8i.amplifyapp.com/api/detectLanguage', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    text: 'Voy a hacer shopping',
    spanglish_threshold: 40.0
  })
});

const result = await response.json();
console.log(result);
```

### Python:
```python
import requests

response = requests.post(
    'https://main.d3onzu7wv6rk8i.amplifyapp.com/api/detectLanguage',
    json={
        'text': 'Hola mundo',
        'spanglish_threshold': 40.0
    }
)

result = response.json()
print(result)
```

## ⚠️ Si Sigue Mostrando el Frontend

Si aún ves el frontend en `/api/`, necesitas:

1. **Eliminar el frontend build:**
   - En "App settings" → "Build settings"
   - **Frontend build command:** Dejar completamente vacío
   - **Build output directory:** Dejar vacío también

2. **O crear un archivo `.amplifyignore`** en la raíz:
   ```
   public/
   *.html
   ```

3. **O simplemente ignorar la ruta `/api/`** y usar directamente la función Lambda a través de API Gateway (más complejo pero más control)

## 🔍 Verificar que Funciona

1. Ve a **CloudWatch Logs** en AWS Console
2. Busca el log group de tu función Lambda: `/aws/lambda/[tu-app]-[env]-detectLanguage`
3. Haz una llamada de prueba
4. Revisa los logs para ver si hay errores

## 📋 Respuesta Esperada

```json
{
  "text": "Hola mundo",
  "dominant_language": "Español",
  "is_spanglish": false,
  "spanglish_type": null,
  "confidence": 95.2,
  "proportions": {
    "español": 95.2,
    "inglés": 4.8
  },
  "details": {
    "original": {"es": 95.2, "en": 4.8},
    "discriminative": {"es": 98.1, "en": 1.9},
    "matches_disc": {"es": 120, "en": 3}
  }
}
```

