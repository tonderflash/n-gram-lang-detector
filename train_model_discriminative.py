"""
Entrenador de modelos discriminativos con Penalización por Coincidencia.

Este script entrena modelos de idioma que penalizan n-gramas compartidos
entre idiomas, haciendo que solo los n-gramas ÚNICOS de cada idioma
tengan peso alto.

Esto elimina el "ruido latino" (raíces compartidas) que confunde al detector.
"""

import json
import math
import argparse
from pathlib import Path
from ngram_extractor import extract_ngrams


def extract_all_ngrams_with_weights(corpus_path: str) -> dict[str, float]:
    """
    Extrae todos los n-gramas de un corpus y calcula sus pesos.
    
    Returns:
        Diccionario {ngram: peso} sin filtrar Top-K aún.
    """
    print(f"  Procesando {corpus_path}...")
    
    with open(corpus_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    if not text:
        raise ValueError(f"El corpus está vacío: {corpus_path}")
    
    # Extraer n-gramas
    ngrams_freq = extract_ngrams(text, min_n=3, max_n=6)
    
    # Total bytes para calcular probabilidad
    total_bytes = len(text.encode('utf-8'))
    
    # Calcular pesos
    all_weights = {}
    for ngram, freq in ngrams_freq.items():
        prob = freq / total_bytes
        ngram_len = len(ngram)
        weight = (prob ** 0.27) * (ngram_len ** 0.09)
        all_weights[ngram] = weight
    
    print(f"    → {len(all_weights)} n-gramas extraídos")
    return all_weights


def apply_cross_language_penalty(
    weights_a: dict[str, float],
    weights_b: dict[str, float],
    penalty_mode: str = "proportional",
    penalty_factor: float = 0.1
) -> tuple[dict[str, float], dict[str, float]]:
    """
    Aplica penalización cruzada a n-gramas compartidos.
    
    Args:
        weights_a: Pesos del idioma A
        weights_b: Pesos del idioma B
        penalty_mode: Modo de penalización:
            - "zero": Si está en ambos → peso = 0
            - "proportional": peso *= penalty_factor para los compartidos
            - "ratio": peso *= (1 - peso_otro/peso_propio) si el otro es mayor
            - "unique_boost": En lugar de penalizar, BOOST a los únicos
        penalty_factor: Factor de penalización (solo para mode="proportional")
    
    Returns:
        Tuple con los pesos penalizados (weights_a_penalized, weights_b_penalized)
    """
    # Encontrar n-gramas compartidos
    shared_ngrams = set(weights_a.keys()) & set(weights_b.keys())
    unique_a = set(weights_a.keys()) - shared_ngrams
    unique_b = set(weights_b.keys()) - shared_ngrams
    
    print(f"\n📊 Análisis de coincidencia:")
    print(f"   N-gramas en A: {len(weights_a)}")
    print(f"   N-gramas en B: {len(weights_b)}")
    print(f"   Compartidos:   {len(shared_ngrams)} ({len(shared_ngrams)*100/len(weights_a):.1f}%)")
    print(f"   Únicos A:      {len(unique_a)}")
    print(f"   Únicos B:      {len(unique_b)}")
    
    # Aplicar penalización según el modo
    penalized_a = weights_a.copy()
    penalized_b = weights_b.copy()
    
    if penalty_mode == "zero":
        # Eliminar completamente los compartidos
        for ngram in shared_ngrams:
            penalized_a[ngram] = 0.0
            penalized_b[ngram] = 0.0
        print(f"\n   Modo 'zero': {len(shared_ngrams)} n-gramas eliminados de ambos")
    
    elif penalty_mode == "proportional":
        # Reducir peso de compartidos por un factor
        for ngram in shared_ngrams:
            penalized_a[ngram] *= penalty_factor
            penalized_b[ngram] *= penalty_factor
        print(f"\n   Modo 'proportional': compartidos reducidos a {penalty_factor*100}%")
    
    elif penalty_mode == "ratio":
        # Penalizar basado en cuánto "domina" el otro idioma ese n-grama
        for ngram in shared_ngrams:
            weight_a = weights_a[ngram]
            weight_b = weights_b[ngram]
            
            # Si B tiene más peso, penalizar A proporcionalmente (y viceversa)
            if weight_b > weight_a:
                ratio = weight_a / weight_b  # < 1
                penalized_a[ngram] *= ratio  # Penalizar más al que tiene menos
            else:
                ratio = weight_b / weight_a
                penalized_b[ngram] *= ratio
        print(f"\n   Modo 'ratio': penalización proporcional aplicada")
    
    elif penalty_mode == "unique_boost":
        # En lugar de penalizar, dar BOOST a los únicos
        boost_factor = 2.0
        for ngram in unique_a:
            penalized_a[ngram] *= boost_factor
        for ngram in unique_b:
            penalized_b[ngram] *= boost_factor
        print(f"\n   Modo 'unique_boost': únicos aumentados {boost_factor}x")
    
    elif penalty_mode == "discriminative":
        # Modo más sofisticado: penalizar según qué tan "compartido" es
        # Si el peso es casi igual en ambos → penalización fuerte
        # Si uno domina claramente → mantener para el dominante
        for ngram in shared_ngrams:
            weight_a = weights_a[ngram]
            weight_b = weights_b[ngram]
            
            # Ratio de similitud (1.0 = idénticos, cerca de 0 = uno domina)
            max_weight = max(weight_a, weight_b)
            min_weight = min(weight_a, weight_b)
            similarity = min_weight / max_weight if max_weight > 0 else 1.0
            
            # Penalización: mientras más similares, más penalización
            # penalty = 1.0 → no hay penalización
            # penalty = 0.0 → eliminar completamente
            penalty = 1.0 - (similarity * (1 - penalty_factor))
            
            penalized_a[ngram] *= penalty
            penalized_b[ngram] *= penalty
        print(f"\n   Modo 'discriminative': penalización adaptativa aplicada")
    
    return penalized_a, penalized_b


def filter_and_save_model(
    weights: dict[str, float],
    output_path: str,
    k: int = 500,
    remove_zeros: bool = True
) -> None:
    """
    Filtra Top-K, elimina redundancia y guarda el modelo.
    """
    # Remover pesos cero si se solicita
    if remove_zeros:
        weights = {ng: w for ng, w in weights.items() if w > 0}
    
    # Ordenar por peso descendente
    sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
    
    # Top-K
    top_k = dict(sorted_weights[:k])
    
    # Filtrar redundancia (substrings)
    sorted_by_length = sorted(top_k.items(), key=lambda x: (len(x[0]), x[1]), reverse=True)
    
    filtered = {}
    for ngram, weight in sorted_by_length:
        is_substring = False
        for accepted in filtered.keys():
            if ngram in accepted and len(ngram) < len(accepted):
                is_substring = True
                break
        if not is_substring:
            filtered[ngram] = weight
    
    # Redondear y guardar
    final = {ng: float(f"{w:.5f}") for ng, w in filtered.items()}
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final, f, ensure_ascii=False, indent=2)
    
    print(f"   → Guardado: {output_path} ({len(final)} n-gramas)")


