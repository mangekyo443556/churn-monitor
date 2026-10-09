# =============================================================================
# Dockerfile — la receta de la "caja" donde corren las Lambdas (Nivel 4)
#
# Equivale a DataScienceModelMonitor.Dockerfile de pipeline-model-monitor.
# Las 4 Lambdas usan ESTA misma imagen; cada una cambia solo el comando
# (CMD) que ejecuta. Ese cambio se configura en template.yaml (ImageConfig).
# =============================================================================

# 1. Punto de partida: imagen oficial de AWS para Lambda con Python 3.10.
#    Trae el "runtime" de Lambda y un emulador para probar en local.
#    Está basada en Amazon Linux 2: por eso fijamos versiones en pyproject.toml.
FROM public.ecr.aws/lambda/python:3.10

# 2. Dependencias primero (cambian poco). Docker guarda cada paso en caché:
#    si requirements.txt no cambió, no reinstala todo en cada build.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# 3. Después el código (cambia seguido).
COPY commons/             ${LAMBDA_TASK_ROOT}/commons/
COPY config/              ${LAMBDA_TASK_ROOT}/config/
COPY train_model/         ${LAMBDA_TASK_ROOT}/train_model/
COPY simulate_production/ ${LAMBDA_TASK_ROOT}/simulate_production/
COPY process_drift/       ${LAMBDA_TASK_ROOT}/process_drift/
COPY notify/              ${LAMBDA_TASK_ROOT}/notify/

# 4. Comando por defecto. template.yaml lo reemplaza para cada Lambda.
CMD ["notify.main.handler"]
