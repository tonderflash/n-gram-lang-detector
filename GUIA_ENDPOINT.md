# Guía: Usar el Detector como Endpoint en Amplify

## 🎯 Objetivo

Desplegar la API en Amplify para que puedas llamarla desde cualquier cliente usando:
```
https://main.d3onzu7wv6rk8i.amplifyapp.com/api/detectLanguage
```

## 📋 Pasos para Desplegar

### Opción 1: Usando Amplify CLI (Recomendado)

1. **Instalar Amplify CLI:**
   ```bash
   npm install -g @aws-amplify/cli
   ```

2. **Inicializar Amplify en tu proyecto:**
   ```bash
   cd /Users/tonderflash/Developer/tagshelf/n-gram-lang-detector
   amplify init
   ```
   - Selecciona tu perfil de AWS
   - Nombre del proyecto: `n-gram-lang-detector`
   - Entorno: `dev` o `main`
   - Editor: tu editor preferido
   - Tipo de app: `javascript`
   - Framework: `none` (o `react` si quieres el frontend)
   - Source directory: `public`
   - Build command: (dejar vacío)
   - Start command: (dejar vacío)

3. **Agregar la función Lambda:**
   ```bash
   amplify add function
   ```
   - Nombre: `detectLanguage`
   - Runtime: `Python 3.11`
   - Template: `Hello World` (lo modificaremos después)
   - Configurar acceso: `No` (por ahora)

4. **Copiar archivos a la función:**
   ```bash
   # Los archivos ya están en amplify/backend/function/detectLanguage/src/
   # Solo necesitas verificar que estén:
   # - index.py (handler)
   # - detect_lang_v2.py
   # - ngram_extractor.py
   # - models/ (carpeta con los 4 archivos JSON)
   ```

5. **Desplegar:**
   ```bash
   amplify push
   ```

### Opción 2: Desde la Consola de Amplify (Más Simple)

1. **En la pantalla de "App settings" que estás viendo:**
   - **App name:** `n-gram-lang-detector` (ya está)
   - **Frontend build command:** (dejar vacío)
   - **Build output directory:** `public`

2. **Después de crear la app, agregar la función:**
   - Ve a tu app en Amplify Console
   - En el menú lateral: `Functions`
   - Click en `Add function`
   - Selecciona `Create new function`
   - Nombre: `detectLanguage`
   - Runtime: `Python 3.11`
   - Copia el contenido de `amplify/backend/function/detectLanguage/src/index.py` al editor
   - Sube los archivos necesarios:
     - `detect_lang_v2.py`
     - `ngram_extractor.py`
     - Carpeta `models/` con los 4 archivos JSON

3. **Configurar la ruta de la API:**
   - En `Rewrites and redirects` de tu app
   - Agregar regla:
     ```
     Source: /api/detectLanguage
     Target: /api/detectLanguage
     Type: Function
     Function: detectLanguage
     ```

## 🔗 Cómo Usar el Endpoint

Una vez desplegado, tu endpoint estará disponible en:

```
POST https://main.d3onzu7wv6rk8i.amplifyapp.com/api/detectLanguage
```

### Ejemplo con cURL:
```bash
curl -X POST https://main.d3onzu7wv6rk8i.amplifyapp.com/api/detectLanguage \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Voy a hacer shopping porque necesito unos jeans nuevos",
    "spanglish_threshold": 40.0
  }'
```

### Ejemplo con JavaScript (fetch):
```javascript
const response = await fetch('https://main.d3onzu7wv6rk8i.amplifyapp.com/api/detectLanguage', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    text: 'Hola mundo',
    spanglish_threshold: 40.0
  })
});

const result = await response.json();
console.log(result);
```

### Ejemplo con Python (requests):
```python
import requests

url = 'https://main.d3onzu7wv6rk8i.amplifyapp.com/api/detectLanguage'
data = {
    'text': 'Voy a hacer shopping porque necesito unos jeans nuevos',
    'spanglish_threshold': 40.0
}

response = requests.post(url, json=data)
result = response.json()
print(result)
```

## 📤 Respuesta del Endpoint

```json
{
  "text": "Voy a hacer shopping porque necesito unos jeans nuevos",
  "dominant_language": "Español",
  "is_spanglish": true,
  "spanglish_type": "ES-dominant",
  "confidence": 65.2,
  "proportions": {
    "español": 65.2,
    "inglés": 34.8
  },
  "details": {
    "original": {"es": 65.2, "en": 34.8},
    "discriminative": {"es": 70.1, "en": 29.9},
    "matches_disc": {"es": 45, "en": 12}
  }
}
```

## ⚠️ Notas Importantes

1. **Tamaño de los modelos:** Los archivos JSON pueden ser grandes. Asegúrate de que estén incluidos en el deployment de Lambda.

2. **Timeout:** La función Lambda tiene un timeout de 30 segundos configurado. Si tus modelos son muy grandes, podrías necesitar aumentarlo.

3. **Memoria:** Configurado para 512 MB. Si tienes problemas, aumenta a 1024 MB.

4. **CORS:** Ya está configurado para permitir requests desde cualquier origen (`*`). En producción, deberías restringirlo.

5. **Cold Start:** La primera llamada puede tardar más (cold start de Lambda). Las siguientes serán más rápidas.

## 🧪 Probar Localmente

Antes de desplegar, puedes probar la función localmente:

```bash
# Instalar SAM CLI o usar el emulador de Lambda
# O simplemente usar la API FastAPI:
cd api
python app.py

# En otra terminal:
curl -X POST http://localhost:8000/detect \
  -H "Content-Type: application/json" \
  -d '{"text": "Hola mundo"}'
```

## 🔍 Troubleshooting

- **Error 404:** Verifica que la ruta esté configurada en `Rewrites and redirects`
- **Error 500:** Revisa los logs de CloudWatch en la función Lambda
- **Modelos no encontrados:** Verifica que los archivos JSON estén en la carpeta `models/` dentro de la función
- **Timeout:** Aumenta el timeout de la función Lambda

