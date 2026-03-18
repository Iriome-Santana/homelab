# AWS — Fase 03 Lambda completo

## Fecha: Marzo 2026

---

## Qué es Lambda y qué problema resuelve

Con EC2 pagas por hora aunque la instancia no haga nada.
Para tareas que ocurren raramente eso es un desperdicio enorme.

```
EC2 t3.micro procesando 10 fotos al día:
  Coste: ~$8/mes
  Tiempo real de trabajo: 20 segundos al día
  Pagas 24 horas para trabajar 20 segundos

Lambda procesando esas mismas 10 fotos:
  Coste: $0 (dentro del free tier de 1M invocaciones/mes)
  Solo se ejecuta cuando hay una foto que procesar
  Si no hay fotos, no hay nada corriendo, no pagas nada
```

Lambda es serverless: no gestionas ningún servidor.
Escribes solo el código de la función. AWS gestiona todo lo demás.

```
Tú escribes:    def handler(event, context):
                    # tu código aquí
                    return resultado

AWS gestiona:   el servidor donde corre
                el SO y sus parches
                la memoria y la CPU
                el escalado si hay 1 o 10.000 peticiones simultáneas
                la disponibilidad
```

---

## Cuándo EC2 y cuándo Lambda

```
EC2:
  Procesos que corren continuamente (servidor web, API con tráfico constante)
  Necesitas control total del SO
  Procesos que tardan más de 15 minutos (límite máximo de Lambda)
  Estado en memoria entre peticiones

Lambda:
  Reaccionar a eventos (archivo subido, item insertado, petición HTTP)
  Tareas cortas y puntuales
  Carga impredecible o muy variable
  No quieres gestionar servidores
  Cron jobs simples
```

---

## Modelo de precio

```
1 millón de invocaciones gratis al mes (siempre, no solo Free Tier)
Después: $0.20 por cada millón adicional
+ $0.0000166667 por GB-segundo de ejecución
```

Para la mayoría de casos de aprendizaje Lambda es completamente gratis.

---

## boto3 — cómo funciona realmente

boto3 es la librería de Python para hablar con AWS.
Traduce tus llamadas Python a peticiones HTTP que AWS entiende.

```python
# Resource: interfaz de alto nivel, más pythonica
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
tabla = dynamodb.Table('gastos-tracker')
tabla.put_item(Item={"user_id": "001", "cantidad": "10.00"})

# Client: interfaz de bajo nivel, más control
s3 = boto3.client('s3', region_name='eu-west-1')
s3.put_object(Bucket='mi-bucket', Key='archivo.txt', Body=b'contenido')
```

### Cómo boto3 encuentra las credenciales

```
1. Variables de entorno        AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
2. ~/.aws/credentials          las que configuraste con aws configure
3. IAM Role de EC2 o Lambda    si estás dentro de una instancia o función
```

Dentro de Lambda boto3 detecta automáticamente el Execution Role.
Por eso nunca hardcodeas credenciales. boto3 las obtiene solo.

---

## La estructura de una función Lambda

Toda función Lambda tiene exactamente esta firma:

```python
def handler(event, context):
    # tu código aquí
    return algo
```

**`event`**: contiene toda la información del evento que disparó Lambda.
Su contenido depende de quién la disparó:

```python
# Si la disparó S3 (archivo subido):
event = {
    "Records": [{
        "s3": {
            "bucket": {"name": "mi-bucket"},
            "object": {"key": "foto.jpg", "size": 1024}
        }
    }]
}

# Si la disparó DynamoDB Streams:
event = {
    "Records": [{
        "eventName": "INSERT",
        "dynamodb": {"NewImage": {...}}
    }]
}

# Si la disparó API Gateway (petición HTTP GET):
event = {
    "httpMethod": "GET",
    "path": "/gastos",
    "queryStringParameters": {"user_id": "001"},
    "body": None
}

# Si la disparó API Gateway (petición HTTP POST):
event = {
    "httpMethod": "POST",
    "path": "/gastos",
    "queryStringParameters": None,
    "body": "{\"descripcion\": \"Café\", \"cantidad\": \"2.50\"}"
}

# Si la disparó EventBridge (cron job):
event = {
    "source": "aws.events",
    "detail-type": "Scheduled Event"
}
```

**`context`**: información sobre la invocación. Cuánto tiempo queda,
el request ID, el nombre de la función. En el día a día apenas se usa.

---

