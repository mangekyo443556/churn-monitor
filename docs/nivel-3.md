# Nivel 3 · Git, GitHub y GitHub Actions

**Objetivo:** que cada cambio pase por una rama y un pull request, y que una máquina de GitHub corra los tests sola.

## Lo que tienes que entender

**Git** guarda la historia del código en *commits*. Una **rama** es una línea de trabajo paralela: trabajas en `feature/algo` sin tocar `main`.

**GitHub** aloja el repositorio. Un **pull request (PR)** es la propuesta de unir tu rama a otra, con espacio para revisión.

**GitHub Actions** ejecuta *workflows*: archivos YAML en `.github/workflows/`. Cada uno dice **cuándo** correr (`on:`) y **qué pasos** ejecutar (`steps:`) en una máquina temporal de GitHub.

## Pasos

1. Crea un repo **personal** en GitHub llamado `churn-monitor` (privado o público; los públicos tienen minutos ilimitados de Actions).
2. Súbelo:

```bash
cd churn-monitor
git init
git add .
git commit -m "Primera versión de churn-monitor"
git branch -M main
git remote add origin git@github.com:TU_USUARIO/churn-monitor.git
git push -u origin main
```

3. Abre la pestaña **Actions** del repo: el workflow `tests` corrió por el push a `main`.
4. Haz tu primer PR:

```bash
git checkout -b feature/escenario-senior
# agrega el escenario senior_wave del Nivel 2 en config/drifts.yaml
poetry version patch                      # sube la versión: 0.1.0 -> 0.1.1
make ci
git add . && git commit -m "Agrega escenario senior_wave"
git push -u origin feature/escenario-senior
```

5. En GitHub, abre el PR hacia `main`. Espera a que `tests` quede en verde y haz merge.
6. Protege `main`: Settings → Branches → Add rule → `main` → "Require status checks to pass" → elige `tests`. Ahora nadie puede hacer merge si los tests fallan.

## Lee el workflow

Abre `.github/workflows/tests.yml`. Cada `step` es lo que harías a mano en una máquina nueva: bajar el código, instalar Python 3.10.12, instalar Poetry, `poetry install`, `make check`, `make test`.

## Ejercicios

1. Haz un PR que rompa un test a propósito. Mira cómo se pone rojo y cómo lees el error en los logs de Actions. Ciérralo sin hacer merge.
2. Agrega al workflow un paso que imprima `poetry show --top-level`.
3. Prueba el flujo de Vana a escala pequeña: crea una rama `dev`, haz los PR hacia `dev` y luego de `dev` a `main`.

## En pipeline-model-monitor

`static-checks.yml` corre en cada PR (como `tests.yml`), y `deploy.yml` despliega con cada push a `dev`, `qa` o `main`, cada rama a su propia cuenta de AWS.

## Terminaste cuando

- Hiciste un PR con tests en verde y uno en rojo.
- `main` está protegida.
