# Jupyter Book · Heart Disease MLOps

Este directorio contiene la **versión documentada del proyecto** como Jupyter
Book.  Organiza todo el trabajo (contexto, notebooks, API, Docker, K8s, tests,
monitoreo y conclusiones) en capítulos y secciones navegables en HTML.

## Estructura

```
jupyter_book/
├── _config.yml             # Configuración global (título, extensiones, HTML)
├── _toc.yml                # Tabla de contenidos (capítulos y secciones)
├── intro.md                # Portada del libro
├── requirements-book.txt   # Dependencias para compilar el libro
│
├── 01_contexto/            # Cap. 1 — Introducción, dataset, arquitectura
├── 02_analisis/            # Cap. 2 — Demo de fuga de datos
│     ├── 00_intro_leakage.md       (teoría)
│     ├── 01_leakage_demo.ipynb     (notebook ejecutado)
│     └── 02_cierre_leakage.md      (lecciones)
├── 03_pipeline/            # Cap. 3 — Pipeline + GridSearchCV
│     ├── 00_intro_pipeline.md
│     ├── 01_model_pipeline_cv.ipynb
│     └── 02_cierre_pipeline.md
├── 04_despliegue/          # Cap. 4 — FastAPI, Docker, Kubernetes
├── 05_operaciones/         # Cap. 5 — Tests, monitoreo, CI/CD
└── 06_conclusiones/        # Cap. 6 — Cierre del libro
```

## Cómo compilar el libro

### 1 · Instalar Jupyter Book

```bash
pip install -r jupyter_book/requirements-book.txt
```

### 2 · Construir el HTML

Desde la **raíz del proyecto**:

```bash
jupyter-book build jupyter_book/
```

El HTML generado queda en `jupyter_book/_build/html/index.html`.  Se puede
abrir directamente en el navegador:

```bash
# En Windows (Git Bash)
start jupyter_book/_build/html/index.html

# En macOS
open jupyter_book/_build/html/index.html

# En Linux
xdg-open jupyter_book/_build/html/index.html
```

### 3 · Limpiar el build

```bash
jupyter-book clean jupyter_book/
```

## Notas importantes

- **Los notebooks no se re-ejecutan** al construir el libro
  (`execute_notebooks: "off"` en `_config.yml`).  Usa las salidas ya guardadas
  en el `.ipynb`.  Si actualizas el código, primero ejecuta el notebook en
  Jupyter / VS Code y vuelve a construir el libro.
- Los notebooks son **los mismos** que los de `/notebooks`.  Se copian aquí
  solamente para mantener una estructura auto-contenida del libro.
- Cada capítulo combina **markdown (narrativa)** y **notebook (ejecución)**
  para separar la explicación del código del código mismo.

## Publicación opcional

Para publicar el libro en GitHub Pages:

```bash
pip install ghp-import
jupyter-book build jupyter_book/
ghp-import -n -p -f jupyter_book/_build/html
```
