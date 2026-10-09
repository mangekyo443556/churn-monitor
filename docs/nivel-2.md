# Nivel 2 · Estructura, configuración YAML, tests y Make

**Objetivo:** pasar del script único del Nivel 0 a un proyecto organizado como `pipeline-model-monitor`, donde cada pieza se puede probar sola.

## Lo que tienes que entender

**Una carpeta por Lambda.** `train_model/`, `simulate_production/`, `process_drift/` y `notify/` serán, en el Nivel 6, cuatro funciones distintas en AWS. Cada una tiene:

- `domain.py`: la lógica pura. Recibe DataFrames, devuelve resultados. No lee ni escribe archivos.
- `main.py`: el `handler(event, context)`, la puerta de entrada que llama AWS. Lee, llama al domain y guarda.

Separarlas permite testear la lógica sin disco ni AWS. `pipeline-model-monitor` lleva la idea más lejos (domain, use_case, ports, adapters), pero el principio es el mismo.

**El evento.** Cada handler recibe un diccionario (`event`) y devuelve otro. La salida de un paso es la entrada del siguiente:

```
simulate_production  →  {"date", "scenario", "batch_key"}
process_drift        →  {"date", "report_key", "alert", "drifted"}
notify               →  {"sent", "text"}
```

**Almacenamiento intercambiable.** `commons/storage.py` habla de "llaves" (`models/churn-v1/model.joblib`). Con `STORAGE=local` las guarda en `.local_bucket/`; con `STORAGE=s3`, en un bucket. El resto del código no se entera. Abre `.local_bucket/` después de correr el pipeline: es la misma estructura que tendrá S3.

**YAML.** Formato de configuración donde la indentación define la jerarquía. `config/drifts.yaml` tiene tres secciones: `dataset` (columnas), `drifts` (algoritmos y umbrales) y `simulation` (escenarios). `commons/config.py` lo lee y valida al arrancar.

**Tests con pytest.** Archivos `tests/test_*.py` con funciones `test_*` que usan `assert`. Los fixtures de `tests/conftest.py` preparan datos sintéticos y una carpeta temporal. `moto` simula S3 en memoria.

**mypy.** Revisa las anotaciones de tipos (`def f(x: int) -> str`) sin ejecutar el código. Detecta errores como pasar un texto donde se espera un número.

**Make.** Recetas con nombre en el `Makefile`. `make help` las lista todas.

## Pasos

```bash
make pipeline                         # datos + entrenamiento + monitoreo
make monitor SCENARIO=none            # control: no debería alertar
make monitor SCENARIO=new_customers   # drift en tenure y en los scores
make monitor SCENARIO=contract_shift  # drift categórico en Contract
make ci                               # mypy + tests
```

Mira los archivos generados en `.local_bucket/` y abre un `drift_report.json`.

## Qué esperar de cada escenario

| Escenario | Features con drift | Drift en scores |
| --- | --- | --- |
| `none` | Ninguna | No |
| `price_increase` | `MonthlyCharges` (PSI ≈ 1.5) | No, aunque sube (PSI ≈ 0.08) |
| `new_customers` | `tenure`, `TotalCharges` | Sí (PSI ≈ 0.27) |
| `contract_shift` | `Contract`, `tenure` | Sí (PSI ≈ 0.45) |

Fíjate en `price_increase`: los precios cambian mucho, pero los scores poco. Un drift en features no siempre mueve al modelo, y por eso se miden ambos.

## Ejercicios

1. **Solo YAML:** crea un escenario `senior_wave` con `oversample` sobre `SeniorCitizen` `eq` `"1"` y `share: 0.6`. Córrelo sin tocar Python.
2. **Umbrales:** cambia `numeric_algorithm` de `feature_drift` a `ks` y luego a `wasserstein`. ¿Qué escenarios siguen alertando? Ajusta `threshold` hasta que `none` no alerte y los otros sí.
3. **Un test que falla:** cambia en `metrics.py` el `np.log(q / p)` por `np.log(p / q)` y corre `make test`. Lee qué test lo detecta y deshaz el cambio.
4. **Escribe un test:** en `tests/test_train_and_simulate.py`, agrega uno que verifique que el escenario `contract_shift` deja 90 % de filas `Month-to-month`.
5. **Avanzado, como en Vana:** agrega `evidently = "0.6.5"` con `poetry add` y reescribe `psi_numeric` usando su TestSuite. Compara resultados y observa cuánto crece `poetry.lock`.

## En pipeline-model-monitor

`process_model/domain/drift_processor.py` hace lo que aquí hace `process_drift/`, con Evidently. `config/drifts.yaml` tiene la misma idea. `local_runs/` existe allá con el mismo propósito.

## Terminaste cuando

- Puedes seguir un evento desde `simulate_production` hasta el mensaje final.
- Sabes agregar un escenario o cambiar un umbral solo con YAML.
- `make ci` pasa.
