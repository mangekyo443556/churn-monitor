# Nivel 6 · Tu propia cuenta de AWS

**Objetivo:** desplegar el monitor en AWS y verlo correr solo, de punta a punta, con alertas en un Slack tuyo.

Usa una cuenta de AWS **personal**, nunca una de Vana.

## 0. Antes de crear nada: protege tu bolsillo

1. Crea la cuenta en [aws.amazon.com](https://aws.amazon.com). Las condiciones del nivel gratuito cambian con el tiempo: revísalas al registrarte.
2. Activa MFA (doble factor) en el usuario raíz y no lo uses para el día a día.
3. **Crea una alerta de presupuesto:** Billing → Budgets → Create budget → "Zero spend" o "Monthly cost" de 5 USD, con aviso a tu correo.
4. Crea un usuario para ti en IAM Identity Center (o un usuario IAM con permisos de administrador, solo en esta cuenta de práctica) y configura la CLI:

```bash
aws configure sso        # o: aws configure, si usas claves
aws sts get-caller-identity
```

Este proyecto usa muy poco: unas pocas ejecuciones de Lambda al día, unos MB en S3 y una imagen en ECR (el registro de imágenes; es lo que más espacio ocupa). Si lo dejas corriendo meses, revisa el costo de ECR. Al terminar, `make destroy` lo borra todo.

## 1. Slack (opcional, pero vale la pena)

1. Crea un workspace gratuito de Slack para practicar y un canal `#alertas-drift`.
2. En [api.slack.com/apps](https://api.slack.com/apps): Create New App → From scratch → Incoming Webhooks → activar → "Add New Webhook to Workspace" → elige el canal.
3. Copia la URL (`https://hooks.slack.com/services/...`). **Es un secreto:** quien la tenga puede publicar en tu canal. Nunca la escribas en el código ni la subas a Git.

Prueba local: `SLACK_WEBHOOK_URL="https://hooks..." make monitor`.

## 2. Primer despliegue (desde tu máquina)

```bash
make build
sam deploy --guided
```

`--guided` te hace preguntas y guarda las respuestas en `samconfig.toml`. Respuestas sugeridas: stack `churn-monitor-dev`, región `us-east-1`, `SlackWebhookUrl` = tu URL (o vacío), `ScheduleState` = `DISABLED`, confirmar cambios = `y`, guardar configuración = `y`.

Antes de aplicar, SAM muestra el **changeset**: la lista de recursos que va a crear. Léela.

Los siguientes despliegues son solo `make deploy`.

## 3. Hacerlo funcionar

```bash
make data              # si no lo tienes local
make upload-data       # sube el CSV al bucket del stack
make invoke-train      # entrena en la Lambda de AWS
make start-execution SCENARIO=new_customers
```

Míralo correr en la consola: Step Functions → `churn-monitor-dev` → la ejecución. Cada paso se pone verde y puedes ver su entrada y salida. Los logs de cada Lambda están en CloudWatch → Log groups. Los archivos, en S3, con la misma estructura que tenías en `.local_bucket/`.

## 4. Encender el horario

```bash
sam deploy --parameter-overrides Environment=dev ScheduleState=ENABLED
```

Mañana a las 13:00 UTC (9:00 en Bolivia) corre sola. Apágalo igual, con `DISABLED`.

## 5. Desplegar desde GitHub Actions (CI/CD)

El workflow `deploy.yml` usa **OIDC**: GitHub le pide a AWS credenciales temporales para cada ejecución, sin guardar claves.

1. IAM → Identity providers → Add provider → OpenID Connect. URL: `https://token.actions.githubusercontent.com`. Audience: `sts.amazonaws.com`.
2. IAM → Roles → Create role → Web identity → ese proveedor. En la condición, limita el acceso a tu repo: `repo:TU_USUARIO/churn-monitor:*`.
3. Permisos del rol: para una cuenta de práctica, `AdministratorAccess` es lo más simple (SAM necesita crear roles, buckets, Lambdas...). En un entorno real se darían permisos mínimos.
4. En GitHub: Settings → Secrets and variables → Actions → crea `AWS_DEPLOY_ROLE_ARN` (el ARN del rol) y `SLACK_WEBHOOK_URL`.
5. Actions → deploy → Run workflow.

Vana usa claves de acceso guardadas como secrets en GitHub, que es el método anterior a OIDC. Funciona igual desde el punto de vista del workflow; la diferencia es que OIDC no deja claves permanentes que se puedan filtrar.

## 6. Limpiar

```bash
make destroy           # vacía el bucket y borra el stack
```

Revisa en ECR que no queden repositorios de imágenes, y en CloudWatch los log groups.

## Ejercicios

1. Cambia `DriftScenario` a `contract_shift`, redespliega y lanza una ejecución. Llega una alerta a Slack.
2. Rompe `process_drift` a propósito (`raise ValueError("prueba")`), despliega y lanza. Mira dónde ves el error en Step Functions y en CloudWatch. Repáralo.
3. Agrega `NOTIFY_ONLY_ON_ALERT: "true"` y comprueba que el escenario `none` ya no avisa.
4. Agrega al template una alarma de CloudWatch que avise si la Step Function falla, como las que tiene `pipeline-model-monitor`.

## Terminaste cuando

- Una ejecución de la Step Function termina en verde y llega el mensaje a Slack.
- Desplegaste una vez desde GitHub Actions.
- Ejecutaste `make destroy`.
