#!/usr/bin/env python3
import os
import re
import requests
from urllib.parse import urlparse
from pathlib import Path

def download_hashnode_images():
    images_dir = Path("images")
    images_dir.mkdir(exist_ok=True)
    
    md_files = list(Path(".").glob("*.md"))
    if not md_files:
        print("No se encontraron archivos .md")
        return
    
    downloaded = 0
    
    for md_file in md_files:
        print(f"Procesando: {md_file}")
        
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Buscar URLs de imágenes del CDN de Hashnode
        urls = re.findall(r'https://cdn\.hashnode\.com/res/hashnode/image/upload/[^\s)]+', content)
        
        print(f"Encontradas {len(urls)} imágenes")
        
        for url in urls:
            try:
                # Limpiar la URL (remover align y otros parámetros)
                clean_url = url.split(' ')[0]
                
                # Generar nombre de archivo único
                filename = f"hashnode_image_{downloaded + 1}.png"
                filepath = images_dir / filename
                
                if not filepath.exists():
                    print(f"Descargando: {filename}")
                    response = requests.get(clean_url)
                    response.raise_for_status()
                    
                    with open(filepath, 'wb') as img_file:
                        img_file.write(response.content)
                    
                    downloaded += 1
                else:
                    print(f"Ya existe: {filename}")
                    
            except Exception as e:
                print(f"Error descargando {clean_url}: {e}")
    
    print(f"\nDescarga completada. {downloaded} imágenes descargadas en la carpeta 'images'")

if __name__ == "__main__":
    download_hashnode_images()