# 🚀 Endpoint API Rápido - Sin Frontend

## Lo que necesitas hacer:

### 1. En Amplify Console → Tu App → Functions

**Crear/Editar función Lambda:**
- Nombre: `detectLanguage`
- Runtime: `Python 3.11`
- Handler: `index.handler`

**Subir estos archivos:**
```
amplify/backend/function/detectLanguage/src/
├── index.py              (handler Lambda)
├── detect_lang_v2.py     (tu detector)
├── ngram_extractor.py    (extractor de n-gramas)
└── models/               (carpeta completa)
    ├── model_es.json
    ├── model_en.json
    ├── model_es_disc.json
    └── model_en_disc.json
```

### 2. En Amplify Console → Rewrites and redirects

Agregar:
```
Source: /api/detect
Target: /api/detectLanguage  
Type: Function
Function: detectLanguage
```

### 3. En App Settings → Build settings

- **Frontend build command:** (VACÍO - dejar en blanco)
- **Build output directory:** (VACÍO - dejar en blanco)

## ✅ Usar el endpoint:

```bash
POST https://main.d3onzu7wv6rk8i.amplifyapp.com/api/detect

Body (JSON):
{
  "text": "Hola mundo",
  "spanglish_threshold": 40.0
}
```

## 📝 Ejemplo JavaScript:

```javascript
const result = await fetch('https://main.d3onzu7wv6rk8i.amplifyapp.com/api/detect', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ text: 'Voy a hacer shopping' })
}).then(r => r.json());

console.log(result);
// { dominant_language: "Español", is_spanglish: true, ... }
```

¡Eso es todo! Solo endpoint, sin frontend.