## El ciclo de vida completo

```
1. Ocurre un evento (S3 upload, petición HTTP, cron job...)

2. AWS busca qué Lambda tiene ese trigger configurado

3. Si Lambda está fría (no se ha ejecutado recientemente):
   → AWS crea un entorno de ejecución nuevo
   → Descarga tu ZIP y lo descomprime
   → Inicializa el runtime de Python
   → Ejecuta el código fuera del handler() (imports, conexiones)
   → COLD START: todo esto tarda entre 100ms y varios segundos

4. AWS llama a tu handler(event, context) con los datos del evento

5. Tu código se ejecuta

6. Lambda devuelve el resultado

7. El entorno se queda caliente durante un tiempo
   Si llega otro evento pronto → WARM START, va directo al paso 4
   Si no llega ningún evento → AWS destruye el entorno
```

---

## Por qué el código fuera del handler importa

```python
import boto3

# Fuera del handler → se ejecuta UNA vez en el cold start
# Se reutiliza en todos los warm starts
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
tabla = dynamodb.Table('gastos-tracker')
conn = None   # conexión a base de datos

def handler(event, context):
    # Dentro del handler → se ejecuta en CADA invocación
    tabla.put_item(Item={"user_id": "001"})
```

Si pusieras `boto3.resource()` dentro del handler, crearía una nueva
conexión en cada invocación. Fuera del handler se crea una vez y se reutiliza.
En producción siempre se inicializan las conexiones fuera del handler.

---

## Cold Start vs Warm Start

```
Cold start:   primera invocación o después de inactividad
              AWS inicializa el entorno desde cero
              Python: ~100-500ms extra
              Java:   ~1-3 segundos extra (JVM lenta de arrancar)

Warm start:   Lambda ya estaba caliente de una invocación reciente
              ejecuta directamente tu código sin inicialización
              latencia mínima
```

Comparativa real de los labs:
```
Lab 1 Lambda sin VPC (S3 → DynamoDB):  Init Duration: 465ms  cold start
                                        Duration: 284ms        tu código
                                        warm start:            37ms total

Lab 3 Lambda sin VPC (EventBridge):    Init Duration: 549ms  cold start
                                        Duration: 780ms        tu código

Lab 4 Lambda CON VPC (RDS):            Init Duration: 168ms  cold start
                                        conexión a RDS:        692ms
                                        warm start:            28ms total
```

El warm start de Lambda con VPC es 30 veces más rápido que el cold start
porque la ENI y la conexión a RDS ya existen y se reutilizan.

---

## Triggers — cómo se despierta Lambda

Lambda no se ejecuta sola. Siempre hay algo que la dispara:

```
S3:               alguien sube un archivo       → Lambda procesa el archivo
API Gateway:      petición HTTP llega            → Lambda responde como servidor web
DynamoDB Streams: item cambia en tabla           → Lambda reacciona al cambio
SQS:              mensaje en cola                → Lambda procesa el mensaje
EventBridge:      cron job o evento de servicio  → Lambda se ejecuta
```

---

## Execution Role — sin credenciales en el código

Lambda usa un IAM Role para tener permisos. boto3 lo detecta automáticamente.

```python
# MAL — nunca hagas esto, las credenciales quedan expuestas
s3 = boto3.client('s3',
    aws_access_key_id='AKIA...',
    aws_secret_access_key='...'
)

# BIEN — boto3 detecta el Role automáticamente
s3 = boto3.client('s3', region_name='eu-west-1')
```

En producción las credenciales de bases de datos van en Secrets Manager,
nunca hardcodeadas en el código aunque sea en variables:

```python
# MAL para producción — hardcodeado aunque sea en variable
DB_PASS = "DevOps2026!"

# BIEN para producción — leer de Secrets Manager en runtime
secret = secretsmanager.get_secret_value(SecretId='rds/devops-postgres')
```

---

## Trust Policy vs Permission Policy

El IAM Role de Lambda tiene dos partes:

```
Trust Policy:       quién puede ASUMIR el Role
                    para Lambda: {"Service": "lambda.amazonaws.com"}
                    sin esto AWS no deja a Lambda usar el Role

Permission Policy:  qué puede HACER quien tenga el Role
                    AWSLambdaBasicExecutionRole    → escribir logs CloudWatch
                    AWSLambdaDynamoDBExecutionRole → leer DynamoDB Streams
                    AmazonS3ReadOnlyAccess          → leer de S3
                    AmazonDynamoDBFullAccess        → escribir en DynamoDB
                    AmazonEC2FullAccess             → gestionar instancias EC2
                    AWSLambdaVPCAccessExecutionRole → crear ENIs en VPC
```

