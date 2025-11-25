"""
Handler para AWS Lambda.
Este archivo permite que la API funcione como función Lambda.
"""

import json
from mangum import Mangum
from app import app

# Crear handler de Mangum para convertir FastAPI a Lambda
handler = Mangum(app)


def lambda_handler(event, context):
    """
    Handler principal para Lambda.
    Mangum convierte automáticamente el evento de Lambda a una request de ASGI.
    """
    return handler(event, context)

