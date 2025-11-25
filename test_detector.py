#!/usr/bin/env python
"""
Script de pruebas para el detector de idioma.
Ejecuta múltiples casos de prueba y muestra los resultados.
"""

from detect_lang import detect_language
import sys

# Casos de prueba organizados por categoría
TEST_CASES = {
    "Español puro": [
        "Hola, ¿cómo estás?",
        "Me gusta mucho el fútbol",
        "Gracias por tu ayuda",
        "Buenos días, ¿qué tal?",
        "El clima está muy agradable hoy",
    ],
    
    "Inglés puro": [
        "Hello, how are you?",
        "I really like football",
        "Thank you for your help",
        "Good morning, how are you doing?",
        "The weather is very nice today",
    ],
    
    "Spanglish (mezcla real)": [
        "Hola world, esto es un test",
        "I feel shame when with you, el martes",
        "Me gusta mucho the weather today",
        "Vamos a watch a movie en el cine",
        "Let's go to la playa this weekend",
    ],
    
    "Frases cortas (ambiguas)": [
        "hola",
        "hello",
        "me",
        "you",
        "gracias",
    ],
    
    "Casos edge": [
        "123456789",
        "!!!???",
        "",
        "a b c d e f",
        "el the la and",
    ],
}

def run_tests():
    """Ejecuta todos los casos de prueba."""
    print("=" * 80)
    print("PRUEBAS DEL DETECTOR DE IDIOMA")
    print("=" * 80)
    print()
    
    total_tests = sum(len(cases) for cases in TEST_CASES.values())
    current_test = 0
    
    for category, test_cases in TEST_CASES.items():
        print(f"\n{'=' * 80}")
        print(f"📂 Categoría: {category}")
        print(f"{'=' * 80}\n")
        
        for text in test_cases:
            current_test += 1
            print(f"[{current_test}/{total_tests}] ", end="")
            
            try:
                detect_language(text, "models/model_es.json", "models/model_en.json")
            except Exception as e:
                print(f"❌ Error: {e}")
            
            print()  # Línea en blanco entre tests
    
    print("=" * 80)
    print("✅ Pruebas completadas")
    print("=" * 80)

if __name__ == "__main__":
    run_tests()
