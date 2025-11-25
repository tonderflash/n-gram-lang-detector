# Detector de Idiomas - N-gram

Detector de idiomas que identifica Español, Inglés y Spanglish usando modelos de n-gramas.

## Endpoint API

El detector está disponible como endpoint REST:

```
POST https://o7fz7ih2uf.execute-api.us-east-2.amazonaws.com/prod/detect
```

### Request

```json
{
  "text": "Texto a analizar",
  "spanglish_threshold": 40.0
}
```

### Response

```json
{
  "text": "Texto analizado",
  "dominant_language": "Español",
  "is_spanglish": false,
  "spanglish_type": null,
  "confidence": 100.0,
  "proportions": {
    "español": 100.0,
    "inglés": 0.0
  },
  "details": {
    "original": {"es": 59.06, "en": 40.94},
    "discriminative": {"es": 100.0, "en": 0.0},
    "matches_disc": {"es": 1, "en": 0}
  }
}
```

## Ejemplos de Uso

### cURL

```bash
curl -X POST https://o7fz7ih2uf.execute-api.us-east-2.amazonaws.com/prod/detect \
  -H "Content-Type: application/json" \
  -d '{"text": "Hola mundo", "spanglish_threshold": 40.0}'
```

### JavaScript

```javascript
const response = await fetch('https://o7fz7ih2uf.execute-api.us-east-2.amazonaws.com/prod/detect', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    text: 'Voy a hacer shopping porque necesito unos jeans nuevos',
    spanglish_threshold: 40.0
  })
});

const result = await response.json();
console.log(result);
```

### Python

```python
import requests

response = requests.post(
    'https://o7fz7ih2uf.execute-api.us-east-2.amazonaws.com/prod/detect',
    json={
        'text': 'Hola mundo',
        'spanglish_threshold': 40.0
    }
)

result = response.json()
print(result)
```

## Archivos Principales

- `detect_lang_v2.py` - Lógica principal del detector híbrido
- `ngram_extractor.py` - Extractor de n-gramas
- `models/` - Modelos entrenados (JSON)
  - `model_es.json` - Modelo original español
  - `model_en.json` - Modelo original inglés
  - `model_es_disc.json` - Modelo discriminativo español
  - `model_en_disc.json` - Modelo discriminativo inglés
- `data/` - Corpus de entrenamiento
  - `es-bible.txt`, `es-combined.txt`, `es-modern.txt` - Corpus español
  - `en-bible.txt`, `en-combined.txt`, `en-modern.txt` - Corpus inglés
- `amplify/backend/function/detectLanguage/src/` - Código de la función Lambda
- `train_model.py` - Script para entrenar modelos
- `train_model_discriminative.py` - Script para entrenar modelos discriminativos

## Despliegue

La función Lambda está desplegada en AWS y expuesta a través de API Gateway.

