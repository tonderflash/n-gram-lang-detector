"""
Script para descargar artículos de Wikipedia en inglés y español.
Genera corpus de texto moderno para entrenamiento de modelos n-gram.
"""

import wikipediaapi
import re
import os
import time
import random
from pathlib import Path

# Categorías variadas para obtener vocabulario diverso
CATEGORIES = {
    'en': [
        # Tecnología
        'Computer_science', 'Artificial_intelligence', 'Internet', 'Software',
        'Mobile_phones', 'Social_media', 'Cryptocurrency', 'Video_games',
        # Ciencia
        'Physics', 'Biology', 'Chemistry', 'Medicine', 'Climate_change',
        'Space_exploration', 'Genetics', 'Psychology',
        # Deportes
        'Association_football', 'Basketball', 'Tennis', 'Olympic_Games',
        'American_football', 'Baseball', 'Swimming_(sport)',
        # Cultura
        'Cinema', 'Television', 'Music', 'Literature', 'Art',
        'Photography', 'Fashion', 'Cooking',
        # Sociedad
        'Economics', 'Politics', 'Education', 'Health', 'Environment',
        'Tourism', 'Transportation', 'Architecture',
        # Vida cotidiana
        'Food', 'Clothing', 'Family', 'Housing', 'Employment',
    ],
    'es': [
        # Tecnología
        'Informática', 'Inteligencia_artificial', 'Internet', 'Software',
        'Teléfono_móvil', 'Redes_sociales', 'Criptomoneda', 'Videojuegos',
        # Ciencia
        'Física', 'Biología', 'Química', 'Medicina', 'Cambio_climático',
        'Exploración_espacial', 'Genética', 'Psicología',
        # Deportes
        'Fútbol', 'Baloncesto', 'Tenis', 'Juegos_Olímpicos',
        'Fútbol_americano', 'Béisbol', 'Natación',
        # Cultura
        'Cine', 'Televisión', 'Música', 'Literatura', 'Arte',
        'Fotografía', 'Moda', 'Gastronomía',
        # Sociedad
        'Economía', 'Política', 'Educación', 'Salud', 'Medio_ambiente',
        'Turismo', 'Transporte', 'Arquitectura',
        # Vida cotidiana
        'Alimento', 'Ropa', 'Familia', 'Vivienda', 'Empleo',
    ]
}

# Artículos populares/importantes adicionales para garantizar contenido
SEED_ARTICLES = {
    'en': [
        'United_States', 'World_War_II', 'Climate_change', 'COVID-19_pandemic',
        'Artificial_intelligence', 'Internet', 'Computer', 'Facebook',
        'Google', 'Apple_Inc.', 'Microsoft', 'Amazon_(company)',
        'Football', 'Basketball', 'Olympic_Games', 'FIFA_World_Cup',
        'New_York_City', 'London', 'Tokyo', 'Paris',
        'Music', 'Film', 'Television', 'Video_game',
        'Science', 'Technology', 'Engineering', 'Mathematics',
        'History', 'Geography', 'Philosophy', 'Psychology',
        'Democracy', 'Human_rights', 'Climate', 'Environment',
        'Health', 'Medicine', 'Education', 'Economy',
        'Food', 'Water', 'Energy', 'Transportation',
        'Communication', 'Social_media', 'Smartphone', 'Email',
    ],
    'es': [
        'Estados_Unidos', 'Segunda_Guerra_Mundial', 'Cambio_climático', 'Pandemia_de_COVID-19',
        'Inteligencia_artificial', 'Internet', 'Computadora', 'Facebook',
        'Google', 'Apple_Inc.', 'Microsoft', 'Amazon',
        'Fútbol', 'Baloncesto', 'Juegos_Olímpicos', 'Copa_Mundial_de_Fútbol',
        'Ciudad_de_México', 'Madrid', 'Buenos_Aires', 'Barcelona',
        'Música', 'Cine', 'Televisión', 'Videojuego',
        'Ciencia', 'Tecnología', 'Ingeniería', 'Matemáticas',
        'Historia', 'Geografía', 'Filosofía', 'Psicología',
        'Democracia', 'Derechos_humanos', 'Clima', 'Medio_ambiente',
        'Salud', 'Medicina', 'Educación', 'Economía',
        'Alimentación', 'Agua', 'Energía', 'Transporte',
        'Comunicación', 'Red_social', 'Teléfono_inteligente', 'Correo_electrónico',
    ]
}


