#!/usr/bin/env python3
import re
from pathlib import Path

def update_image_references():
    md_files = list(Path(".").glob("*.md"))
    
    for md_file in md_files:
        print(f"Actualizando referencias en: {md_file}")
        
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Encontrar y reemplazar URLs de Hashnode con referencias locales
        urls = re.findall(r'https://cdn\.hashnode\.com/res/hashnode/image/upload/[^\s)]+', content)
        
        updated_content = content
        for i, url in enumerate(urls, 1):
            clean_url = url.split(' ')[0]
            local_path = f"images/hashnode_image_{i}.png"
            updated_content = updated_content.replace(url, local_path)
        
        # Escribir el archivo actualizado
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"Reemplazadas {len(urls)} referencias de imágenes")

if __name__ == "__main__":
    update_image_references()