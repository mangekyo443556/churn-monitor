# churn-monitor

Un mini monitor de drift para un modelo de churn, construido para **aprender paso a paso** las mismas piezas que usa `pipeline-model-monitor` en Vana: Poetry, `pyproject.toml`, YAML, tests, GitHub Actions, Docker, SAM, Step Functions y CodeArtifact.

Todo corre primero en tu máquina, y solo al final en **tu propia** cuenta de AWS. No toca nada de Vana.

## Qué hace

1. **Entrena** un modelo de churn con el dataset público Telco Customer Churn (7.032 clientes de una telefónica).
2. **Simula** datos de producción, deformándolos a propósito: subida de precios, ola de clientes nuevos, cambio de contratos.
3. **Mide el drift** de cada feature y de los scores del modelo (PSI, Jensen-Shannon, KS, Wasserstein).
4. **Avisa** por Slack si algo cambió más de lo permitido.

Resultado real de `make monitor SCENARIO=price_increase`:

```
:rotating_light: Drift detectado · *churn-v1* · 2026-10-08
Escenario simulado: `price_increase` · 1000 filas
Score promedio: entrenamiento 0.266 → hoy 0.338

:rotating_light: *feature_drift* (input) · 7% de features con drift
    ⚠️ `MonthlyCharges` psi=1.494 (umbral 0.2)
    · `TotalCharges` psi=0.042 (umbral 0.2)
:white_check_mark: *target_drift* (output) · 0% de features con drift
    · `score` psi=0.100 (umbral 0.2)
```

## Los niveles

Cada nivel agrega **una** tecnología. No pases al siguiente hasta que el anterior funcione.

| Nivel | Qué aprendes | Necesitas | Guía |
| --- | --- | --- | --- |
| 0 | Python, entornos virtuales, pip | Python 3.10 | [docs/nivel-0.md](docs/nivel-0.md) |
| 1 | Poetry, `pyproject.toml`, `poetry.lock` | Poetry 1.8.4 | [docs/nivel-1.md](docs/nivel-1.md) |
| 2 | Estructura del código, YAML de configuración, tests, mypy, Make | — | [docs/nivel-2.md](docs/nivel-2.md) |
| 3 | Git, GitHub, pull requests, GitHub Actions | Cuenta de GitHub | [docs/nivel-3.md](docs/nivel-3.md) |
| 4 | Docker e imágenes de Lambda | Docker Desktop | [docs/nivel-4.md](docs/nivel-4.md) |
| 5 | SAM: infraestructura como código, en local | SAM CLI | [docs/nivel-5.md](docs/nivel-5.md) |
| 6 | Tu cuenta de AWS: S3, Lambda, Step Functions, EventBridge, Slack | Cuenta de AWS | [docs/nivel-6.md](docs/nivel-6.md) |
| 7 | Paquetes privados con CodeArtifact (opcional) | Cuenta de AWS | [docs/nivel-7.md](docs/nivel-7.md) |

Los niveles 0 a 5 son gratis y no necesitan AWS.

## Arranque rápido (niveles 1 y 2)

```bash
pyenv local 3.10.12
poetry config virtualenvs.in-project true
make install        # dependencias exactas desde poetry.lock
make pipeline       # descarga datos, entrena, simula y mide drift
make ci             # mypy + tests (lo mismo que GitHub Actions)
make help           # todas las recetas
```

Prueba los otros escenarios: `make monitor SCENARIO=new_customers` (o `none`, `contract_shift`).

## Estructura y equivalencias con pipeline-model-monitor

```
churn-monitor/
├── pyproject.toml          Nivel 1 · dependencias y config de herramientas
├── poetry.lock             Nivel 1 · versiones exactas (no editar a mano)
├── Makefile                Nivel 2 · atajos: make test, make build...
├── config/drifts.yaml      Nivel 2 · dataset, umbrales y escenarios
├── commons/                Nivel 2 · config, almacenamiento local/S3, logger
├── train_model/            Lambda 1 · entrena (se corre a mano)
├── simulate_production/    Lambda 2 · fabrica el batch del día
├── process_drift/          Lambda 3 · calcula el drift
├── notify/                 Lambda 4 · manda el resumen a Slack
├── tests/                  Nivel 2 · 33 tests, sin internet ni AWS
├── local_runs/             Nivel 2 · correr las Lambdas en tu máquina
├── events/                 Nivel 4-5 · eventos JSON de ejemplo
├── .github/workflows/      Nivel 3 y 6 · tests.yml y deploy.yml
├── Dockerfile              Nivel 4 · la imagen de las 4 Lambdas
├── template.yaml           Nivel 5-6 · toda la infraestructura de AWS
├── samconfig.toml          Nivel 5-6 · opciones guardadas de SAM
├── nivel0/                 Nivel 0 · el mismo problema en un solo script
├── nivel7-paquete-privado/ Nivel 7 · una librería para publicar en CodeArtifact
└── docs/                   una guía por nivel + dataset alternativo
```

| Aquí | En pipeline-model-monitor |
| --- | --- |
| `simulate_production` → `process_drift` → `notify` | `get_models` → `process_model` (Map) → `notify_slack` |
| `config/drifts.yaml` | `config/drifts.yaml` |
| Métricas hechas a mano en `process_drift/metrics.py` | Librería Evidently |
| `commons/storage.py` (local o S3) | `adapters/` de cada Lambda |
| `local_runs/run_pipeline.py` | `local_runs/*.py` |
| `tests.yml` | `static-checks.yml` |
| `deploy.yml` manual con OIDC | `deploy.yml` automático por rama con claves |
| `nivel7-paquete-privado/churn-utils` | El paquete `vana` en CodeArtifact |

## Datos

Telco Customer Churn, publicado por IBM como dataset de ejemplo y difundido en Kaggle. `make data` lo baja de la [copia pública de IBM en GitHub](https://github.com/IBM/telco-customer-churn-on-icp4d), así no necesitas cuenta de Kaggle.

Para un caso más cercano a Vana, con drift **real** en el tiempo en lugar de simulado, mira [docs/dataset-alternativo.md](docs/dataset-alternativo.md) (Lending Club).