---

## Layers — dependencias compartidas

Sin Layers cada función lleva todas sus dependencias en el ZIP:
```
función-1.zip  → tu código (2KB) + pandas + numpy (50MB)
función-2.zip  → tu código (2KB) + pandas + numpy (50MB)  ← duplicado
función-3.zip  → tu código (2KB) + pandas + numpy (50MB)  ← duplicado
```

Con Layers:
```
pandas-numpy-layer.zip  → dependencias (50MB) — subido UNA vez
función-1.zip  → solo tu código (2KB) + referencia al Layer
función-2.zip  → solo tu código (2KB) + referencia al Layer
función-3.zip  → solo tu código (2KB) + referencia al Layer
```

Si sale una versión nueva actualizas el Layer una vez y todas las funciones
lo heredan. Cada función puede tener hasta 5 Layers.

---

## Lambda en VPC

Por defecto Lambda corre fuera de tu VPC.
No puede acceder a recursos privados como RDS o ElastiCache.

```
Lambda sin VPC:   corre en infraestructura AWS fuera de tu VPC
                  puede acceder a S3, DynamoDB, internet
                  NO puede acceder a RDS en subnet privada

Lambda con VPC:   vive dentro de tu VPC como una EC2
                  puede acceder a RDS, ElastiCache, EC2 privadas
                  NO puede acceder a internet sin NAT Gateway
```

Cuando metes Lambda en VPC le asignas subnet y Security Group.
Usa la misma cadena de Security Groups que ya conoces:

```
Lambda (sg-app) → sg-database acepta 5432 desde sg-app → RDS PostgreSQL
```

### AWSLambdaVPCAccessExecutionRole — por qué es necesaria

Cuando Lambda está en VPC AWS crea interfaces de red (ENIs) en tus subnets
para comunicarse con los recursos privados.
Sin esta política Lambda no puede crear las ENIs y falla al arrancar.

### Cuándo meter Lambda en VPC y cuándo no

```
Meter en VPC:
  Lambda necesita acceder a RDS          → obligatorio
  Lambda necesita acceder a ElastiCache  → obligatorio

No meter en VPC:
  Lambda solo accede a S3, DynamoDB, SQS → no necesita VPC
  Lambda llama a APIs externas           → necesita internet, sin NAT no puede
```

Solo en VPC si es estrictamente necesario.

---

## API Gateway — qué es y cómo encaja con Lambda

Lambda no puede recibir peticiones HTTP directamente.
Solo sabe recibir un event y devolver un resultado.
API Gateway es el traductor entre HTTP y Lambda.

```
Sin API Gateway:
  Internet → ??? → Lambda
  Lambda no escucha puertos, no puede recibir HTTP directamente

Con API Gateway:
  Internet → API Gateway → Lambda
  API Gateway escucha HTTPS permanentemente
  Cuando llega una petición la convierte en event y llama a Lambda
```

### Cómo API Gateway traduce una petición HTTP

```
Petición HTTP que llega:
  GET /gastos?user_id=001

API Gateway la convierte en event para Lambda:
  {
    "httpMethod": "GET",
    "path": "/gastos",
    "queryStringParameters": {"user_id": "001"}
  }

Lambda devuelve:
  {"statusCode": 200, "headers": {...}, "body": "[{gastos...}]"}

API Gateway lo convierte en respuesta HTTP real:
  HTTP 200 OK
  Content-Type: application/json
  [{gastos...}]
```

### La estructura de respuesta que API Gateway necesita

Lambda SIEMPRE debe devolver este formato cuando está detrás de API Gateway:

```python
return {
    "statusCode": 200,          # código HTTP
    "headers": {                # cabeceras HTTP
        "Content-Type": "application/json"
    },
    "body": json.dumps({...})   # contenido SIEMPRE en string
}
```

Si no devuelves exactamente esta estructura API Gateway no sabe qué responder.

### Cómo manejar distintos métodos HTTP en Lambda