def train_discriminative_models(
    corpus_a_path: str,
    corpus_b_path: str,
    output_a_path: str,
    output_b_path: str,
    k: int = 500,
    penalty_mode: str = "proportional",
    penalty_factor: float = 0.1
) -> None:
    """
    Entrena dos modelos discriminativos simultáneamente.
    
    Los modelos resultantes tendrán pesos reducidos para n-gramas
    compartidos, haciendo que la detección se base en lo ÚNICO
    de cada idioma.
    """
    print("=" * 60)
    print("🔧 Entrenamiento Discriminativo con Cross-Language Penalty")
    print("=" * 60)
    
    # Paso 1: Extraer n-gramas de ambos corpus
    print("\n📖 Paso 1: Extrayendo n-gramas...")
    weights_a = extract_all_ngrams_with_weights(corpus_a_path)
    weights_b = extract_all_ngrams_with_weights(corpus_b_path)
    
    # Paso 2: Aplicar penalización cruzada
    print("\n⚖️  Paso 2: Aplicando penalización cruzada...")
    penalized_a, penalized_b = apply_cross_language_penalty(
        weights_a, weights_b,
        penalty_mode=penalty_mode,
        penalty_factor=penalty_factor
    )
    
    # Paso 3: Filtrar y guardar
    print("\n💾 Paso 3: Filtrando Top-K y guardando...")
    filter_and_save_model(penalized_a, output_a_path, k)
    filter_and_save_model(penalized_b, output_b_path, k)
    
    print("\n✅ Entrenamiento completado!")
    print("=" * 60)


