# Nivel 0 · Python a secas

**Objetivo:** correr el problema completo (entrenar, simular producción, medir drift) en un solo archivo, con las herramientas más básicas. Así ves el "qué" antes de preocuparte por el "cómo se organiza".

## Lo que tienes que entender

**Intérprete de Python.** Es el programa que ejecuta tu código. Puedes tener varios instalados (3.10, 3.12...). Este proyecto usa **3.10**, porque es la versión de la Lambda.

**pyenv.** Instala y cambia entre versiones de Python sin romper el Python del sistema operativo.

```bash
pyenv install 3.10.12
pyenv local 3.10.12      # esta carpeta usará 3.10.12 (crea .python-version)
python --version
```

**Entorno virtual (venv).** Una carpeta con su propio Python y sus propias librerías. Si instalas pandas dentro de un venv, solo existe ahí. Cada proyecto tiene el suyo, así no chocan versiones entre proyectos.

**pip y requirements.txt.** `pip` instala librerías desde PyPI. Un `requirements.txt` es una lista de librerías para instalar todas juntas.

## Pasos

```bash
cd nivel0
python -m venv .venv               # crea el entorno virtual
source .venv/bin/activate          # lo "enciende": el prompt cambia a (.venv)
pip install -r requirements.txt
python train_simple.py
deactivate                         # lo apaga
```

Salida esperada (aproximada):

```
7032 clientes, 26.6% se fueron
AUC en datos no vistos: 0.834

Drift por feature numérica (PSI):
  tenure          0.005
  MonthlyCharges  1.483  <-- DRIFT
  TotalCharges    0.003
```

## Qué está pasando

1. Se baja el CSV y se limpia (`TotalCharges` trae espacios vacíos que no son números).
2. Se separa 70 % para entrenar y 30 % que el modelo nunca ve.
3. Se entrena una regresión logística. El AUC (0.5 = azar, 1 = perfecto) dice qué tan bien separa a quienes se van.
4. Se simula "producción" subiendo los precios 25 % en ese 30 %.
5. Se compara cada columna entre entrenamiento y producción con **PSI** (Population Stability Index). Solo `MonthlyCharges` cambió, y PSI lo detecta.

## Ejercicios

1. Cambia el `1.25` por `1.05`. ¿El PSI sigue pasando de 0.2? ¿A partir de qué subida lo detecta?
2. Simula otro cambio: `production["tenure"] = production["tenure"] // 2`. ¿Qué columnas se mueven?
3. Borra `.venv`, créalo de nuevo e instala. Ahora imagina que un compañero instala dentro de un año: `requirements.txt` no tiene versiones, así que le tocarán versiones distintas a las tuyas. Ese es el problema que resuelve el Nivel 1.

## Terminaste cuando

- Sabes crear, activar y borrar un entorno virtual.
- Puedes explicar con tus palabras qué mide el PSI.
