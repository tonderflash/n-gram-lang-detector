#!/usr/bin/env python
"""
Script para probar la API localmente antes de desplegar.
"""

import requests
import json

API_URL = "http://localhost:8000"

def test_api():
    """Prueba la API con varios casos de prueba."""
    
    test_cases = [
        {
            "name": "Español puro",
            "text": "Hoy es un día hermoso para caminar por el parque"
        },
        {
            "name": "Inglés puro",
            "text": "The weather is beautiful today for a walk in the park"
        },
        {
            "name": "Spanglish",
            "text": "Voy a hacer shopping porque necesito unos jeans nuevos"
        },
        {
            "name": "Spanglish EN-dominant",
            "text": "I'm going to the tienda to buy some tortillas for dinner"
        }
    ]
    
    print("=" * 60)
    print("🧪 PRUEBAS DE LA API")
    print("=" * 60)
    print()
    
    # Verificar que la API esté corriendo
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        if response.status_code == 200:
            print("✅ API está corriendo")
        else:
            print(f"⚠️  API respondió con código: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se puede conectar a la API")
        print(f"   Asegúrate de que la API esté corriendo en {API_URL}")
        print("   Ejecuta: cd api && python app.py")
        return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    print()
    
    # Probar cada caso
    for i, test_case in enumerate(test_cases, 1):
        print(f"[{i}/{len(test_cases)}] {test_case['name']}")
        print(f"Texto: \"{test_case['text']}\"")
        
        try:
            response = requests.post(
                f"{API_URL}/detect",
                json={"text": test_case['text'], "spanglish_threshold": 40.0},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                emoji = "🌐" if data['is_spanglish'] else ("🇪🇸" if data['dominant_language'] == 'Español' else "🇬🇧")
                print(f"   {emoji} {data['dominant_language']}")
                if data['is_spanglish']:
                    print(f"   Spanglish: {data['spanglish_type']}")
                print(f"   Confianza: {data['confidence']:.1f}%")
                print(f"   Proporciones: {data['proportions']['español']:.1f}% ES | {data['proportions']['inglés']:.1f}% EN")
                print("   ✅ Éxito")
            else:
                print(f"   ❌ Error {response.status_code}: {response.text}")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
    
    print("=" * 60)
    print("✅ Pruebas completadas")
    print("=" * 60)

if __name__ == "__main__":
    test_api()