def analyze_shared_ngrams(model_a_path: str, model_b_path: str, top_n: int = 20):
    """
    Analiza los n-gramas compartidos entre dos modelos existentes.
    Útil para diagnóstico.
    """
    with open(model_a_path, 'r', encoding='utf-8') as f:
        model_a = json.load(f)
    with open(model_b_path, 'r', encoding='utf-8') as f:
        model_b = json.load(f)
    
    shared = set(model_a.keys()) & set(model_b.keys())
    
    print(f"\n📊 Análisis de modelos existentes:")
    print(f"   Modelo A: {len(model_a)} n-gramas")
    print(f"   Modelo B: {len(model_b)} n-gramas")
    print(f"   Compartidos: {len(shared)} ({len(shared)*100/min(len(model_a), len(model_b)):.1f}%)")
    
    if shared:
        print(f"\n   Top {top_n} n-gramas compartidos (ordenados por peso combinado):")
        shared_weights = [(ng, model_a[ng], model_b[ng]) for ng in shared]
        shared_weights.sort(key=lambda x: x[1] + x[2], reverse=True)
        
        print(f"   {'N-grama':<12} {'Peso A':>10} {'Peso B':>10} {'Diff':>10}")
        print(f"   {'-'*12} {'-'*10} {'-'*10} {'-'*10}")
        for ngram, wa, wb in shared_weights[:top_n]:
            diff = abs(wa - wb)
            print(f"   {repr(ngram):<12} {wa:>10.5f} {wb:>10.5f} {diff:>10.5f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Entrenar modelos discriminativos con Cross-Language Penalty"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")
    
    # Comando: train
    train_parser = subparsers.add_parser("train", help="Entrenar modelos discriminativos")
    train_parser.add_argument("corpus_a", help="Corpus del idioma A")
    train_parser.add_argument("corpus_b", help="Corpus del idioma B")
    train_parser.add_argument("output_a", help="Ruta de salida modelo A")
    train_parser.add_argument("output_b", help="Ruta de salida modelo B")
    train_parser.add_argument("--k", type=int, default=500, help="Top-K n-gramas")
    train_parser.add_argument(
        "--penalty-mode",
        choices=["zero", "proportional", "ratio", "unique_boost", "discriminative"],
        default="proportional",
        help="Modo de penalización"
    )
    train_parser.add_argument(
        "--penalty-factor",
        type=float,
        default=0.1,
        help="Factor de penalización (para mode=proportional/discriminative)"
    )
    
    # Comando: analyze
    analyze_parser = subparsers.add_parser("analyze", help="Analizar modelos existentes")
    analyze_parser.add_argument("model_a", help="Modelo A")
    analyze_parser.add_argument("model_b", help="Modelo B")
    analyze_parser.add_argument("--top", type=int, default=20, help="Top N compartidos")
    
    args = parser.parse_args()
    
    if args.command == "train":
        train_discriminative_models(
            args.corpus_a,
            args.corpus_b,
            args.output_a,
            args.output_b,
            k=args.k,
            penalty_mode=args.penalty_mode,
            penalty_factor=args.penalty_factor
        )
    elif args.command == "analyze":
        analyze_shared_ngrams(args.model_a, args.model_b, args.top)
    else:
        parser.print_help()

