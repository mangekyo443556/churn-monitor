# Nivel 4 · Docker e imágenes de Lambda

**Objetivo:** empaquetar el código con todo lo que necesita en una imagen, y ejecutar las Lambdas dentro de esa imagen en tu máquina, exactamente como correrán en AWS.

## Lo que tienes que entender

**Imagen.** Una "caja" sellada con sistema operativo mínimo, Python, librerías y tu código. Se construye una vez y da el mismo resultado en cualquier máquina.

**Contenedor.** Una imagen en ejecución. Puedes arrancar muchos contenedores de la misma imagen.

**Dockerfile.** La receta de la imagen. Ábrelo: cada línea está comentada.

- `FROM` elige la imagen de partida. Usamos la oficial de AWS para Lambda con Python 3.10, la misma de `pipeline-model-monitor`.
- `COPY` mete archivos en la imagen.
- `RUN` ejecuta un comando al construirla (instalar librerías).
- `CMD` es lo que se ejecuta al arrancar. Aquí, qué `handler` corre.

**Por qué `requirements.txt` otra vez.** Docker no usa Poetry: instala con `pip`. `make export` traduce `poetry.lock` a un `requirements.txt` con las mismas versiones exactas. Poetry decide; Docker obedece.

**El emulador de Lambda.** La imagen base trae un programa que, al arrancar, imita a AWS Lambda: escucha en el puerto 8080 y espera que le mandes un evento por HTTP.

**Montar una carpeta (volumen).** Con `-v` le prestas una carpeta de tu máquina al contenedor. Montamos `.local_bucket/` en `/tmp/bucket`, así el contenedor lee y escribe los mismos archivos que el modo local.

## Pasos

Instala [Docker Desktop](https://www.docker.com/products/docker-desktop/) (en Windows, con integración WSL2) y verifica con `docker run hello-world`.

```bash
make data                  # si aún no tienes el CSV en .local_bucket/
make docker-build          # export + docker build (la primera vez tarda)
docker images              # ahí está churn-monitor:local
make docker-train          # entrena DENTRO del contenedor
make docker-monitor        # simula, mide drift y notifica, cada paso en su contenedor
```

Mira `local_runs/docker_invoke.sh` para ver qué hace cada invocación: arranca el contenedor con un handler, le manda el evento con `curl` y lo detiene.

Para hacerlo a mano:

```bash
docker run --rm -p 9000:8080 \
  -v "$(pwd)/.local_bucket:/tmp/bucket" -e STORAGE=local -e LOCAL_DATA_DIR=/tmp/bucket \
  churn-monitor:local process_drift.main.handler

# en otra terminal:
curl -X POST http://localhost:9000/2015-03-31/functions/function/invocations -d @events/process_drift.json
```

## Ejercicios

1. Cambia una línea de `notify/domain.py` y reconstruye. Fíjate en que Docker reutiliza la capa de `pip install` (dice `CACHED`): por eso las dependencias se copian antes que el código.
2. Entra a la imagen y explórala: `docker run --rm -it --entrypoint bash churn-monitor:local`, luego `ls /var/task` y `python --version`.
3. Agrega `COPY tests/ ...` al Dockerfile, reconstruye y compara el tamaño con `docker images`. Deshazlo: los tests no deben ir en producción.

## Lección del repo real

La imagen base usa Amazon Linux 2. Algunas librerías nuevas ya no publican binarios para sistemas tan viejos, y entonces `pip` intenta compilarlas y falla. Por eso las versiones están fijas. Este proyecto ya está verificado: las 17 dependencias de `requirements.txt` tienen binarios compatibles.

## En pipeline-model-monitor

`DataScienceModelMonitor.Dockerfile` hace lo mismo para sus 4 Lambdas, y agrega la extensión de Datadog.

## Terminaste cuando

- `make docker-monitor` imprime el reporte desde los contenedores.
- Puedes explicar la diferencia entre imagen y contenedor.
