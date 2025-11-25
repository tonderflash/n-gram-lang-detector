"""
Extractor de n-gramas para detección de idioma.

Esta es la primera tarea del pipeline: extraer todos los n-gramas posibles
de un texto sin procesamiento adicional, tratando el texto como un stream
de bytes sin tokenizar (untokenized stream of bytes).

Basado en el método de whatlang (paper de referencia).
"""

import re


def extract_ngrams(text: str, min_n: int = 3, max_n: int = 6, filter_noise: bool = True) -> dict[str, int]:
    """
    Extrae todos los n-gramas posibles de un texto.
    
    Trata el texto como un stream de bytes sin tokenizar, extrayendo
    secuencias de longitud min_n hasta max_n (inclusive).
    
    Args:
        text: Texto de entrada (untokenized stream of bytes)
        min_n: Longitud mínima de n-grama (default: 3)
        max_n: Longitud máxima de n-grama (default: 6)
        filter_noise: Si True, filtra n-gramas ruidosos (default: True)
    
    Returns:
        Diccionario con n-gramas como keys y sus frecuencias como values.
        Ejemplo: {"hol": 1, "ola": 1, "la ": 1, ...}
    
    Example:
        >>> extract_ngrams("hola mundo", min_n=3, max_n=3)
        {'hol': 1, 'ola': 1, 'la ': 1, 'a m': 1, ' mu': 1, 'mun': 1, 'und': 1, 'ndo': 1}
    """
    if not text:
        return {}
    
    if min_n < 1 or max_n < min_n:
        raise ValueError("min_n debe ser >= 1 y max_n debe ser >= min_n")
    
    ngrams = {}
    text_length = len(text)
    
    # Extraer n-gramas para cada longitud desde min_n hasta max_n
    for n in range(min_n, max_n + 1):
        # Para cada posición posible en el texto
        for i in range(text_length - n + 1):
            ngram = text[i:i + n]
            
            # Filtros de ruido (opcionales, basados en el paper)
            if filter_noise:
                # 1. Filtrar n-gramas que empiezan con espacio
                if ngram.startswith(" "):
                    continue
                
                # 2. Filtrar n-gramas con 3+ dígitos consecutivos
                if re.search(r'\d{3,}', ngram):
                    continue
                
                # 3. Filtrar n-gramas con 3+ caracteres idénticos consecutivos
                if re.search(r'(.)\1{2,}', ngram):
                    continue
                
                # 4. Filtrar n-gramas que son solo espacios o puntuación
                if re.match(r'^[\s\W]+$', ngram):
                    continue
            
            ngrams[ngram] = ngrams.get(ngram, 0) + 1
    
    return ngrams


def extract_ngrams_by_length(text: str, min_n: int = 3, max_n: int = 6) -> dict[int, dict[str, int]]:
    """
    Extrae n-gramas agrupados por longitud.
    
    Similar a extract_ngrams pero devuelve un diccionario donde las keys
    son las longitudes de n-grama y los values son diccionarios de n-gramas.
    
    Args:
        text: Texto de entrada
        min_n: Longitud mínima de n-grama
        max_n: Longitud máxima de n-grama
    
    Returns:
        Diccionario con estructura {longitud: {ngram: frecuencia}}
        Ejemplo: {3: {"hol": 1, "ola": 1}, 4: {"hola": 1, ...}}
    """
    if not text:
        return {}
    
    if min_n < 1 or max_n < min_n:
        raise ValueError("min_n debe ser >= 1 y max_n debe ser >= min_n")
    
    result = {}
    text_length = len(text)
    
    for n in range(min_n, max_n + 1):
        ngrams = {}
        for i in range(text_length - n + 1):
            ngram = text[i:i + n]
            ngrams[ngram] = ngrams.get(ngram, 0) + 1
        result[n] = ngrams
    
    return result

