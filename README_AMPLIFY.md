# Despliegue en AWS Amplify

Este proyecto puede ser desplegado en AWS Amplify como una aplicación full-stack.

## Estructura del Proyecto

```
n-gram-lang-detector/
├── api/                    # Backend API (FastAPI)
│   └── app.py             # API REST
├── public/                 # Frontend estático
│   ├── index.html         # Interfaz web
│   └── models/            # Modelos JSON
├── requirements.txt        # Dependencias Python
├── amplify.yml            # Configuración de Amplify
└── ...                    # Código fuente del detector
```

## Opciones de Despliegue

### Opción 1: Amplify con Lambda Functions (Recomendado)

1. **Configurar Amplify Hosting:**
   ```bash
   # Instalar Amplify CLI
   npm install -g @aws-amplify/cli
   
   # Inicializar proyecto
   amplify init
   ```

2. **Crear función Lambda:**
   ```bash
   amplify add function
   # Seleccionar: Lambda function
   # Nombre: detectLanguage
   # Runtime: Python 3.11
   ```

3. **Configurar la función Lambda:**
   - Copiar `api/app.py` a `amplify/backend/function/detectLanguage/src/`
   - Copiar `detect_lang_v2.py` y `ngram_extractor.py` a la misma carpeta
   - Copiar los modelos a `amplify/backend/function/detectLanguage/src/models/`
   - Crear `requirements.txt` en la carpeta de la función

4. **Desplegar:**
   ```bash
   amplify push
   ```

### Opción 2: Amplify Hosting + API Gateway + Lambda

1. **Crear función Lambda manualmente:**
   - En AWS Console, crear una función Lambda
   - Runtime: Python 3.11
   - Subir el código desde `api/`
   - Configurar API Gateway como trigger

2. **Actualizar `public/index.html`:**
   - Cambiar `API_URL` a la URL de tu API Gateway

3. **Desplegar frontend:**
   ```bash
   amplify add hosting
   amplify publish
   ```

### Opción 3: Amplify Hosting (Solo Frontend) + Backend Separado

Si prefieres mantener el backend en otro servicio (EC2, ECS, etc.):

1. **Desplegar solo el frontend:**
   ```bash
   amplify add hosting
   amplify publish
   ```

2. **Actualizar `public/index.html`:**
   - Configurar `API_URL` con la URL de tu backend

## Configuración de CORS

Si el backend está en un dominio diferente, asegúrate de configurar CORS en `api/app.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://tu-dominio.amplifyapp.com"],  # Tu dominio de Amplify
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Variables de Entorno

Si necesitas configurar variables de entorno en Amplify:

1. En AWS Console → Amplify → App Settings → Environment variables
2. Agregar variables como:
   - `MODEL_PATH`: Ruta a los modelos
   - `SPANGLISH_THRESHOLD`: Umbral por defecto

## Pruebas Locales

Antes de desplegar, prueba localmente:

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar API
cd api
python app.py

# Abrir index.html en el navegador
# O usar un servidor local:
python -m http.server 8080
```

## Notas Importantes

1. **Tamaño de los modelos:** Los modelos JSON pueden ser grandes. Asegúrate de que estén incluidos en el despliegue.

2. **Cold Start:** Las funciones Lambda pueden tener un "cold start" la primera vez. Considera usar provisioned concurrency si necesitas baja latencia.

3. **Límites de Lambda:**
   - Tiempo máximo: 15 minutos
   - Memoria: Hasta 10 GB
   - Tamaño del deployment: 50 MB (comprimido) o 250 MB (descomprimido)

4. **Costos:** Amplify Hosting tiene un tier gratuito generoso. Lambda también tiene un tier gratuito.

## Troubleshooting

- **Error 502:** Verifica que la función Lambda esté correctamente configurada
- **CORS errors:** Revisa la configuración de CORS en `app.py`
- **Modelos no encontrados:** Verifica las rutas a los modelos en la función Lambda
- **Timeout:** Aumenta el timeout de la función Lambda si los modelos son grandes

