#!/usr/bin/env python
"""
Análisis de umbrales para detección de Spanglish.
Mide la distribución de porcentajes en casos puros vs. mixtos.
"""

from detect_lang import load_model, calculate_scores, extract_ngrams

# Casos de prueba etiquetados
LABELED_CASES = {
    "pure_spanish": [
        "Hola, ¿cómo estás?",
        "Me gusta mucho el fútbol",
        "Gracias por tu ayuda",
        "Buenos días, ¿qué tal?",
        "El clima está muy agradable hoy",
        "Vamos al cine esta noche",
        "¿Dónde está la biblioteca?",
        "Necesito ayuda con mi tarea",
        "La comida está deliciosa",
        "Tengo que ir al trabajo mañana",
    ],
    
    "pure_english": [
        "Hello, how are you?",
        "I really like football",
        "Thank you for your help",
        "Good morning, how are you doing?",
        "The weather is very nice today",
        "Let's go to the movies tonight",
        "Where is the library?",
        "I need help with my homework",
        "The food is delicious",
        "I have to go to work tomorrow",
    ],
    
    "spanglish": [
        "Hola world, esto es un test",
        "I feel shame when with you, el martes",
        "Me gusta mucho the weather today",
        "Vamos a watch a movie en el cine",
        "Let's go to la playa this weekend",
        "Tengo que hacer my homework ahora",
        "The party estuvo muy fun anoche",
        "Quiero comer pizza and drink soda",
        "My familia vive en Mexico City",
        "Estoy learning English at school",
    ],
}

def analyze_threshold():
    """Analiza la distribución de porcentajes para encontrar el umbral óptimo."""
    model_es = load_model("models/model_es.json")
    model_en = load_model("models/model_en.json")
    
    results = {
        "pure_spanish": [],
        "pure_english": [],
        "spanglish": [],
    }
    
    print("=" * 80)
    print("ANÁLISIS DE UMBRALES PARA SPANGLISH")
    print("=" * 80)
    print()
    
    for category, texts in LABELED_CASES.items():
        print(f"\n{'=' * 80}")
        print(f"📂 Categoría: {category.replace('_', ' ').title()}")
        print(f"{'=' * 80}\n")
        
        for text in texts:
            # Extraer n-gramas
            text_ngrams_dict = extract_ngrams(text, min_n=3, max_n=6)
            text_ngrams = set(text_ngrams_dict.keys())
            
            # Calcular scores
            sum_es, cos_es = calculate_scores(text_ngrams, model_es)
            sum_en, cos_en = calculate_scores(text_ngrams, model_en)
            
            # Calcular porcentajes
            total_score = cos_es + cos_en
            if total_score > 0:
                pct_es = (cos_es / total_score) * 100
                pct_en = (cos_en / total_score) * 100
            else:
                pct_es = 0.0
                pct_en = 0.0
            
            # Guardar resultados
            results[category].append({
                "text": text,
                "pct_es": pct_es,
                "pct_en": pct_en,
                "min_pct": min(pct_es, pct_en),
            })
            
            print(f"  {pct_es:5.1f}% ES | {pct_en:5.1f}% EN | Min: {min(pct_es, pct_en):5.1f}% | {text[:50]}")
    
    # Análisis estadístico
    print("\n" + "=" * 80)
    print("📊 ANÁLISIS ESTADÍSTICO")
    print("=" * 80)
    print()
    
    for category, data in results.items():
        min_pcts = [d["min_pct"] for d in data]
        avg_min = sum(min_pcts) / len(min_pcts)
        max_min = max(min_pcts)
        
        print(f"{category.replace('_', ' ').title()}:")
        print(f"  Promedio del idioma minoritario: {avg_min:.1f}%")
        print(f"  Máximo del idioma minoritario:   {max_min:.1f}%")
        print()
    
    # Recomendación de umbral
    pure_spanish_max = max(d["min_pct"] for d in results["pure_spanish"])
    pure_english_max = max(d["min_pct"] for d in results["pure_english"])
    spanglish_min = min(d["min_pct"] for d in results["spanglish"])
    
    pure_max = max(pure_spanish_max, pure_english_max)
    
    print("=" * 80)
    print("🎯 RECOMENDACIÓN DE UMBRAL")
    print("=" * 80)
    print()
    print(f"Máximo 'ruido' en casos puros:     {pure_max:.1f}%")
    print(f"Mínimo 'mezcla' en Spanglish real: {spanglish_min:.1f}%")
    print()
    
    # Umbral óptimo: punto medio entre el máximo de puros y mínimo de spanglish
    optimal_threshold = (pure_max + spanglish_min) / 2
    print(f"✅ Umbral óptimo sugerido: {optimal_threshold:.1f}%")
    print()
    print(f"   (Punto medio entre {pure_max:.1f}% y {spanglish_min:.1f}%)")
    print()

if __name__ == "__main__":
    analyze_threshold()
