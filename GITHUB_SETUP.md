# 🚀 Guía para Subir el Proyecto a GitHub

## Paso 1: Inicializar Git Localmente

Abre la terminal en la carpeta del proyecto y ejecuta:

```bash
cd "c:\Users\byed2\Documents\miacd\Vision Computarizada\audiolouder"

# Inicializar repositorio Git
git init

# Verificar que se creó correctamente
git status
```

## Paso 2: Configurar Git (Si es primera vez)

```bash
# Configurar tu nombre
git config --global user.name "Tu Nombre"

# Configurar tu email (usa el mismo que tu cuenta de GitHub)
git config --global user.email "tu-email@ejemplo.com"

# Verificar configuración
git config --list
```

## Paso 3: Agregar Archivos al Staging

```bash
# Ver qué archivos se van a agregar (debe respetar .gitignore)
git status

# Agregar todos los archivos (excepto los de .gitignore)
git add .

# Verificar archivos agregados
git status
```

**⚠️ Archivos que NO deben subirse (están en .gitignore):**
- `.env` (contiene API keys)
- `ml_token.json` (token de Mercado Libre)
- `__pycache__/` (archivos compilados)
- `.venv/` (entorno virtual)
- `pricing_analysis*.json` (outputs temporales)

## Paso 4: Hacer el Commit Inicial

```bash
git commit -m "feat: Initial commit - Louder Pricing Intelligence system

- Nueva arquitectura con SearchStrategyAgent
- Pipeline de 6 pasos (extracción, búsqueda, scraping, matching, stats, pricing)
- Soporte para análisis de productos pivote por URL
- Web scraping de Mercado Libre sin API
- Documentación completa y actualizada
"
```

## Paso 5: Crear Repositorio en GitHub

### Opción A: Desde la Web (Más Fácil)

1. Ve a https://github.com
2. Click en el botón **"+"** (arriba derecha) → **"New repository"**
3. Configura el repositorio:
   - **Repository name**: `louder-pricing-intelligence`
   - **Description**: `Sistema inteligente de análisis de precios para e-commerce con agentes LLM`
   - **Visibility**: 
     - ✅ **Public** (si quieres que sea visible para todos)
     - ✅ **Private** (si quieres mantenerlo privado)
   - **❌ NO selecciones** "Add a README file" (ya tenemos uno)
   - **❌ NO selecciones** "Add .gitignore" (ya tenemos uno)
   - **❌ NO selecciones** "Choose a license" (podemos agregarlo después)
4. Click **"Create repository"**

### Opción B: Desde GitHub CLI (Si tienes gh instalado)

```bash
# Instalar GitHub CLI (si no lo tienes)
# Descargar desde: https://cli.github.com/

# Autenticarse
gh auth login

# Crear repositorio
gh repo create louder-pricing-intelligence --public --source=. --remote=origin
```

## Paso 6: Conectar Repositorio Local con GitHub

Después de crear el repo en GitHub, copia los comandos que aparecen o usa estos:

```bash
# Agregar el remote (reemplaza TU_USUARIO con tu usuario de GitHub)
git remote add origin https://github.com/TU_USUARIO/louder-pricing-intelligence.git

# Verificar que se agregó correctamente
git remote -v

# Renombrar rama principal a 'main' (estándar actual de GitHub)
git branch -M main
```

## Paso 7: Subir el Código a GitHub

```bash
# Push inicial
git push -u origin main
```

Si te pide autenticación:
- **Usuario**: Tu usuario de GitHub
- **Password**: Usa un **Personal Access Token** (NO tu contraseña)

### Crear Personal Access Token (PAT):
1. Ve a https://github.com/settings/tokens
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Configura:
   - **Note**: `Louder Project Token`
   - **Expiration**: 90 días (o lo que prefieras)
   - **Scopes**: Selecciona `repo` (acceso completo a repos)
4. Click **"Generate token"**
5. **⚠️ COPIA EL TOKEN** (solo se muestra una vez)
6. Usa este token como password cuando Git te lo pida

## Paso 8: Verificar en GitHub

1. Ve a `https://github.com/TU_USUARIO/louder-pricing-intelligence`
2. Debes ver todos tus archivos
3. El README.md se mostrará automáticamente en la página principal