```python
def handler(event, context):
    metodo = event.get('httpMethod')
    params = event.get('queryStringParameters') or {}
    body   = json.loads(event.get('body') or '{}')

    if metodo == 'GET':
        # datos vienen en params (queryStringParameters)
        user_id = params['user_id']

    elif metodo == 'POST':
        # datos vienen en body
        descripcion = body['descripcion']
        tabla.put_item(Item=body)
        return {"statusCode": 201, "body": json.dumps({"mensaje": "Creado"})}

    elif metodo == 'DELETE':
        # datos vienen en params
        tabla.delete_item(Key={"user_id": params['user_id']})
        return {"statusCode": 200, "body": json.dumps({"mensaje": "Borrado"})}
```

```
GET y DELETE:  datos en la URL    → event['queryStringParameters']
POST y PUT:    datos en el body   → event['body'] (string JSON, hay que parsear)
```

---

## EventBridge — cron jobs y eventos de infraestructura

EventBridge es el bus de eventos central de AWS.
Tiene dos usos principales:

**Uso 1 — Cron jobs programados**
```
rate(2 minutes)           → cada 2 minutos (para labs)
rate(1 hour)              → cada hora
cron(0 20 ? * MON-FRI *)  → lunes a viernes a las 20:00 UTC
cron(0 8 ? * MON-FRI *)   → lunes a viernes a las 08:00 UTC
```

**Uso 2 — Reaccionar a eventos de servicios AWS**
```
EC2 cambia de estado     → EventBridge detecta → Lambda notifica al equipo
Usuario falla login 3x   → EventBridge detecta → Lambda bloquea el usuario
RDS hace backup          → EventBridge detecta → Lambda actualiza dashboard
```

### Diferencia entre EventBridge y DynamoDB Streams

```
DynamoDB Streams:   eventos de cambios en DATOS
                    item insertado, modificado o borrado

EventBridge:        eventos de cambios en INFRAESTRUCTURA y cron jobs
                    cambios de estado de servicios, tareas programadas
```

---

## Cómo leer los logs de CloudWatch

```
INIT_START:      Lambda inicializando (cold start)
START:           comienza tu función handler()
...prints...     todo lo que hiciste print()
END:             termina tu función
REPORT:
  Duration:        cuánto tardó tu código exactamente
  Billed Duration: cuánto te cobra AWS (redondean al alza a 1ms)
  Memory Size:     RAM configurada
  Max Memory Used: RAM que realmente usó tu función
  Init Duration:   cuánto tardó el cold start (solo aparece en cold starts)
```

Si no aparece `INIT_START` ni `Init Duration` → warm start.

---

## Comandos útiles Lambda

```bash
# Crear función
aws lambda create-function \
  --function-name NOMBRE \
  --runtime python3.12 \
  --handler archivo.funcion \
  --zip-file fileb://codigo.zip \
  --role ARN-DEL-ROLE \
  --timeout 30 \
  --memory-size 128

# Crear función con VPC
aws lambda create-function \
  --function-name NOMBRE \
  --runtime python3.12 \
  --handler archivo.funcion \
  --zip-file fileb://codigo.zip \
  --role ARN-DEL-ROLE \
  --timeout 60 \
  --memory-size 128 \
  --vpc-config "SubnetIds=subnet-xxx,SecurityGroupIds=sg-xxx" \
  --environment "Variables={CLAVE=valor}"

# Ver estado de la función
aws lambda get-function \
  --function-name NOMBRE \
  --query "Configuration.State" \
  --output text

# Invocar manualmente (resultado se guarda en archivo)
aws lambda invoke \
  --function-name NOMBRE \
  --payload '{"clave": "valor"}' \
  --cli-binary-format raw-in-base64-out \
  response.json

cat response.json

# Dar permiso a S3 para invocar Lambda
aws lambda add-permission \
  --function-name NOMBRE \
  --statement-id s3-permission \
  --action lambda:InvokeFunction \
  --principal s3.amazonaws.com \
  --source-arn arn:aws:s3:::BUCKET

# Dar permiso a API Gateway para invocar Lambda
aws lambda add-permission \
  --function-name NOMBRE \
  --statement-id apigateway-permission \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:eu-west-1:ID-CUENTA:API-ID/*/GET/ruta"

# Dar permiso a EventBridge para invocar Lambda
aws lambda add-permission \
  --function-name NOMBRE \
  --statement-id eventbridge-permission \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn ARN-DE-LA-REGLA

# Ver logs en tiempo real
aws logs tail /aws/lambda/NOMBRE --follow

# Eliminar función
aws lambda delete-function --function-name NOMBRE
```

## Comandos útiles API Gateway

