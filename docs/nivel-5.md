# Nivel 5 · SAM en local

**Objetivo:** describir toda la infraestructura de AWS en un archivo de texto, validarlo y probar las Lambdas con SAM, todavía sin cuenta de AWS.

## Lo que tienes que entender

**Infraestructura como código.** En vez de crear recursos con clics en la consola de AWS, los describes en un archivo versionado en Git. Una herramienta compara lo que pides con lo que existe y aplica las diferencias.

**CloudFormation** es esa herramienta en AWS. Todo lo que crea un template se agrupa en un **stack**, que se actualiza o borra como unidad.

**SAM** es una capa sobre CloudFormation, especializada en Lambdas. `template.yaml` usa sus atajos (`AWS::Serverless::Function`, `S3CrudPolicy`...). Ábrelo: está comentado.

Lo que describe, en orden:

| Recurso | Tipo | Para qué |
| --- | --- | --- |
| `DataBucket` | S3 | Reemplaza a `.local_bucket/`. Borra batches y reportes de más de 30 días |
| 4 funciones | Lambda (imagen) | Las mismas 4 carpetas; misma imagen, distinto `Command` |
| `MonitorStateMachine` | Step Function | Llama a simular → drift → notificar, en orden |
| `DailySchedule` | EventBridge | Arranca la Step Function todos los días a las 13:00 UTC (apagado al inicio) |

Conceptos que vas a ver en el template:

- **Parameters:** valores que eliges al desplegar (entorno, webhook de Slack, escenario).
- **`!Ref`, `!GetAtt`, `!Sub`:** funciones para referirse a otros recursos. `!Ref DataBucket` es "el nombre del bucket que se cree".
- **Policies:** permisos. Cada Lambda solo puede tocar su bucket; la Step Function solo puede invocar sus 3 Lambdas.
- **Metadata:** le dice a `sam build` qué Dockerfile usar.

**samconfig.toml** guarda las opciones de `sam deploy` para no escribirlas cada vez. Es otro TOML, pero lo lee SAM, no Poetry.

## Pasos

Instala la [SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html). Necesita Docker.

```bash
make validate          # sam validate --lint: revisa el template
make build             # export + sam build: construye la imagen de las 4 Lambdas
ls .aws-sam/           # lo que dejó sam build
make local-notify      # sam local invoke NotifyFunction con un reporte de ejemplo
```

`local-notify` usa `events/notify_inline.json`, que trae el reporte completo dentro del evento. Por eso funciona sin S3.

## Ejercicios

1. Rompe el template a propósito: pon `MemorySize: mucho` y corre `make validate`. Lee el error.
2. Cambia el horario a las 8:00 de Bolivia (UTC-4). Pista: `cron(minuto hora día mes día-semana año)`.
3. Agrega una variable de entorno `LOG_LEVEL` solo a `ProcessDriftFunction`.
4. Busca en el template de `pipeline-model-monitor` los mismos tipos: `AWS::Serverless::Function`, `AWS::StepFunctions::StateMachine`, `AWS::Events::Rule`. Allá la Step Function usa un estado `Map` para procesar varios modelos en paralelo. ¿Cómo lo agregarías aquí si tuvieras dos modelos?

## Terminaste cuando

- `make validate` y `make build` pasan.
- Puedes señalar en `template.yaml` dónde se define cada pieza del diagrama.
