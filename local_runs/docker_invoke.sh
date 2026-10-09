#!/usr/bin/env bash
# Ejecuta una Lambda dentro de su imagen Docker, en tu máquina (Nivel 4).
#
# La imagen base de AWS trae un "emulador de Lambda": al arrancar el contenedor
# queda escuchando en el puerto 8080, y le mandas el evento con un POST.
# La carpeta .local_bucket/ se monta dentro del contenedor en /tmp/bucket,
# así el contenedor lee y escribe los mismos archivos que el modo local.
#
# Uso: ./local_runs/docker_invoke.sh <imagen> <handler> <evento.json>
set -euo pipefail
IMAGE="$1"; HANDLER="$2"; EVENT="$3"
NAME="churn-monitor-invoke"

mkdir -p .local_bucket
docker rm -f "$NAME" >/dev/null 2>&1 || true
docker run -d --rm --name "$NAME" -p 9000:8080 \
  -v "$(pwd)/.local_bucket:/tmp/bucket" \
  -e STORAGE=local -e LOCAL_DATA_DIR=/tmp/bucket \
  "$IMAGE" "$HANDLER" >/dev/null
sleep 2

echo ">>> $HANDLER  (evento: $EVENT)"
curl -s -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" -d @"$EVENT"
echo
docker logs "$NAME" 2>&1 | grep -E "INFO|ERROR|Traceback" | tail -5 || true
docker stop "$NAME" >/dev/null
