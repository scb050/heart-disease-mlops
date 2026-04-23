# 5.3 Integración continua con GitHub Actions

Los tests sólo sirven si **se ejecutan**.  Un workflow de CI automatiza esa
ejecución en cada push y pull request, impidiendo que código roto llegue a
`main`.

## El workflow completo

El archivo [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) define
un pipeline sencillo pero efectivo:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build-and-validate:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout del repositorio
        uses: actions/checkout@v4

      - name: Configurar Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.10"

      - name: Instalar dependencias
        run: |
          python -m pip install --upgrade pip
          pip install -r docker/requirements.txt
          pip install pytest==8.3.3 httpx==0.27.2 flake8==7.1.1

      - name: Verificar sintaxis de app
        run: |
          python -m compileall app

      - name: Lint con flake8
        run: |
          flake8 app --max-line-length=300 --extend-ignore=E203,W503

      - name: Ejecutar tests con pytest
        run: |
          pytest tests/ -v
```

## Desglose por etapas

### `on` — cuándo se dispara

```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
```

Se corre en **dos eventos**:

1. **Push a `main`** → validación de que lo que se mergeó está sano.
2. **Pull request hacia `main`** → bloquea merges si falla.

### `Checkout del repositorio`

Clona el repo en la máquina de GitHub Actions.  Usamos `actions/checkout@v4`,
la versión estable actual.

### `Configurar Python`

```yaml
python-version: "3.10"
```

Fijamos la misma versión que el Dockerfile.  **Consistencia total** entre CI y
producción.

### `Instalar dependencias`

Instala lo mismo que correrá en producción (`docker/requirements.txt`) más
las herramientas de desarrollo (`pytest`, `httpx`, `flake8`).  `httpx` es
necesario porque el `TestClient` de FastAPI lo usa por debajo.

### `Verificar sintaxis de app`

```bash
python -m compileall app
```

Compila todo el módulo `app/` sin ejecutarlo.  Si hay **errores de sintaxis**
ni siquiera llega a la siguiente etapa.  Es la forma más barata de atrapar
regresiones obvias.

### `Lint con flake8`

```bash
flake8 app --max-line-length=300 --extend-ignore=E203,W503
```

Estilo de código:

- `--max-line-length=300` → relajado porque el dashboard HTML embebido en
  `api.py` tiene líneas largas.
- `--extend-ignore=E203,W503` → ignora dos reglas que entran en conflicto con
  el formato Black.

### `Ejecutar tests con pytest`

El paso final corre toda la suite de tests en modo verboso.  Si algún test
falla, el job entero falla y GitHub marca la PR como bloqueada.

## El ciclo completo

```
Developer push / PR
        │
        ▼
   GitHub Actions
        │
   ┌────┴────┬─────────┬──────────┐
   ▼         ▼         ▼          ▼
Checkout  Install   Compile    pytest
          deps      check
        │
        ▼
Success → merge permitido
Failure → merge bloqueado, notificación al autor
```

## Buenas prácticas aplicadas

```{admonition} Fijar versiones
:class: tip

Todas las herramientas externas están pinneadas (`pytest==8.3.3`, `flake8==7.1.1`).
Esto evita el clásico "funcionaba ayer" cuando una herramienta saca un major
con cambios incompatibles.
```

```{admonition} Mismos requirements en CI y producción
:class: tip

La CI instala **exactamente** `docker/requirements.txt`, que es lo que usa la
imagen Docker.  Si algo pasa en CI, pasa en producción; si algo falla en CI,
falla antes de llegar a producción.
```

## Evolución natural del pipeline

El CI actual valida el código.  Un paso siguiente sería un pipeline de **CD**
(continuous deployment) que, después de que CI pase, haga:

1. `docker build` de la imagen.
2. `docker push` a un registro.
3. `kubectl rollout` del deployment.
4. Test de humo contra `/health` después del rollout.

Esto convierte un push a `main` en un **despliegue automático** a producción,
con rollback automático si el health check falla.