```bash
# Crear API
aws apigateway create-rest-api --name "nombre-api"

# Ver APIs existentes
aws apigateway get-rest-apis \
  --query "items[*].{ID:id,Nombre:name}" \
  --output table

# Obtener recurso raíz
aws apigateway get-resources \
  --rest-api-id API-ID \
  --query "items[0].id" \
  --output text

# Crear recurso (endpoint)
aws apigateway create-resource \
  --rest-api-id API-ID \
  --parent-id ROOT-ID \
  --path-part "nombre-endpoint"

# Crear método GET
aws apigateway put-method \
  --rest-api-id API-ID \
  --resource-id RESOURCE-ID \
  --http-method GET \
  --authorization-type NONE

# Conectar método con Lambda
aws apigateway put-integration \
  --rest-api-id API-ID \
  --resource-id RESOURCE-ID \
  --http-method GET \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:eu-west-1:lambda:path/2015-03-31/functions/LAMBDA-ARN/invocations"

# Desplegar API
aws apigateway create-deployment \
  --rest-api-id API-ID \
  --stage-name prod

# Eliminar API
aws apigateway delete-rest-api --rest-api-id API-ID
```

## Comandos útiles EventBridge

```bash
# Crear regla con schedule
aws events put-rule \
  --name "nombre-regla" \
  --schedule-expression "rate(2 minutes)" \
  --state ENABLED

# Conectar regla con Lambda
aws events put-targets \
  --rule "nombre-regla" \
  --targets "Id=lambda-target,Arn=LAMBDA-ARN"

# Desactivar regla
aws events disable-rule --name "nombre-regla"

# Eliminar targets y regla
aws events remove-targets --rule "nombre-regla" --ids lambda-target
aws events delete-rule --name "nombre-regla"
```

---

## Labs realizados

### Lab 1 — Lambda disparada por S3 upload → escribe metadata en DynamoDB

**Flujo:**
```
Subir archivo a S3
    │ S3 genera evento automáticamente
    ▼
Lambda recibe event con nombre, tamaño y bucket
    │ extrae la metadata
    ▼
DynamoDB guarda registro de cada archivo subido
```

**Caso de uso real:** sistema de auditoría que registra automáticamente
cada archivo que llega a un bucket sin intervención humana.

**Infraestructura:**
```
Bucket:    lambda-s3-lab-iriome-2026
Tabla:     s3-metadata (filename HASH + timestamp RANGE)
Role:      lambda-s3-dynamodb-role
           AWSLambdaBasicExecutionRole + S3ReadOnly + DynamoDBFullAccess
Función:   s3-metadata-processor
Trigger:   S3 notification → s3:ObjectCreated:*
```

**Lo que demostró:**
- Primera subida: cold start 465ms + código 284ms
- Segunda subida: warm start 37ms (8x más rápido)
- S3 necesita permiso explícito (`add-permission`) para invocar Lambda

**Código clave:**
```python
def handler(event, context):
    for record in event['Records']:
        bucket   = record['s3']['bucket']['name']
        filename = record['s3']['object']['key']
        size     = record['s3']['object']['size']
        tabla.put_item(Item={
            "filename": filename, "bucket": bucket, "size": size
        })
```

---

### Lab 2 — Lambda + API Gateway: API REST serverless

**Flujo:**
```
curl https://URL/gastos?user_id=001
    │ petición HTTP real por internet
    ▼
API Gateway convierte petición en event
    ▼
Lambda consulta DynamoDB
    │ devuelve JSON
    ▼
API Gateway responde HTTP 200
```

**Caso de uso real:** API del Expense Tracker serverless.
Sin EC2 corriendo 24/7, sin servidor que gestionar.

**URL generada:**
```
https://API-ID.execute-api.eu-west-1.amazonaws.com/prod/gastos
```

**Infraestructura:**
```
Función:     gastos-api
API:         gastos-api (API Gateway REST)
Endpoint:    GET /gastos?user_id=XXX
Stage:       prod
```

**Respuestas verificadas:**
```
GET /gastos?user_id=usuario-001  → 200 con 4 gastos en JSON
GET /gastos                      → 400 con mensaje de error
```

**Lo que aprendí sobre POST vs GET:**
```
GET y DELETE:  datos en queryStringParameters (URL)
POST y PUT:    datos en body (JSON string, hay que parsear con json.loads)
```

---

### Lab 3 — Lambda + EventBridge: cron job serverless

