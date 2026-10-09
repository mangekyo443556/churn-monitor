# Dataset alternativo: Lending Club (drift real en crédito)

Telco es ideal para aprender, pero tiene una limitación: **no tiene fechas**. Todo el drift de este proyecto es fabricado. En Vana el drift ocurre solo, con el paso del tiempo: cambian los clientes, la economía y las políticas de crédito.

## La propuesta

**Lending Club Loan Data**, disponible en Kaggle (búscalo como "Lending Club Loan Data"; el archivo principal se llama `accepted_2007_to_2018Q4.csv`).

Por qué encaja mejor con Vana:

- **Es crédito.** Préstamos personales con monto, tasa de interés, ingreso, endeudamiento (DTI), puntaje FICO, grado de riesgo y propósito. La variable objetivo es si el préstamo terminó pagado (`Fully Paid`) o en pérdida (`Charged Off`): es un modelo de riesgo, como los de Vana.
- **Tiene fecha de emisión** (`issue_d`), de 2007 a 2018. Puedes entrenar con un periodo y monitorear los meses siguientes, y el drift aparece solo.
- **Tiene cambios reales documentables.** A lo largo de esos años cambiaron la mezcla de grados, las tasas y el perfil de los solicitantes. El monitor tiene algo real que encontrar.

Lo que cuesta:

- **Es grande:** más de 2 millones de filas y unas 150 columnas (más de 1 GB). Hay que reducirlo antes: quedarse con 12–15 columnas y, si hace falta, una muestra.
- **Tiene trampas de "fuga de información".** Columnas como `total_pymnt`, `recoveries` o `last_pymnt_d` se conocen *después* de dar el préstamo. Si el modelo las usa, parece buenísimo pero es inútil. Es una lección valiosa para riesgo crediticio.
- **Hay que filtrar estados.** Solo sirven préstamos terminados: `Fully Paid` y `Charged Off`. Los `Current` todavía no tienen resultado.

## Cómo adaptarlo

### 1. Reducir el archivo (una vez, en tu máquina)

```python
import pandas as pd

cols = ["issue_d", "loan_status", "loan_amnt", "term", "int_rate", "grade",
        "emp_length", "home_ownership", "annual_inc", "purpose", "dti",
        "fico_range_low", "revol_util", "open_acc"]
df = pd.read_csv("accepted_2007_to_2018Q4.csv", usecols=cols, low_memory=False)
df = df[df["loan_status"].isin(["Fully Paid", "Charged Off"])]
df["issue_d"] = pd.to_datetime(df["issue_d"], format="%b-%Y")
df = df[(df["issue_d"] >= "2014-01-01") & (df["issue_d"] < "2017-01-01")]
df.to_csv("lending_club_2014_2016.csv", index=False)
```

### 2. Cambiar `config/drifts.yaml`

```yaml
model_name: credit-risk-v1
dataset:
  raw_key: data/raw/lending_club_2014_2016.csv
  id_column: issue_d          # no hay id; cualquier columna que no sea feature
  target: loan_status
  positive_label: "Charged Off"
  date_column: issue_d        # NUEVO
  train_until: "2015-01-01"   # NUEVO: entrena con 2014
  numeric_features: [loan_amnt, int_rate, annual_inc, dti, fico_range_low, revol_util, open_acc]
  categorical_features: [term, grade, emp_length, home_ownership, purpose]
```

### 3. Cambiar el código (este es el ejercicio)

- **`commons/config.py`:** agregar `date_column` y `train_until` (opcionales) a `DatasetConfig`.
- **`train_model/domain.py`:** si hay `date_column`, separar por fecha en vez de al azar. Baseline = antes de `train_until`; holdout = después.
- **`simulate_production`:** agregar un modo `month` que, en lugar de deformar datos, tome del holdout los préstamos del mes indicado en el evento (`{"month": "2016-03"}`).
- **Escenarios:** ya no hacen falta para provocar drift; quedan para pruebas.

Después corre el monitor mes por mes (2015-01, 2015-02... 2016-12) y grafica cómo crece el PSI de cada feature con el tiempo. Así se ve el drift natural, que es lo que el monitor de Vana vigila todos los días.

## Otra opción más liviana

**Bike Sharing Dataset (UCI)**: alquileres diarios y por hora de bicicletas en Washington, 2011–2012, con clima y fecha. Es chico (unas 17.000 filas por hora) y tiene drift estacional muy visible: invierno contra verano. No es crédito, y el modelo sería de regresión (cuántas bicicletas), pero es una buena forma de ver drift real sin lidiar con un archivo gigante.
