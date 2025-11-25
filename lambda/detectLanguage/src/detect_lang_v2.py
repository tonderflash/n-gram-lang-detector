"""
Detector de idioma v2: Híbrido con detección de Spanglish.

Estrategia:
1. Usa modelos ORIGINALES para detectar si hay mezcla (Spanglish)
2. Usa modelos DISCRIMINATIVOS para mayor precisión cuando es idioma puro

Esto combina lo mejor de ambos enfoques:
- Los modelos originales capturan el "ruido latino" que ayuda a detectar mezclas
- Los modelos discriminativos eliminan ese ruido para clasificación precisa
"""

import json
import math
import sys
from pathlib import Path
from ngram_extractor import extract_ngrams


def load_model(model_path: str) -> dict[str, float]:
    try:
        with open(model_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: No se encontró el modelo {model_path}")
        sys.exit(1)


def calculate_scores(text_ngrams: set[str], model: dict[str, float]) -> tuple[float, float, int]:
    """
    Calcula puntajes para un texto dado un modelo.
    Retorna: (cosine_similarity, sum_weights, num_matches)
    """
    matches = [ngram for ngram in text_ngrams if ngram in model]
    num_matches = len(matches)
    
    if not matches:
        return 0.0, 0.0, 0
    
    sum_weights = sum(model[ngram] for ngram in matches)
    
    numerator = sum(model[ngram] ** 2 for ngram in matches)
    norm_text = math.sqrt(sum(model[ngram] ** 2 for ngram in matches))
    norm_model = math.sqrt(sum(w ** 2 for w in model.values()))
    
    if norm_text == 0 or norm_model == 0:
        cosine_sim = 0.0
    else:
        cosine_sim = numerator / (norm_text * norm_model)
        
    return cosine_sim, sum_weights, num_matches


def detect_language_v2(
    text: str,
    model_es_orig_path: str = "models/model_es.json",
    model_en_orig_path: str = "models/model_en.json",
    model_es_disc_path: str = "models/model_es_disc.json",
    model_en_disc_path: str = "models/model_en_disc.json",
    spanglish_threshold: float = 40.0,
    verbose: bool = True
) -> dict:
    """
    Detecta idioma con sistema híbrido.
    
    Args:
        text: Texto a clasificar
        spanglish_threshold: Si ambos idiomas superan este %, es Spanglish
        verbose: Imprimir resultados detallados
    
    Returns:
        dict con resultados de detección
    """
    # Cargar modelos
    model_es_orig = load_model(model_es_orig_path)
    model_en_orig = load_model(model_en_orig_path)
    model_es_disc = load_model(model_es_disc_path)
    model_en_disc = load_model(model_en_disc_path)
    
    # Extraer n-gramas del texto
    text_ngrams = set(extract_ngrams(text, min_n=3, max_n=6).keys())
    
    # === PASO 1: Detección con modelos ORIGINALES (para Spanglish) ===
    cos_es_orig, _, matches_es_orig = calculate_scores(text_ngrams, model_es_orig)
    cos_en_orig, _, matches_en_orig = calculate_scores(text_ngrams, model_en_orig)
    
    total_orig = cos_es_orig + cos_en_orig
    if total_orig > 0:
        pct_es_orig = (cos_es_orig / total_orig) * 100
        pct_en_orig = (cos_en_orig / total_orig) * 100
    else:
        pct_es_orig = pct_en_orig = 0.0
    
    # === PASO 2: Detección con modelos DISCRIMINATIVOS (para precisión) ===
    cos_es_disc, _, matches_es_disc = calculate_scores(text_ngrams, model_es_disc)
    cos_en_disc, _, matches_en_disc = calculate_scores(text_ngrams, model_en_disc)
    
    total_disc = cos_es_disc + cos_en_disc
    if total_disc > 0:
        pct_es_disc = (cos_es_disc / total_disc) * 100
        pct_en_disc = (cos_en_disc / total_disc) * 100
    else:
        pct_es_disc = pct_en_disc = 0.0
    
    # === PASO 3: Decisión híbrida ===
    is_spanglish = False
    spanglish_type = None
    
    # Calcular "confianza" del idioma dominante en modelo original
    diff_orig = abs(pct_es_orig - pct_en_orig)
    
    # Criterio principal: Si la diferencia en modelo original es pequeña
    # Y ambos superan un mínimo, es Spanglish
    # La clave: "vocabulario latino" da diferencias de ~15-25%
    # Spanglish real da diferencias de ~0-15%
    SPANGLISH_MAX_DIFF = 15.0  # Si la diferencia es menor a esto, es mezcla
    
    if diff_orig <= SPANGLISH_MAX_DIFF and min(pct_es_orig, pct_en_orig) >= 35:
        is_spanglish = True
        
        # Determinar el tipo de Spanglish
        if pct_es_orig > pct_en_orig + 3:
            spanglish_type = "ES-dominant"
        elif pct_en_orig > pct_es_orig + 3:
            spanglish_type = "EN-dominant"
        else:
            spanglish_type = "balanced"
    
    # Criterio secundario: diferencia media (15-25%) pero con evidencia discriminativa
    elif diff_orig <= 25 and min(pct_es_orig, pct_en_orig) >= 30:
        # Solo es Spanglish si el discriminativo también muestra mezcla real
        if matches_es_disc > 0 and matches_en_disc > 0:
            is_spanglish = True
            if pct_es_orig > pct_en_orig:
                spanglish_type = "ES-dominant"
            else:
                spanglish_type = "EN-dominant"
    
    # === PASO 4: Determinar idioma dominante ===
    if is_spanglish:
        # Para Spanglish, usar modelo original para proporciones
        dominant_lang = "Español" if pct_es_orig > pct_en_orig else "Inglés"
        confidence = max(pct_es_orig, pct_en_orig)
        final_es_pct = pct_es_orig
        final_en_pct = pct_en_orig
    else:
        # Para idioma puro, priorizar discriminativo si hay matches
        if total_disc > 0 and (matches_es_disc > 0 or matches_en_disc > 0):
            dominant_lang = "Español" if cos_es_disc > cos_en_disc else "Inglés"
            confidence = max(pct_es_disc, pct_en_disc)
            final_es_pct = pct_es_disc
            final_en_pct = pct_en_disc
        else:
            # Fallback al modelo original si discriminativo no tiene matches
            dominant_lang = "Español" if cos_es_orig > cos_en_orig else "Inglés"
            confidence = max(pct_es_orig, pct_en_orig)
            final_es_pct = pct_es_orig
            final_en_pct = pct_en_orig
    
    # === Resultados ===
    result = {
        "text": text[:50] + "..." if len(text) > 50 else text,
        "dominant_language": dominant_lang,
        "is_spanglish": is_spanglish,
        "spanglish_type": spanglish_type,
        "confidence": confidence,
        "proportions": {
            "español": final_es_pct,
            "inglés": final_en_pct
        },
        "details": {
            "original": {"es": pct_es_orig, "en": pct_en_orig},
            "discriminative": {"es": pct_es_disc, "en": pct_en_disc},
            "matches_disc": {"es": matches_es_disc, "en": matches_en_disc}
        }
    }
    
    if verbose:
        print(f"\nTexto: \"{result['text']}\"")
        print("-" * 50)
        
        # Mostrar análisis detallado
        print(f"📊 Análisis Original:      {pct_es_orig:.1f}% ES | {pct_en_orig:.1f}% EN")
        print(f"📊 Análisis Discriminativo: {pct_es_disc:.1f}% ES | {pct_en_disc:.1f}% EN")
        print(f"🔍 Matches únicos:          {matches_es_disc} ES | {matches_en_disc} EN")
        print("-" * 50)
        
        if is_spanglish:
            emoji = "🌐"
            lang_display = f"SPANGLISH ({spanglish_type})"
            print(f"{emoji} Resultado: {lang_display}")
            print(f"   Base: {dominant_lang}")
            print(f"   Mezcla: {final_es_pct:.1f}% Español | {final_en_pct:.1f}% Inglés")
        else:
            emoji = "🇪🇸" if dominant_lang == "Español" else "🇬🇧"
            print(f"{emoji} Resultado: {dominant_lang}")
            print(f"   Confianza: {confidence:.1f}%")
    
    return result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Detector de idioma v2 (híbrido)")
    parser.add_argument("text", nargs="?", help="Texto a clasificar")
    parser.add_argument("--demo", action="store_true", help="Ejecutar demo con textos de prueba")
    parser.add_argument("--threshold", type=float, default=40.0, help="Umbral de Spanglish (default: 40)")
    
    args = parser.parse_args()
    
    if args.demo:
        test_cases = [
            # Español puro
            "Hoy es un día hermoso para caminar por el parque",
            "La situación económica del país ha mejorado considerablemente",
            
            # Inglés puro
            "The weather is beautiful today for a walk in the park",
            "The economic situation of the country has improved considerably",
            
            # Spanglish
            "Voy a hacer shopping porque necesito unos jeans nuevos",
            "I'm going to the tienda to buy some tortillas for dinner",
            "Let me tell you something, eso no está cool bro, you need to chill",
            "Estaba chilling en mi house cuando llegó mi friend",
            "We were at the party y de repente everyone started dancing",
        ]
        
        print("=" * 60)
        print("🔬 DEMO: Detector de Idioma v2 (Híbrido)")
        print("=" * 60)
        
        for text in test_cases:
            detect_language_v2(text, spanglish_threshold=args.threshold)
            print()
        
    elif args.text:
        detect_language_v2(args.text, spanglish_threshold=args.threshold)
    else:
        parser.print_help()

