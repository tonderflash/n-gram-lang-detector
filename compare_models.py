"""
Script para comparar modelos originales vs discriminativos.
"""

import json
import math
from ngram_extractor import extract_ngrams


def load_model(path: str) -> dict[str, float]:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def calculate_cosine(text_ngrams: set[str], model: dict[str, float]) -> float:
    matches = [ng for ng in text_ngrams if ng in model]
    if not matches:
        return 0.0
    
    numerator = sum(model[ng] ** 2 for ng in matches)
    norm_text = math.sqrt(sum(model[ng] ** 2 for ng in matches))
    norm_model = math.sqrt(sum(w ** 2 for w in model.values()))
    
    if norm_text == 0 or norm_model == 0:
        return 0.0
    
    return numerator / (norm_text * norm_model)


def compare_detection(text: str, label: str = ""):
    """Compara la detección entre modelos originales y discriminativos."""
    
    # Cargar modelos
    model_es_orig = load_model("models/model_es.json")
    model_en_orig = load_model("models/model_en.json")
    model_es_disc = load_model("models/model_es_disc.json")
    model_en_disc = load_model("models/model_en_disc.json")
    
    # Extraer n-gramas del texto
    text_ngrams = set(extract_ngrams(text, min_n=3, max_n=6).keys())
    
    # Calcular scores
    cos_es_orig = calculate_cosine(text_ngrams, model_es_orig)
    cos_en_orig = calculate_cosine(text_ngrams, model_en_orig)
    cos_es_disc = calculate_cosine(text_ngrams, model_es_disc)
    cos_en_disc = calculate_cosine(text_ngrams, model_en_disc)
    
    # Calcular porcentajes
    total_orig = cos_es_orig + cos_en_orig
    total_disc = cos_es_disc + cos_en_disc
    
    pct_es_orig = (cos_es_orig / total_orig * 100) if total_orig > 0 else 0
    pct_en_orig = (cos_en_orig / total_orig * 100) if total_orig > 0 else 0
    pct_es_disc = (cos_es_disc / total_disc * 100) if total_disc > 0 else 0
    pct_en_disc = (cos_en_disc / total_disc * 100) if total_disc > 0 else 0
    
    # Determinar ganadores
    winner_orig = "ES" if cos_es_orig > cos_en_orig else "EN"
    winner_disc = "ES" if cos_es_disc > cos_en_disc else "EN"
    
    # Mostrar resultados
    print(f"\n{'='*70}")
    if label:
        print(f"📝 {label}")
    print(f"Texto: \"{text[:60]}{'...' if len(text) > 60 else ''}\"")
    print(f"{'='*70}")
    
    print(f"\n{'Modelo':<20} {'ES Score':>12} {'EN Score':>12} {'ES %':>8} {'EN %':>8} {'Ganador':>10}")
    print(f"{'-'*20} {'-'*12} {'-'*12} {'-'*8} {'-'*8} {'-'*10}")
    
    print(f"{'Original':<20} {cos_es_orig:>12.4f} {cos_en_orig:>12.4f} {pct_es_orig:>7.1f}% {pct_en_orig:>7.1f}% {winner_orig:>10}")
    print(f"{'Discriminativo':<20} {cos_es_disc:>12.4f} {cos_en_disc:>12.4f} {pct_es_disc:>7.1f}% {pct_en_disc:>7.1f}% {winner_disc:>10}")
    
    # Análisis de mejora
    diff_orig = abs(pct_es_orig - pct_en_orig)
    diff_disc = abs(pct_es_disc - pct_en_disc)
    
    print(f"\n📊 Diferencia (mayor = más confianza):")
    print(f"   Original:      {diff_orig:.1f}%")
    print(f"   Discriminativo: {diff_disc:.1f}%")
    
    if diff_disc > diff_orig:
        print(f"   ✅ Mejora de {diff_disc - diff_orig:.1f}% en confianza")
    else:
        print(f"   ⚠️  Sin mejora (posible Spanglish real)")
    
    return {
        "original": {"es": pct_es_orig, "en": pct_en_orig, "winner": winner_orig, "diff": diff_orig},
        "discriminative": {"es": pct_es_disc, "en": pct_en_disc, "winner": winner_disc, "diff": diff_disc}
    }


if __name__ == "__main__":
    # Textos de prueba
    test_cases = [
        # Español puro
        ("Hoy es un día hermoso para caminar por el parque", "Español puro"),
        ("La situación económica del país ha mejorado considerablemente", "Español formal (vocabulario latino)"),
        
        # Inglés puro
        ("The weather is beautiful today for a walk in the park", "Inglés puro"),
        ("The economic situation of the country has improved considerably", "Inglés formal (vocabulario latino)"),
        
        # Casos difíciles (vocabulario técnico/latino)
        ("The information technology revolution transformed communication", "Inglés técnico"),
        ("La revolución de la tecnología de información transformó la comunicación", "Español técnico"),
        
        # Spanglish real
        ("Voy a hacer shopping porque necesito unos jeans nuevos", "Spanglish real"),
        ("I'm going to the tienda to buy some tortillas for dinner", "Spanglish real (EN base)"),
    ]
    
    print("\n" + "="*70)
    print("🔬 COMPARACIÓN: Modelos Originales vs Discriminativos")
    print("="*70)
    
    for text, label in test_cases:
        compare_detection(text, label)
    
    print("\n" + "="*70)
    print("✅ Comparación completada")
    print("="*70)