def clean_text(text: str) -> str:
    """
    Limpia el texto de Wikipedia removiendo elementos no deseados.
    """
    # Remover referencias [1], [2], etc.
    text = re.sub(r'\[\d+\]', '', text)
    
    # Remover URLs
    text = re.sub(r'http[s]?://\S+', '', text)
    
    # Remover caracteres especiales pero mantener puntuación básica
    text = re.sub(r'[^\w\s\.\,\;\:\!\?\'\"\-\(\)áéíóúüñÁÉÍÓÚÜÑ]', ' ', text)
    
    # Normalizar espacios múltiples
    text = re.sub(r'\s+', ' ', text)
    
    # Remover líneas muy cortas (probablemente encabezados)
    lines = text.split('\n')
    lines = [line.strip() for line in lines if len(line.strip()) > 50]
    
    return '\n'.join(lines)


def get_article_text(wiki: wikipediaapi.Wikipedia, title: str) -> str:
    """
    Obtiene el texto de un artículo de Wikipedia.
    """
    page = wiki.page(title)
    
    if not page.exists():
        return ""
    
    return page.text


def get_category_articles(wiki: wikipediaapi.Wikipedia, category_name: str, max_articles: int = 20) -> list:
    """
    Obtiene artículos de una categoría de Wikipedia.
    """
    cat = wiki.page(f"Category:{category_name}")
    
    if not cat.exists():
        return []
    
    articles = []
    for member in cat.categorymembers.values():
        if member.ns == wikipediaapi.Namespace.MAIN:  # Solo artículos principales
            articles.append(member.title)
            if len(articles) >= max_articles:
                break
    
    return articles


def download_wikipedia_corpus(lang: str, output_path: str, target_size_mb: float = 5.0):
    """
    Descarga un corpus de Wikipedia para un idioma específico.
    
    Args:
        lang: Código de idioma ('en' o 'es')
        output_path: Ruta del archivo de salida
        target_size_mb: Tamaño objetivo en MB
    """
    print(f"\n{'='*60}")
    print(f"Descargando corpus de Wikipedia ({lang.upper()})")
    print(f"{'='*60}")
    
    wiki = wikipediaapi.Wikipedia(
        user_agent='LanguageDetectorTrainer/1.0 (training data collection)',
        language=lang
    )
    
    target_bytes = int(target_size_mb * 1024 * 1024)
    collected_text = []
    collected_bytes = 0
    processed_titles = set()
    
    # Primero, procesar artículos semilla (garantizados)
    print(f"\n📖 Procesando artículos semilla...")
    seed_articles = SEED_ARTICLES.get(lang, [])
    
    for title in seed_articles:
        if collected_bytes >= target_bytes:
            break
            
        if title in processed_titles:
            continue
            
        text = get_article_text(wiki, title)
        if text:
            cleaned = clean_text(text)
            if len(cleaned) > 500:  # Solo textos sustanciales
                collected_text.append(cleaned)
                collected_bytes += len(cleaned.encode('utf-8'))
                processed_titles.add(title)
                print(f"  ✓ {title} ({len(cleaned):,} chars)")
        
        time.sleep(0.1)  # Rate limiting
    
    print(f"\n  Progreso: {collected_bytes/1024/1024:.2f} MB / {target_size_mb} MB")
    
    # Luego, procesar categorías
    print(f"\n📚 Procesando categorías...")
    categories = CATEGORIES.get(lang, [])
    random.shuffle(categories)  # Aleatorizar para variedad
    
    for category in categories:
        if collected_bytes >= target_bytes:
            break
            
        print(f"\n  Categoría: {category}")
        articles = get_category_articles(wiki, category, max_articles=15)
        
        for title in articles:
            if collected_bytes >= target_bytes:
                break
                
            if title in processed_titles:
                continue
                
            text = get_article_text(wiki, title)
            if text:
                cleaned = clean_text(text)
                if len(cleaned) > 500:
                    collected_text.append(cleaned)
                    collected_bytes += len(cleaned.encode('utf-8'))
                    processed_titles.add(title)
                    print(f"    ✓ {title[:40]}... ({len(cleaned):,} chars)")
            
            time.sleep(0.1)  # Rate limiting
        
        print(f"  Progreso: {collected_bytes/1024/1024:.2f} MB / {target_size_mb} MB")
    
    # Guardar corpus
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    full_text = '\n\n'.join(collected_text)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_text)
    
    final_size = len(full_text.encode('utf-8'))
    
    print(f"\n{'='*60}")
    print(f"✅ Corpus guardado: {output_path}")
    print(f"   Artículos: {len(processed_titles)}")
    print(f"   Tamaño: {final_size/1024/1024:.2f} MB")
    print(f"   Líneas: {len(full_text.splitlines()):,}")
    print(f"{'='*60}")
    
    return final_size


