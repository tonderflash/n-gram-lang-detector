"""
Handler Lambda para el detector de idiomas.
Se expone automáticamente en /api/detectLanguage
"""

import json
import sys
from pathlib import Path

# Agregar el directorio de la función al path
sys.path.insert(0, str(Path(__file__).parent))

# Importar módulos necesarios
from detect_lang_v2 import detect_language_v2


def handler(event, context):
    """
    Handler principal de Lambda.
    
    Event structure:
    {
        "httpMethod": "POST",
        "path": "/api/detectLanguage",
        "body": "{\"text\": \"...\", \"spanglish_threshold\": 40.0}",
        "headers": {...}
    }
    """
    
    # Determinar el método HTTP
    http_method = event.get("httpMethod", "GET")
    path = event.get("path", "")
    
    # CORS headers
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS"
    }
    
    # Manejar OPTIONS (preflight CORS)
    if http_method == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({"message": "OK"})
        }
    
    # Health check
    if http_method == "GET" and path.endswith("/health"):
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({"status": "healthy", "service": "language-detector"})
        }
    
    # Endpoint principal: POST /api/detectLanguage o /api/detect
    if http_method == "POST":
        try:
            # Parsear el body
            body = event.get("body", "{}")
            if isinstance(body, str):
                body = json.loads(body)
            
            text = body.get("text", "")
            spanglish_threshold = body.get("spanglish_threshold", 40.0)
            
            if not text:
                return {
                    "statusCode": 400,
                    "headers": headers,
                    "body": json.dumps({"error": "El campo 'text' es requerido"})
                }
            
            # Determinar rutas a los modelos
            # En Lambda, los archivos están en /var/task o en el directorio de la función
            current_dir = Path(__file__).parent
            
            possible_paths = [
                current_dir / "models",  # Primero buscar en el mismo directorio que index.py
                Path("/var/task") / "models",
                Path("/var/task") / "public" / "models",
                current_dir.parent / "models",
            ]
            
            models_path = None
            for path in possible_paths:
                test_file = path / "model_es.json"
                if test_file.exists():
                    models_path = path
                    break
            
            if not models_path:
                # Último intento: buscar recursivamente desde /var/task
                import os
                for root, dirs, files in os.walk("/var/task"):
                    if "model_es.json" in files:
                        models_path = Path(root)
                        break
            
            if not models_path:
                return {
                    "statusCode": 500,
                    "headers": headers,
                    "body": json.dumps({
                        "error": "No se encontraron los modelos",
                        "debug": {
                            "current_dir": str(current_dir),
                            "searched_paths": [str(p) for p in possible_paths]
                        }
                    })
                }
            
            # Llamar al detector
            result = detect_language_v2(
                text=text,
                model_es_orig_path=str(models_path / "model_es.json"),
                model_en_orig_path=str(models_path / "model_en.json"),
                model_es_disc_path=str(models_path / "model_es_disc.json"),
                model_en_disc_path=str(models_path / "model_en_disc.json"),
                spanglish_threshold=spanglish_threshold,
                verbose=False
            )
            
            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps(result, ensure_ascii=False)
            }
            
        except Exception as e:
            return {
                "statusCode": 500,
                "headers": headers,
                "body": json.dumps({
                    "error": "Error al detectar idioma",
                    "message": str(e)
                })
            }
    
    # Método no permitido
    return {
        "statusCode": 405,
        "headers": headers,
        "body": json.dumps({"error": "Método no permitido"})
    }

