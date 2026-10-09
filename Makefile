# =============================================================================
# Makefile — atajos para no recordar comandos largos (Nivel 2 en adelante)
#
# Uso:  make <receta>        Ejemplo: make test
#       make help            lista todas las recetas
#
# OJO: las líneas de comandos van indentadas con TAB, no con espacios.
# =============================================================================

.PHONY: help install data train monitor pipeline test check ci export \
        docker-build docker-train docker-monitor \
        build validate local-notify deploy upload-data invoke-train start-execution destroy

SCENARIO ?= price_increase
IMAGE    ?= churn-monitor:local
STACK    ?= churn-monitor-dev
VERSION  := $(shell poetry version -s 2>/dev/null)

help:  ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# --- Nivel 1-2: trabajo local ------------------------------------------------

install:  ## Instala dependencias exactamente como dice poetry.lock
	poetry check --lock
	poetry install

data:  ## Descarga el dataset Telco a .local_bucket/
	poetry run python local_runs/download_data.py

train:  ## Entrena el modelo (Lambda train_model, en local)
	poetry run python local_runs/run_pipeline.py train

monitor:  ## Corre simular -> drift -> notificar. Ej: make monitor SCENARIO=new_customers
	poetry run python local_runs/run_pipeline.py monitor --scenario $(SCENARIO)

pipeline: data train monitor  ## Todo desde cero: datos, entrenamiento y monitoreo

test:  ## Tests con cobertura (falla si baja de 70 %)
	poetry run pytest --cov=. --cov-report=term-missing

check:  ## Revisión de tipos con mypy (modo estricto)
	poetry run mypy .

ci: check test  ## Lo mismo que corre GitHub Actions en cada pull request

# --- Nivel 4: Docker en local ------------------------------------------------

export:  ## Traduce poetry.lock a requirements.txt (lo que instala Docker)
	poetry check --lock
	poetry export -f requirements.txt --without-hashes --only main --output requirements.txt

docker-build: export  ## Construye la imagen de Lambda en tu máquina
	docker build -t $(IMAGE) .

docker-train: docker-build  ## Entrena DENTRO del contenedor, usando .local_bucket/
	./local_runs/docker_invoke.sh $(IMAGE) train_model.main.handler events/train.json

docker-monitor: docker-build  ## Simula + drift + notifica dentro del contenedor
	./local_runs/docker_invoke.sh $(IMAGE) simulate_production.main.handler events/simulate.json
	./local_runs/docker_invoke.sh $(IMAGE) process_drift.main.handler events/process_drift.json
	./local_runs/docker_invoke.sh $(IMAGE) notify.main.handler events/notify.json

# --- Nivel 5: SAM en local ---------------------------------------------------

validate:  ## Revisa que template.yaml sea válido
	sam validate --lint

build: export  ## Construye las 4 Lambdas con SAM (igual que el CI)
	sam build

local-notify: build  ## Ejecuta la Lambda de notificación con SAM, sin AWS
	sam local invoke NotifyFunction --event events/notify_inline.json

# --- Nivel 6: tu cuenta de AWS ----------------------------------------------
# Requieren credenciales (aws sts get-caller-identity debe funcionar).

deploy: build  ## Crea o actualiza el stack en AWS (pide confirmación)
	sam deploy --parameter-overrides Environment=dev Version=$(VERSION)

upload-data:  ## Sube el CSV al bucket del stack
	aws s3 cp .local_bucket/data/raw/telco.csv s3://$$(./local_runs/stack_output.sh $(STACK) DataBucketName)/data/raw/telco.csv

invoke-train:  ## Entrena el modelo en la Lambda de AWS
	sam remote invoke TrainModelFunction --stack-name $(STACK) --event '{}'

start-execution:  ## Lanza la Step Function a mano. Ej: make start-execution SCENARIO=contract_shift
	aws stepfunctions start-execution \
		--state-machine-arn $$(./local_runs/stack_output.sh $(STACK) StateMachineArn) \
		--input '{"scenario": "$(SCENARIO)"}'

destroy:  ## Borra TODO lo creado en AWS (vacía el bucket primero)
	aws s3 rm s3://$$(./local_runs/stack_output.sh $(STACK) DataBucketName) --recursive
	sam delete --stack-name $(STACK)