def create_balanced_corpus(wiki_path: str, bible_path: str, output_path: str, wiki_ratio: float = 0.9):
    """
    Crea un corpus balanceado combinando Wikipedia y texto bíblico.
    
    Args:
        wiki_path: Ruta al corpus de Wikipedia
        bible_path: Ruta al corpus bíblico
        output_path: Ruta de salida
        wiki_ratio: Proporción de Wikipedia (0.9 = 90% wiki, 10% bíblico)
    """
    print(f"\n📊 Creando corpus balanceado...")
    
    # Leer Wikipedia
    with open(wiki_path, 'r', encoding='utf-8') as f:
        wiki_text = f.read()
    
    # Leer texto bíblico
    with open(bible_path, 'r', encoding='utf-8') as f:
        bible_text = f.read()
    
    wiki_size = len(wiki_text.encode('utf-8'))
    
    # Calcular cuánto texto bíblico incluir
    bible_target = int(wiki_size * (1 - wiki_ratio) / wiki_ratio)
    bible_text_trimmed = bible_text[:bible_target] if len(bible_text.encode('utf-8')) > bible_target else bible_text
    
    # Combinar
    combined = wiki_text + '\n\n' + bible_text_trimmed
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(combined)
    
    final_size = len(combined.encode('utf-8'))
    
    print(f"   Wikipedia: {wiki_size/1024/1024:.2f} MB ({wiki_ratio*100:.0f}%)")
    print(f"   Bíblico: {len(bible_text_trimmed.encode('utf-8'))/1024/1024:.2f} MB ({(1-wiki_ratio)*100:.0f}%)")
    print(f"   Total: {final_size/1024/1024:.2f} MB")
    print(f"   Guardado en: {output_path}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Descargar corpus de Wikipedia para entrenamiento")
    parser.add_argument("--lang", choices=['en', 'es', 'both'], default='both',
                        help="Idioma a descargar (default: both)")
    parser.add_argument("--size", type=float, default=5.0,
                        help="Tamaño objetivo en MB (default: 5.0)")
    parser.add_argument("--output-dir", default="data",
                        help="Directorio de salida (default: data)")
    parser.add_argument("--create-balanced", action="store_true",
                        help="Crear también corpus balanceados con texto bíblico")
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if args.lang in ['en', 'both']:
        download_wikipedia_corpus('en', str(output_dir / 'en-wikipedia.txt'), args.size)
        
        if args.create_balanced:
            bible_path = output_dir / 'en-bible.txt'
            if bible_path.exists():
                create_balanced_corpus(
                    str(output_dir / 'en-wikipedia.txt'),
                    str(bible_path),
                    str(output_dir / 'en-final.txt')
                )
    
    if args.lang in ['es', 'both']:
        download_wikipedia_corpus('es', str(output_dir / 'es-wikipedia.txt'), args.size)
        
        if args.create_balanced:
            bible_path = output_dir / 'es-bible.txt'
            if bible_path.exists():
                create_balanced_corpus(
                    str(output_dir / 'es-wikipedia.txt'),
                    str(bible_path),
                    str(output_dir / 'es-final.txt')
                )
    
    print("\n🎉 ¡Descarga completada!")


