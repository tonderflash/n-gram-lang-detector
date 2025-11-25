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

def calculate_scores(text_ngrams: set[str], model: dict[str, float]) -> tuple[float, float]:
    """
    Calcula puntajes para un texto dado un modelo.
    Retorna: (suma_pesos, cosine_similarity)
    """
    
    # Intersección de n-gramas (los que están en el texto y en el modelo)
    matches = [ngram for ngram in text_ngrams if ngram in model]
    
    # 1. Suma de pesos
    # score = sum(weight) para cada match
    sum_weights = sum(model[ngram] for ngram in matches)
    
    # 2. Cosine Similarity
    # Numerador: sum(w_text * w_lang)
    # Como w_text = w_lang (si existe), entonces sum(w_lang^2) para los matches
    numerator = sum(model[ngram] ** 2 for ngram in matches)
    
    # Denominador: |A| * |B|
    # |A| (Texto): sqrt(sum(w_text^2)) -> sqrt(sum(w_lang^2)) para los matches
    norm_text = math.sqrt(sum(model[ngram] ** 2 for ngram in matches))
    
    # |B| (Modelo): sqrt(sum(w_lang^2)) para TODO el modelo
    # Esto se podría pre-calcular para optimizar, pero aquí lo hacemos al vuelo
    norm_model = math.sqrt(sum(w ** 2 for w in model.values()))
    
    if norm_text == 0 or norm_model == 0:
        cosine_sim = 0.0
    else:
        cosine_sim = numerator / (norm_text * norm_model)
        
    return sum_weights, cosine_sim

def detect_language(text: str, model_es_path: str, model_en_path: str):
    model_es = load_model(model_es_path)
    model_en = load_model(model_en_path)
    
    # Extraer n-gramas del texto (usamos solo las keys, ignoramos frecuencia por ahora)
    text_ngrams_dict = extract_ngrams(text, min_n=3, max_n=6)
    text_ngrams = set(text_ngrams_dict.keys())
    
    # Calcular puntajes
    sum_es, cos_es = calculate_scores(text_ngrams, model_es)
    sum_en, cos_en = calculate_scores(text_ngrams, model_en)
    
    print(f"Texto: \"{text[:50]}...\"")
    print("-" * 40)
    # print(f"Resultados (Suma de Pesos):")
    # print(f"  Español: {sum_es:.4f}")
    # print(f"  Inglés:  {sum_en:.4f}")
    # winner_sum = "Español" if sum_es > sum_en else "Inglés"
    # print(f"  🏆 Ganador: {winner_sum}")
    # print("-" * 40)
    
    # Preferimos usar Cosine Similarity porque es más robusto y vacano (REAL)
    # La suma de pesos es un método más básico.
    
    print("-" * 40)
    print(f"Resultados (Cosine Similarity):")
    print(f"  Español: {cos_es:.4f}")
    print(f"  Inglés:  {cos_en:.4f}")
    
    # Calcular porcentajes (Proporción)
    total_score = cos_es + cos_en
    if total_score > 0:
        pct_es = (cos_es / total_score) * 100
        pct_en = (cos_en / total_score) * 100
    else:
        pct_es = 0.0
        pct_en = 0.0
        
    print(f"  📊 Proporción: {pct_es:.1f}% Español | {pct_en:.1f}% Inglés")
    
    # Umbral de Spanglish: si ambos idiomas superan 45%, es mezcla real
    # (Basado en análisis empírico: el ruido en textos puros puede llegar a ~44%)
    SPANGLISH_THRESHOLD = 45.0
    if pct_es >= SPANGLISH_THRESHOLD and pct_en >= SPANGLISH_THRESHOLD:
        print(f"  🌐 Spanglish detectado (ambos idiomas > {SPANGLISH_THRESHOLD}%)")
    
    winner_cos = "Español" if cos_es > cos_en else "Inglés"
    print(f"  🏆 Ganador: {winner_cos}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Detectar idioma de un texto")
    parser.add_argument("text", help="Texto a clasificar")
    parser.add_argument(
        "--discriminative", "-d",
        action="store_true",
        help="Usar modelos discriminativos (menos ruido latino)"
    )
    
    args = parser.parse_args()
    
    if args.discriminative:
        detect_language(args.text, "models/model_es_disc.json", "models/model_en_disc.json")
    else:
        detect_language(args.text, "models/model_es.json", "models/model_en.json")
