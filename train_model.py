import json
import math
import sys
from pathlib import Path
from ngram_extractor import extract_ngrams

import argparse

import argparse

def train_model(corpus_path: str, output_path: str, k: int = 500):
    """
    Entrena un modelo de idioma a partir de un corpus.
    
    Pipeline:
    1. Leer corpus
    2. Extraer n-gramas (frecuencias)
    3. Calcular probabilidades y PESOS para TODOS los n-gramas
    4. Ordenar por PESO descendente
    5. Filtrar Top-K
    6. Guardar modelo
    """
    print(f"Procesando {corpus_path} (K={k})...")
    
    try:
        with open(corpus_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {corpus_path}")
        return

    if not text:
        print("Error: El corpus está vacío")
        return

    # 1 & 2. Extraer n-gramas
    ngrams_freq = extract_ngrams(text, min_n=3, max_n=6)
    
    # Total bytes para calcular probabilidad
    total_bytes = len(text.encode('utf-8'))
    
    # 3. Calcular pesos para TODOS (antes de filtrar)
    all_ngrams_weights = {}
    
    for ngram, freq in ngrams_freq.items():
        prob = freq / total_bytes
        ngram_len = len(ngram)
        
        weight = (prob ** 0.27) * (ngram_len ** 0.09)
        all_ngrams_weights[ngram] = weight

    # 4. Ordenar por PESO descendente
    sorted_by_weight = sorted(all_ngrams_weights.items(), key=lambda item: item[1], reverse=True)
    
    # 5. Filtrar Top-K
    top_k_model = dict(sorted_by_weight[:k])
    
    # 6. Filtrar redundancia (eliminar substrings de n-gramas más largos con mayor peso)
    # Ordenamos por longitud descendente para procesar primero los más largos
    sorted_by_length = sorted(top_k_model.items(), key=lambda item: (len(item[0]), item[1]), reverse=True)
    
    filtered_model = {}
    for ngram, weight in sorted_by_length:
        # Verificar si este n-grama es substring de alguno ya aceptado (más largo y con mayor peso)
        is_substring = False
        for accepted_ngram in filtered_model.keys():
            if ngram in accepted_ngram and len(ngram) < len(accepted_ngram):
                is_substring = True
                break
        
        if not is_substring:
            filtered_model[ngram] = weight
    
    # Redondear para guardar (estética y tamaño)
    final_model = {ngram: float(f"{weight:.5f}") for ngram, weight in filtered_model.items()}
        
    # 7. Guardar modelo
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_model, f, ensure_ascii=False, indent=2)
        
    print(f"Modelo guardado en {output_path} ({len(final_model)} n-gramas, {k - len(final_model)} redundantes eliminados)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Entrenar modelo de idioma n-gram")
    parser.add_argument("corpus_path", help="Ruta al archivo de corpus")
    parser.add_argument("output_path", help="Ruta para guardar el modelo JSON")
    parser.add_argument("--k", type=int, default=500, help="Número de n-gramas a mantener (Top-K)")
    
    args = parser.parse_args()
    
    train_model(args.corpus_path, args.output_path, args.k)