## 📋 Comandos Resumidos (Copy-Paste)

```bash
# 1. Inicializar y configurar
cd "c:\Users\byed2\Documents\miacd\Vision Computarizada\audiolouder"
git init
git config --global user.name "Tu Nombre"
git config --global user.email "tu-email@ejemplo.com"

# 2. Primer commit
git add .
git commit -m "feat: Initial commit - Louder Pricing Intelligence system"

# 3. Conectar con GitHub (reemplaza TU_USUARIO)
git remote add origin https://github.com/TU_USUARIO/louder-pricing-intelligence.git
git branch -M main

# 4. Subir
git push -u origin main
```

## 🔄 Comandos para Futuros Cambios

Cuando hagas cambios en el futuro:

```bash
# Ver archivos modificados
git status

# Agregar cambios
git add .

# Hacer commit
git commit -m "descripción de los cambios"

# Subir a GitHub
git push
```

## 🏷️ Sugerencias de Nombres de Commits

Usa prefijos para organizar commits:

- `feat:` - Nueva funcionalidad
- `fix:` - Corrección de bugs
- `docs:` - Cambios en documentación
- `refactor:` - Refactorización de código
- `test:` - Agregar o modificar tests
- `chore:` - Tareas de mantenimiento

Ejemplos:
```bash
git commit -m "feat: add support for price history tracking"
git commit -m "fix: correct IQR outlier detection algorithm"
git commit -m "docs: update README with new architecture"
```

## 🎨 Mejorar tu Repositorio (Opcional)

### 1. Agregar Topics (Etiquetas)

En tu repo de GitHub:
- Click en ⚙️ (Settings) o el engranaje junto a "About"
- Agregar topics: `python`, `llm`, `pricing`, `e-commerce`, `langchain`, `openai`, `web-scraping`, `mercado-libre`

### 2. Crear un LICENSE

Si quieres agregar licencia:
```bash
# Crear archivo LICENSE
# GitHub tiene plantillas: Add file → Create new file → "LICENSE"
```

Sugerencia: MIT License (permisiva) o GPL (copyleft)

### 3. Agregar Badges al README

Agrega al inicio de README.md:
```markdown
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![LangChain](https://img.shields.io/badge/🦜_LangChain-0.1.0-green.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-orange.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
```

### 4. Crear CONTRIBUTING.md

Si quieres que otros contribuyan:
```markdown
# Contributing to Louder Pricing Intelligence

¡Gracias por tu interés en contribuir!

## Cómo Contribuir
1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'feat: add nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request
```

## ⚠️ Importante: Seguridad

### Antes de hacer push, VERIFICA que estos archivos NO estén en Git:

```bash
# Ver qué archivos se subirán
git status

# Verificar que estos NO aparezcan:
# ❌ .env
# ❌ ml_token.json
# ❌ .venv/
# ❌ __pycache__/
```

### Si accidentalmente subiste información sensible:

```bash
# Remover archivo del historial
git rm --cached archivo-sensible
git commit -m "chore: remove sensitive file"
git push

# Si ya subiste tokens/keys:
# ⚠️ REGENERA inmediatamente las keys en OpenAI/ML
```

## 📞 Solución de Problemas

### Error: "failed to push some refs"
```bash
# Hacer pull primero
git pull origin main --rebase
git push
```

### Error: "Authentication failed"
- Usa un Personal Access Token, NO tu contraseña
- Verifica que el token tenga scope `repo`

### Quitar archivos del staging
```bash
# Quitar un archivo
git reset HEAD archivo.txt

# Quitar todos
git reset HEAD .
```

### Ver el historial
```bash
# Ver commits
git log --oneline

# Ver cambios en un archivo
git log --oneline -- archivo.py
```

## ✅ Checklist Final

Antes de hacer el push inicial, verifica:

- [ ] `.gitignore` está actualizado
- [ ] `.env` NO está en staging
- [ ] `ml_token.json` NO está en staging
- [ ] README.md está actualizado
- [ ] Has probado que el demo funciona
- [ ] Commit message es descriptivo
- [ ] Repositorio en GitHub está creado
- [ ] Remote está configurado correctamente

---

**¡Listo!** Tu proyecto estará en GitHub y podrás compartirlo con tu equipo o comunidad. 🎉
