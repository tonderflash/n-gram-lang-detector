"""
API REST para el detector de idiomas.
Desplegable en AWS Amplify como función serverless.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
from pathlib import Path

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

from detect_lang_v2 import detect_language_v2

app = FastAPI(title="Language Detector API", version="1.0.0")

# Configurar CORS para permitir requests desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar el dominio de Amplify
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DetectRequest(BaseModel):
    text: str
    spanglish_threshold: float = 40.0


class DetectResponse(BaseModel):
    text: str
    dominant_language: str
    is_spanglish: bool
    spanglish_type: str | None
    confidence: float
    proportions: dict[str, float]
    details: dict


@app.get("/")
async def root():
    return {
        "message": "Language Detector API",
        "version": "1.0.0",
        "endpoints": {
            "/detect": "POST - Detecta el idioma de un texto",
            "/health": "GET - Health check"
        }
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/detect", response_model=DetectResponse)
async def detect_language(request: DetectRequest):
    """
    Detecta el idioma de un texto.
    
    Args:
        request: Objeto con el texto a analizar y opciones
    
    Returns:
        Resultado de la detección con idioma dominante, si es Spanglish, etc.
    """
    try:
        # Determinar la ruta base según el entorno
        # En Lambda, los archivos están en el mismo directorio o en /var/task
        base_path = Path(__file__).parent.parent
        
        # Intentar diferentes rutas posibles
        possible_paths = [
            base_path / "public" / "models",
            base_path / "models",
            Path("/var/task") / "models",  # Lambda
            Path("/var/task") / "public" / "models",  # Lambda con estructura completa
        ]
        
        models_path = None
        for path in possible_paths:
            if (path / "model_es.json").exists():
                models_path = path
                break
        
        if not models_path:
            # Fallback: usar rutas relativas desde el directorio raíz
            models_path = base_path / "public" / "models"
        
        # Construir rutas completas a los modelos
        model_es_orig = str(models_path / "model_es.json")
        model_en_orig = str(models_path / "model_en.json")
        model_es_disc = str(models_path / "model_es_disc.json")
        model_en_disc = str(models_path / "model_en_disc.json")
        
        result = detect_language_v2(
            text=request.text,
            model_es_orig_path=model_es_orig,
            model_en_orig_path=model_en_orig,
            model_es_disc_path=model_es_disc,
            model_en_disc_path=model_en_disc,
            spanglish_threshold=request.spanglish_threshold,
            verbose=False  # No imprimir en la API
        )
        
        return DetectResponse(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al detectar idioma: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

