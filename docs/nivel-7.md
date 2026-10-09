# Nivel 7 · Paquetes privados con CodeArtifact (opcional)

**Objetivo:** publicar una librería propia en un repositorio privado y consumirla desde otro proyecto, como hace Vana con el paquete `vana`.

## Lo que tienes que entender

**Librería vs aplicación.** `churn-monitor` es una aplicación (`package-mode = false`): se ejecuta, no se instala. `nivel7-paquete-privado/churn-utils` es una librería: se construye en un archivo `.whl` y otros proyectos la instalan con `poetry add`.

**Repositorio de paquetes.** PyPI es el público. CodeArtifact es uno privado dentro de tu cuenta de AWS: solo entra quien tiene permiso.

**Dominio y repositorio.** En CodeArtifact, un dominio agrupa repositorios. Vana usa, por ejemplo, el dominio `vana-repositories-domain`.

**Token.** Para entrar, le pides a AWS un token temporal (12 horas por defecto) y se lo das a Poetry como contraseña. Es lo que hace `make codeartifact_setup` en `pipeline-model-monitor`.

## Costo

CodeArtifact tiene un nivel gratuito pequeño de almacenamiento y solicitudes. Confírmalo en la página de precios antes de crear el dominio, y bórralo al terminar.

## Pasos: publicar

```bash
# 1. Crear dominio y repositorio
aws codeartifact create-domain --domain practica
aws codeartifact create-repository --domain practica --repository python-privado

# 2. Obtener la URL del repositorio y un token
ENDPOINT=$(aws codeartifact get-repository-endpoint --domain practica \
  --repository python-privado --format pypi --query repositoryEndpoint --output text)
TOKEN=$(aws codeartifact get-authorization-token --domain practica \
  --query authorizationToken --output text)

# 3. Decirle a Poetry dónde publicar y con qué credenciales
cd nivel7-paquete-privado/churn-utils
poetry config repositories.practica "$ENDPOINT"
poetry config http-basic.practica aws "$TOKEN"

# 4. Construir y publicar
poetry publish --build -r practica
```

## Pasos: consumir

Desde la raíz de `churn-monitor`, en una rama de prueba:

```bash
poetry source add --priority=supplemental practica "${ENDPOINT}simple/"
poetry config http-basic.practica aws "$TOKEN"
poetry add churn-utils --source practica
```

Abre `pyproject.toml`: aparecieron la sección `[[tool.poetry.source]]` y la dependencia con `source = "practica"`. Es exactamente lo que tiene `pipeline-model-monitor` con `vana`.

Ahora puedes usar `from churn_utils import psi, psi_label` en el código.

## El problema con Docker

Al construir la imagen, `pip` también necesita el token para bajar `churn-utils`. `pipeline-model-monitor` lo resuelve con `poetry export --with-credentials`, que mete el token dentro de `requirements.txt` (por eso ese archivo nunca se sube a Git). Pruébalo:

```bash
poetry export -f requirements.txt --without-hashes --only main --with-credentials -o requirements.txt
grep churn-utils requirements.txt
```

## Ejercicios

1. Cambia `psi_label`, sube la versión a `0.1.1` en el `pyproject.toml` de la librería, publica y actualiza en el proyecto con `poetry update churn-utils`.
2. Espera a que venza el token (o usa uno inválido) y corre `poetry install` sin caché. Lee el error 401: es el que verás en Vana cuando olvides `make codeartifact_setup`.

## Limpiar

```bash
aws codeartifact delete-repository --domain practica --repository python-privado
aws codeartifact delete-domain --domain practica
```

## Terminaste cuando

- Publicaste una versión y la instalaste desde otro proyecto.
- Entiendes por qué `poetry install` falla sin token.