**Flujo:**
```
EventBridge dispara Lambda cada 2 minutos
    ▼
Lambda busca EC2 con tag Environment=dev en estado running
    ▼
Lambda para las instancias encontradas
    ▼
CloudWatch guarda el log
```

**Caso de uso real:** parar EC2 de desarrollo fuera del horario laboral.
En producción: `cron(0 20 ? * MON-FRI *)` → ahorra 14 horas de coste diario.

**Infraestructura:**
```
Función:  ec2-dev-scheduler
Role:     lambda-ec2-scheduler-role + AmazonEC2FullAccess
Regla:    parar-ec2-dev, rate(2 minutes)
Tag EC2:  Environment=dev
```

**Resultado verificado:**
```
13:24:58  EventBridge disparó Lambda automáticamente
13:24:59  Instancias dev encontradas: ['i-0b6d6e6e6aa0ac3dd']
13:24:59  Paradas correctamente en menos de 1 segundo
```

---

### Lab 4 — Lambda en VPC conectada a RDS PostgreSQL

**Flujo:**
```
aws lambda invoke
    ▼
Lambda (subnet privada, sg-app)
    │ psycopg2 puerto 5432
    ▼
RDS PostgreSQL (subnet privada, sg-database)
    │ acepta 5432 desde sg-app
    ▼
Lambda devuelve gastos en JSON
```

**Caso de uso real:** microservicio que consulta datos relacionales
sin exponer RDS al exterior.

**Infraestructura:**
```
Función:  lambda-rds-query
Role:     lambda-rds-role
          AWSLambdaBasicExecutionRole + AWSLambdaVPCAccessExecutionRole
VPC:      devops-vpc, private-subnet-1a, sg-app
Env var:  DB_HOST → endpoint de RDS
```

**Comparativa cold start vs warm start:**
```
Cold start:   Init 168ms + conexión RDS 692ms = ~860ms total
Warm start:   28ms total (30x más rápido)
              sin INIT_START, sin "Creando nueva conexión"
```

**Por qué la conexión se reutiliza:**
```python
conn = None   # fuera del handler → persiste entre invocaciones

def get_connection():
    global conn
    if conn is None or conn.closed:
        conn = psycopg2.connect(...)   # solo en cold start
    return conn                         # warm start → devuelve la existente
```

**Problema de seguridad identificado:**
`DB_PASS = "DevOps2026!"` hardcodeado en el código → MAL.
En producción las credenciales van en Secrets Manager.

---

## Lo que aprendí rompiendo cosas

**`$API_ID` se pierde al cerrar la terminal**
Las variables de entorno no persisten entre sesiones.
Si necesitas el ID de una API más tarde, obtenerlo con:
```bash
aws apigateway get-rest-apis --query "items[*].{ID:id,Nombre:name}" --output table
```

**Lambda en estado `Pending` al invocarla**
Cuando Lambda está en VPC necesita unos minutos para crear las ENIs.
Aunque el comando de creación devuelva éxito, la función no está lista aún.
Esperar hasta que `aws lambda get-function --query "Configuration.State"` devuelva `Active`.

**EventBridge tardó en propagarse**
Igual que con DynamoDB Streams, los triggers de EventBridge tienen
propagación eventual. Si no funciona inmediatamente, esperar 1-2 minutos.

---

## Cuándo usaría esto en trabajo real

```
Lambda + S3:
  Procesar imágenes al subirse (redimensionar, generar miniaturas)
  Validar CSVs al subirse (formato, datos obligatorios)
  Indexar documentos PDF en un motor de búsqueda

Lambda + API Gateway:
  APIs con tráfico muy variable (de 0 a miles de req/minuto)
  MVPs y prototipos donde no quieres gestionar servidores
  Microservicios pequeños con lógica simple

Lambda + EventBridge:
  Parar EC2 de dev fuera del horario laboral
  Generar reportes diarios y enviarlos por email
  Limpiar objetos expirados de S3 periódicamente
  Monitorizar cambios de configuración en la infraestructura

Lambda + DynamoDB Streams:
  Notificaciones en tiempo real cuando cambian datos
  Sincronización entre servicios desacoplados
  Auditoría automática de cambios

Lambda en VPC + RDS:
  Microservicio que consulta datos relacionales
  Funciones que necesitan acceso a bases de datos privadas
  Lógica de negocio que no justifica una EC2 encendida 24/7
```
