"""Nivel 0: todo en un solo script, sin Poetry, sin estructura, sin AWS.

Objetivo: ver el problema completo de un vistazo antes de repartirlo en piezas.
    1. Leer datos  2. Entrenar  3. Simular producción  4. Medir drift

Cómo correrlo (desde la carpeta nivel0/):
    python3.10 -m venv .venv
    source .venv/bin/activate          # en Windows/WSL2 igual
    pip install -r requirements.txt
    python train_simple.py

Fíjate en que este script tiene TODO mezclado: rutas, columnas, umbrales,
lógica y prints. En el Nivel 2 cada cosa se va a su lugar.
"""
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

URL = "https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv"
CSV = Path("telco.csv")
NUMERIC = ["tenure", "MonthlyCharges", "TotalCharges"]
CATEGORICAL = ["Contract", "InternetService", "PaymentMethod", "SeniorCitizen"]

# 1. Leer datos ---------------------------------------------------------------
if not CSV.exists():
    print("Descargando dataset...")
    urllib.request.urlretrieve(URL, CSV)
df = pd.read_csv(CSV)
df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
df = df.dropna(subset=NUMERIC)
df["SeniorCitizen"] = df["SeniorCitizen"].astype(str)
y = (df["Churn"] == "Yes").astype(int)
print(f"{len(df)} clientes, {y.mean():.1%} se fueron")

# 2. Entrenar -----------------------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    df[NUMERIC + CATEGORICAL], y, test_size=0.3, random_state=42, stratify=y
)
model = Pipeline([
    ("prep", ColumnTransformer([
        ("num", StandardScaler(), NUMERIC),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
    ])),
    ("clf", LogisticRegression(max_iter=1000)),
])
model.fit(X_train, y_train)
print(f"AUC en datos no vistos: {roc_auc_score(y_test, model.predict_proba(X_test)[:, 1]):.3f}")

# 3. Simular "producción": subimos los precios 25 % ----------------------------
production = X_test.copy()
production["MonthlyCharges"] = production["MonthlyCharges"] * 1.25


# 4. Medir drift con PSI ------------------------------------------------------
def psi(reference: pd.Series, current: pd.Series, bins: int = 10) -> float:
    """Population Stability Index. < 0.1 estable, 0.1-0.25 moderado, > 0.25 fuerte."""
    edges = np.unique(np.quantile(reference, np.linspace(0, 1, bins + 1)))
    edges[0], edges[-1] = -np.inf, np.inf
    p = np.histogram(reference, edges)[0] / len(reference)
    q = np.histogram(current, edges)[0] / len(current)
    p, q = np.clip(p, 1e-6, None), np.clip(q, 1e-6, None)
    return float(np.sum((q - p) * np.log(q / p)))


print("\nDrift por feature numérica (PSI):")
for col in NUMERIC:
    value = psi(X_train[col], production[col])
    flag = "  <-- DRIFT" if value > 0.2 else ""
    print(f"  {col:15s} {value:.3f}{flag}")
