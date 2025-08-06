# Post Article Backup

Repositorio para respaldar y gestionar artículos de blog con imágenes locales.

## 📁 Estructura del Proyecto

```
post-article-backup/
├── images/                     # Imágenes descargadas del CDN
│   ├── hashnode_image_1.png   # Login de CodeCatalyst
│   ├── hashnode_image_2.png   # Pantalla principal
│   ├── hashnode_image_3.png   # Opciones de proyecto
│   ├── hashnode_image_4.png   # Blueprint selection
│   ├── hashnode_image_5.png   # Configuración del proyecto
│   ├── hashnode_image_6.png   # Configuración de cuenta
│   ├── hashnode_image_7.png   # Creación del proyecto
│   ├── hashnode_image_8.png   # Pipeline execution
│   ├── hashnode_image_9.png   # API test
│   └── hashnode_image_10.png  # DynamoDB
├── codecatalist.md            # Artículo original con imágenes locales
├── codecatalyst_dev_to.md     # Versión para dev.to con URLs de GitHub
├── download_images.py         # Script para descargar imágenes del CDN
├── update_references.py       # Script para actualizar referencias locales
├── requirements.txt           # Dependencias Python
└── README.md                 # Este archivo
```

## 🛠️ Scripts Configurados

### 1. `download_images.py`
Descarga automáticamente imágenes del CDN de Hashnode desde archivos markdown.

**Uso:**
```bash
pip install -r requirements.txt
python download_images.py
```

**Funcionalidades:**
- Busca archivos `.md` en el directorio
- Extrae URLs del CDN de Hashnode
- Descarga imágenes con nombres secuenciales
- Evita descargas duplicadas

### 2. `update_references.py`
Actualiza las referencias de imágenes en archivos markdown para usar rutas locales.

**Uso:**
```bash
python update_references.py
```

**Funcionalidades:**
- Reemplaza URLs del CDN con rutas locales
- Mantiene la posición original de las imágenes
- Preserva el texto alternativo

## 📝 Archivos de Contenido

### `codecatalist.md`
- Artículo original con imágenes locales
- Compatible con GitHub markdown
- Referencias: `images/hashnode_image_X.png`

### `codecatalyst_dev_to.md`
- Versión optimizada para dev.to
- Incluye front matter con metadatos
- URLs de GitHub raw para imágenes
- Formato: `https://raw.githubusercontent.com/olcortesb/post-article-backup/refs/heads/main/images/hashnode_image_X.png`

## 🚀 Flujo de Trabajo

1. **Descargar imágenes:**
   ```bash
   python download_images.py
   ```

2. **Actualizar referencias:**
   ```bash
   python update_references.py
   ```

3. **Para dev.to:** Usar `codecatalyst_dev_to.md` directamente

4. **Para GitHub:** Usar `codecatalist.md`

## 📋 Dependencias

- `requests==2.31.0` - Para descargar imágenes

## 🎯 Propósito

Este repositorio permite:
- ✅ Respaldar artículos con imágenes locales
- ✅ Independencia de CDNs externos
- ✅ Compatibilidad con múltiples plataformas
- ✅ Automatización del proceso de descarga
- ✅ Versionado de contenido y recursos