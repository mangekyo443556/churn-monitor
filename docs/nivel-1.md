# Nivel 1 · Poetry, pyproject.toml y poetry.lock

**Objetivo:** que cualquier persona (o servidor) instale exactamente las mismas versiones que tú, siempre.

## Lo que tienes que entender

**TOML.** Un formato de texto para configuración: secciones entre corchetes y `clave = valor`. No hace nada solo; lo lee una herramienta.

```toml
[tool.poetry.dependencies]
pandas = "2.2.2"      # exactamente esta versión
pyyaml = "^6.0"       # cualquier 6.x (6.0, 6.1...), pero no 7.0
```

**pyproject.toml.** La "ficha" del proyecto: nombre, versión, dependencias y ajustes de herramientas (pytest, mypy). Ábrelo; está comentado línea por línea.

**poetry.lock.** El resultado de resolver todas las dependencias, incluidas las indirectas (pandas necesita numpy, que necesita...), con versiones exactas. Lo genera Poetry; no se edita a mano. Analogía: `pyproject.toml` es la lista del súper, `poetry.lock` el ticket.

**Grupos de dependencias.** `[tool.poetry.dependencies]` son las que necesita el programa para correr. `[tool.poetry.group.dev.dependencies]` solo para desarrollar (pytest, mypy). Las de desarrollo no van a la Lambda.

## Instalar Poetry

```bash
pipx install poetry==1.8.4
poetry config virtualenvs.in-project true   # el venv se crea en ./.venv
```

## Pasos

```bash
cd churn-monitor            # la raíz del proyecto
pyenv local 3.10.12
poetry install              # lee poetry.lock y crea .venv con todo
poetry run python --version # "poetry run" ejecuta dentro del .venv
poetry show --top-level     # lo que pediste
poetry show --tree          # lo que pediste y lo que eso arrastra
```

## Comandos que vas a usar

| Comando | Qué hace | ¿Cambia el lock? |
| --- | --- | --- |
| `poetry install` | Instala exactamente lo del lock | No |
| `poetry add requests` | Agrega una dependencia nueva | Sí |
| `poetry add --group dev black` | Agrega una dependencia solo de desarrollo | Sí |
| `poetry update pyyaml` | Sube UNA dependencia dentro de su rango | Sí |
| `poetry update` (sin nombre) | Sube TODAS. Evítalo | Sí |
| `poetry check --lock` | Verifica que lock y pyproject coincidan | No |
| `poetry version patch` | Sube la versión del proyecto (0.1.0 → 0.1.1) | No |

## Ejercicios

1. Borra `.venv` y corre `poetry install`. Todo vuelve idéntico: esa es la promesa del lock.
2. Cambia `pandas = "2.2.2"` por `pandas = "2.2.3"` **sin** tocar el lock y corre `poetry check --lock`. Lee el error. Deshaz el cambio.
3. `poetry add --group dev rich`, mira el diff de ambos archivos con `git diff`, y luego `poetry remove --group dev rich`.
4. Lee los comentarios de `pyproject.toml` sobre por qué las versiones de la Lambda están fijas.

## En pipeline-model-monitor

El mismo esquema. La regla del equipo, nacida de dos despliegues rotos: el lock manda. No se corre `poetry update` en el CI; si quieres actualizar algo, `poetry update <paquete>`, pruebas y commiteas el lock.

## Terminaste cuando

- Puedes explicar la diferencia entre `pyproject.toml` y `poetry.lock`.
- Sabes qué comando usar para instalar, agregar y actualizar.
