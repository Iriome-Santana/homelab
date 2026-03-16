# AWS — Fase 03 RDS, DynamoDB y Lambda

## Fecha: Marzo 2026

---

## El problema que resuelven las bases de datos gestionadas

Sin servicios gestionados, tener una base de datos en producción significa
ser tú el DBA (Database Administrator). Eres responsable de todo:

```
Instalar y configurar el motor
Aplicar parches de seguridad cuando salen
Hacer backups diarios y verificar que funcionan
Monitorizar que el disco no se llena
Configurar alta disponibilidad si la necesitas
Gestionar el failover si la instancia falla
Actualizar la versión del motor
Configurar el cifrado
```

En una startup sin equipo de operaciones dedicado, eso es inasumible.
Los servicios gestionados de AWS resuelven exactamente eso.

---

## La jerarquía correcta — cómo encaja todo

```
Bases de datos relacionales (SQL):
├── PostgreSQL
├── MySQL
├── MariaDB
├── Oracle
└── SQL Server

Bases de datos no relacionales (NoSQL):
├── DynamoDB   (clave-valor y documentos, creada por AWS)
├── MongoDB    (documentos)
├── Redis      (clave-valor en memoria)
└── Cassandra  (columnas distribuidas)

Servicios gestionados de AWS:
├── RDS        → gestiona las relacionales (PostgreSQL, MySQL, MariaDB, Oracle, SQL Server)
├── DynamoDB   → NoSQL propio de AWS, no gestiona otro motor, ES el motor
├── DocumentDB → compatible con MongoDB, gestionado por AWS
└── ElastiCache → Redis y Memcached gestionados
```

RDS no es una base de datos en sí misma. Es un servicio que envuelve
las bases de datos relacionales existentes y las hace gestionadas.
DynamoDB sí es una base de datos en sí misma, creada por AWS desde cero.

---

## RDS — Relational Database Service

### Qué es y qué resuelve

RDS es PostgreSQL (o MySQL, MariaDB, Oracle, SQL Server) gestionado por AWS.
Te conectas y usas la base de datos exactamente igual que si fuera PostgreSQL normal.
Por debajo AWS se encarga de todo lo operacional.

```
PostgreSQL en EC2:  tú gestionas todo
                    más barato si tienes equipo dedicado
                    control total sobre la configuración
                    si la EC2 falla, pierdes la BD hasta restaurarla manualmente

RDS PostgreSQL:     AWS gestiona todo lo operacional
                    backups automáticos con retención configurable
                    parches de seguridad automáticos
                    Multi-AZ para failover automático
                    más caro que EC2 solo, pero incluye todo el trabajo operacional
```

Analogía:
```
PostgreSQL en EC2:  comprarte un coche y ser tú el mecánico
RDS:                leasing con mantenimiento incluido
                    conduces el mismo coche pero el taller se encarga de todo
```

### Cuándo usar RDS vs EC2 con PostgreSQL

```
Aprendiendo o proyecto personal  → EC2 si quieres control total y ahorrar
Startup sin equipo de ops        → RDS, no puedes permitirte un DBA dedicado
Empresa grande con equipo DevOps → puede valer la pena EC2 a escala
```

En la mayoría de empresas medianas y startups en producción se usa RDS
porque el coste del tiempo humano supera el sobrecoste del servicio.

---

## Subnet Groups

### Qué es y por qué existe

Un Subnet Group es una lista de subnets que le das a RDS antes de crear
la instancia. Le estás diciendo a AWS en qué subnets tiene permiso
para colocar tu base de datos.

Sin Subnet Group no puedes crear una instancia RDS. Es un prerequisito obligatorio.

```
Subnet Group devops-db-subnet-group:
├── private-subnet-1a (eu-west-1a)
└── private-subnet-1b (eu-west-1b)
```

### Por qué siempre subnets privadas

La base de datos es el activo más valioso de cualquier aplicación.
En una subnet pública internet puede intentar conectarse al puerto 5432
y lanzar ataques de fuerza bruta o explotar vulnerabilidades del motor.
En una subnet privada ese vector de ataque no existe físicamente,
el tráfico nunca llega.

```
Subnet pública:   internet → puede intentar conectar al puerto 5432
Subnet privada:   internet → no hay ruta, el tráfico nunca llega
```

### Por qué necesita mínimo dos subnets en AZs distintas

AWS lo requiere aunque no uses Multi-AZ. Lo exige por diseño para que
puedas activar Multi-AZ en el futuro sin recrear la instancia desde cero.

---

## Multi-AZ

### Qué problema resuelve

Sin Multi-AZ si el datacenter donde está tu BD tiene un problema
(corte eléctrico, fallo de hardware), tu aplicación cae hasta que
AWS restaura la instancia manualmente. Puede tardar 10-30 minutos.

Con Multi-AZ activo:

```
AZ-a (eu-west-1a):  instancia PRINCIPAL
                    recibe todas las lecturas y escrituras
                         │
                         │ replicación SÍNCRONA
                         │ cada escritura se confirma en AMBAS AZs
                         │ antes de responder al cliente
                         ▼
AZ-b (eu-west-1b):  instancia STANDBY
                    réplica exacta en tiempo real
                    no recibe tráfico, solo existe como seguro
```

Si AZ-a falla:
```
1. AWS detecta el fallo (~1 minuto)
2. Promueve la instancia de AZ-b a principal
3. Actualiza el DNS del endpoint automáticamente
4. Tu aplicación reconecta al mismo endpoint, ahora apunta a AZ-b
5. Tiempo total de interrupción: 1-2 minutos
```

Tu aplicación siempre se conecta al mismo endpoint DNS.
Nunca sabe en qué AZ está la instancia activa en cada momento.

### Cuándo activarlo y cuándo no

```
Sin Multi-AZ:   1 instancia db.t3.micro → ~$15/mes
Con Multi-AZ:   2 instancias db.t3.micro → ~$30/mes
```

```
Producción con usuarios reales   → Multi-AZ siempre
Staging:                         → sin Multi-AZ (no es crítico)
Desarrollo y labs:               → sin Multi-AZ (ahorro)
```

---

## Read Replicas

### Qué problema resuelve

Multi-AZ resuelve alta disponibilidad. Read Replicas resuelven rendimiento.
Son conceptos completamente distintos.

La mayoría de aplicaciones web leen mucho más de lo que escriben:
```
Un usuario típico:
  Escrituras: sube 1 post, da 10 likes, escribe 5 comentarios
  Lecturas:   carga el feed 50 veces, ve 200 perfiles, navega 100 páginas
```

Con millones de usuarios una sola instancia se satura con tanto tráfico de lectura.

```
Instancia principal:
  recibe todas las ESCRITURAS
       │
       │ replicación ASÍNCRONA
       │ (puede ir ligeramente por detrás, milisegundos)
       ▼
Read Replica 1, 2, 3...:
  reciben solo LECTURAS
  tu aplicación distribuye las lecturas entre ellas
```

### Diferencia clave con Multi-AZ

```
Multi-AZ:        replicación SÍNCRONA
                 la standby NO recibe tráfico
                 objetivo: sobrevivir fallos (alta disponibilidad)

Read Replicas:   replicación ASÍNCRONA
                 las réplicas SÍ reciben tráfico de lectura
                 objetivo: escalar rendimiento
```

En producción real se usan los dos juntos:
```
Instancia principal Multi-AZ  →  alta disponibilidad
     +
Read Replicas                 →  rendimiento escalado
```

---

## Aurora

Motor de base de datos creado por AWS desde cero, compatible con MySQL y PostgreSQL.
Misma API que MySQL o PostgreSQL pero arquitectura completamente reescrita.

```
Hasta 5x más rápido que MySQL estándar
Hasta 3x más rápido que PostgreSQL estándar
Almacenamiento que crece automáticamente (hasta 128TB)
Hasta 15 Read Replicas (RDS normal soporta hasta 5)
Failover más rápido que RDS estándar
```

Para el examen: saber que existe, que es compatible con MySQL y PostgreSQL,
y que es más caro pero más potente que RDS estándar.
Para aprender: no se usa porque es más caro que RDS normal.

---

## Estrategia de coste para labs

```
DynamoDB:  siempre gratis hasta 25GB → úsalo sin preocuparte
RDS:       cobra por hora aunque esté parada
           crear → hacer el lab → eliminar inmediatamente
           no hacer stop, hacer delete/terminate
```

Esta es la diferencia importante con EC2:
en EC2 puedes hacer Stop y no cobras compute.
En RDS incluso parada cobra. Por eso se elimina al terminar.

---

## Lab 1 — RDS PostgreSQL en subnet privada

### Infraestructura construida

```
Tu máquina local
      │ SSH
      ▼
ec2-public-bastion (subnet pública, sg-public-web)
      │ psql puerto 5432
      ▼
RDS PostgreSQL devops-postgres (subnet privada, sg-database)
      endpoint: devops-postgres.c12yiesu025r.eu-west-1.rds.amazonaws.com
      motor: PostgreSQL 15.14
      clase: db.t3.micro
      almacenamiento: 20GB gp2
      Multi-AZ: desactivado (lab temporal)
      acceso público: desactivado
```

### Paso 1 — Crear el Subnet Group

```bash
aws rds create-db-subnet-group \
  --db-subnet-group-name devops-db-subnet-group \
  --db-subnet-group-description "Subnets privadas para RDS" \
  --subnet-ids \
    $(aws ec2 describe-subnets \
      --filters "Name=tag:Name,Values=private-subnet-1a" \
      --query "Subnets[0].SubnetId" --output text) \
    $(aws ec2 describe-subnets \
      --filters "Name=tag:Name,Values=private-subnet-1b" \
      --query "Subnets[0].SubnetId" --output text)
```

### Paso 2 — Verificar sg-database existente

```bash
aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=sg.database" \
  --query "SecurityGroups[0].{ID:GroupId,Nombre:GroupName,Reglas:IpPermissions}" \
  --output json
```

sg-database ya existía del lab de VPC: acepta puerto 5432 solo desde sg-app.

### Paso 3 — Crear la instancia RDS

```bash
SG_DB=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=sg.database" \
  --query "SecurityGroups[0].GroupId" --output text)

aws rds create-db-instance \
  --db-instance-identifier devops-postgres \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.14 \
  --master-username devopsadmin \
  --master-user-password DevOps2026! \
  --db-name devopsdb \
  --db-subnet-group-name devops-db-subnet-group \
  --vpc-security-group-ids $SG_DB \
  --no-multi-az \
  --allocated-storage 20 \
  --storage-type gp2 \
  --no-publicly-accessible \
  --backup-retention-period 0
```

Monitorizar hasta available (~5-10 minutos):
```bash
watch -n 30 "aws rds describe-db-instances \
  --db-instance-identifier devops-postgres \
  --query 'DBInstances[0].{Estado:DBInstanceStatus,Endpoint:Endpoint.Address}' \
  --output table"
```

### Paso 4 — Problema encontrado y solución

El Bastion tiene sg-public-web, no sg-app.
sg-database solo acepta desde sg-app → conexión bloqueada.

Solución para el lab: añadir regla temporal en sg-database
que permita 5432 desde sg-public-web:

```bash
SG_DB=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=sg.database" \
  --query "SecurityGroups[0].GroupId" --output text)

SG_PUBLIC=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=sg.public_web" \
  --query "SecurityGroups[0].GroupId" --output text)

aws ec2 authorize-security-group-ingress \
  --group-id $SG_DB \
  --protocol tcp \
  --port 5432 \
  --source-group $SG_PUBLIC
```

En producción real el Bastion nunca se conecta a RDS directamente.
Solo la capa de aplicación con sg-app habla con la base de datos.

### Paso 5 — Conectar desde el Bastion

```bash
# Instalar cliente psql en Amazon Linux 2023
sudo dnf install -y postgresql15

# Conectar a RDS
psql --host=ENDPOINT --port=5432 --username=devopsadmin --dbname=devopsdb
```

### Paso 6 — Queries ejecutadas

```sql
SELECT version();

CREATE TABLE gastos (
    id SERIAL PRIMARY KEY,
    descripcion VARCHAR(100),
    cantidad DECIMAL(10,2),
    categoria VARCHAR(50),
    fecha DATE DEFAULT CURRENT_DATE
);

INSERT INTO gastos (descripcion, cantidad, categoria) VALUES
    ('Supermercado', 45.50, 'alimentacion'),
    ('Gasolina', 60.00, 'transporte'),
    ('Netflix', 12.99, 'ocio'),
    ('Gimnasio', 35.00, 'salud');

SELECT * FROM gastos;
SELECT descripcion, cantidad FROM gastos WHERE categoria = 'alimentacion';
```

### Paso 7 — Verificar que desde internet no conecta

```bash
psql --host=ENDPOINT --port=5432 --username=devopsadmin --dbname=devopsdb
# Resultado: timeout, nunca conecta
```

No es que AWS rechace la conexión. Es que RDS no tiene IP pública
y no hay ruta física para llegar desde internet.
--no-publicly-accessible hace exactamente esto.

### Paso 8 — Eliminar la instancia

```bash
aws rds delete-db-instance \
  --db-instance-identifier devops-postgres \
  --skip-final-snapshot \
  --delete-automated-backups
```

---

## DynamoDB

### Qué es y qué lo diferencia de RDS

DynamoDB es una base de datos NoSQL creada por AWS desde cero.
No gestiona otro motor por debajo, ES el motor.
No tiene SQL, no tiene JOINs, no tiene esquema fijo.

### Tabla vs Database — diferencia con PostgreSQL

En PostgreSQL existe una jerarquía:
```
Servidor PostgreSQL
└── Database: devopsdb
    ├── Table: gastos
    └── Table: usuarios
```

En DynamoDB no existe el concepto de database.
Las tablas viven directamente en tu cuenta y región:
```
Cuenta AWS (eu-west-1)
├── Table: gastos-tracker
├── Table: usuarios
└── Table: pedidos
```

### Esquema flexible — la diferencia real con SQL

En PostgreSQL todas las filas tienen exactamente las mismas columnas.
En DynamoDB cada item puede tener atributos completamente distintos:

```python
item1 = {"user_id": "001", "descripcion": "Café",    "cantidad": "2.50"}
item2 = {"user_id": "001", "descripcion": "Gasolina", "cantidad": "60.00",
         "litros": "40", "estacion": "Repsol"}        # atributos extra
item3 = {"user_id": "002", "descripcion": "Gimnasio", "cantidad": "35.00",
         "tipo_pago": "mensualidad"}                  # atributo distinto
```

### Primary Key

```
Partition Key sola:       un atributo que identifica el item de forma única
                          DynamoDB lo usa para distribuir datos internamente

Partition Key + Sort Key: dos atributos combinados
                          Partition Key agrupa items relacionados
                          Sort Key los ordena dentro del grupo

Ejemplo usado en el lab:
  user_id (HASH) + timestamp (RANGE)
  todos los gastos del mismo usuario van juntos, ordenados cronológicamente
  permite consultar "gastos de usuario-001 entre dos fechas" eficientemente
```

### Billing modes

```
PAY_PER_REQUEST:  pagas solo por las operaciones que haces
                  sin capacidad mínima reservada
                  perfecto para cargas variables y aprendizaje

PROVISIONED:      reservas capacidad de lectura y escritura por hora
                  pagas aunque no uses la capacidad reservada
                  más barato a escala si el tráfico es predecible
```

### Query vs Scan — diferencia crítica

```
Query:  usa la Partition Key para ir directamente a los datos
        eficiente, solo lee los items que necesita
        SIEMPRE usar Query en producción

Scan:   recorre TODA la tabla item por item
        en una tabla con 10 millones de items, lee los 10 millones
        muy caro en producción
        solo para labs o migraciones puntuales
```

### Cómo DynamoDB devuelve atributos

DynamoDB envuelve los valores con su tipo:
```python
{"S": "texto"}    → String
{"N": "123"}      → Number
{"BOOL": True}    → Boolean

# Por eso accedes así en el código:
user_id  = item['user_id']['S']
cantidad = item['cantidad']['S']
```

---

## DynamoDB Streams

### Qué problema resuelve

```
Sin Streams:
Tu API → guarda gasto → envía email → actualiza inventario → notifica almacén
                              │
                  si el email falla, ¿qué pasa con el inventario?
                  todo está acoplado, un fallo rompe todo

Con Streams:
Tu API → guarda gasto → responde al usuario en milisegundos

En paralelo automáticamente:
  Lambda 1 → envía email           (si falla, no afecta a las demás)
  Lambda 2 → actualiza inventario  (si falla, se reintenta sola)
  Lambda 3 → notifica almacén      (independiente)
```

### Cómo funciona

DynamoDB Streams es como un vigilante mirando la tabla las 24 horas.
Cada vez que algo cambia apunta lo que pasó. Los eventos se guardan
durante 24 horas, después desaparecen.

### StreamViewType

```
KEYS_ONLY:           solo la clave del item que cambió
NEW_IMAGE:           cómo quedó el item después del cambio
OLD_IMAGE:           cómo era el item antes del cambio
NEW_AND_OLD_IMAGES:  ambos, útil para auditoría
```

### Casos de uso reales

```
Pedido insertado          → email automático al cliente
Usuario actualiza perfil  → invalida caché automáticamente
Item borrado              → auditoría, quién borró qué y cuándo
Precio modificado         → notificación a usuarios con el producto en favoritos
```

---

## Lambda — Serverless Computing

### Qué problema resuelve

Con EC2 pagas por hora aunque no haga nada.
Para tareas que ocurren raramente eso es un desperdicio enorme.

```
EC2 t3.micro procesando 10 fotos al día:
  Coste: ~$8/mes
  Tiempo real de trabajo: 20 segundos al día
  Pagas 24 horas para trabajar 20 segundos

Lambda procesando esas mismas 10 fotos:
  Coste: $0 (dentro del free tier de 1M invocaciones/mes)
  Solo se ejecuta cuando hay una foto que procesar
```

### Cómo funciona

```
Tú escribes:    def handler(event, context):
                    # tu código aquí
                    return resultado

AWS gestiona:   el servidor donde corre
                el SO y sus parches
                la memoria y la CPU
                el escalado automático
                la disponibilidad
```

Lambda no corre siempre. Se despierta cuando ocurre un evento,
ejecuta tu código, y desaparece. Si no hay eventos no pagas nada.

### Modelo de precio

```
1 millón de invocaciones gratis al mes (siempre, no solo Free Tier)
Después: $0.20 por cada millón adicional
+ tiempo de ejecución por GB-segundo
```

### Cuándo EC2 y cuándo Lambda

```
EC2:
  Procesos que corren continuamente
  Necesitas control total del SO
  Procesos que tardan más de 15 minutos (límite máximo de Lambda)
  Estado en memoria entre peticiones

Lambda:
  Reaccionar a eventos
  Tareas cortas y puntuales
  Carga impredecible o muy variable
  No quieres gestionar servidores
  Cron jobs simples
```

### Triggers — cómo se despierta Lambda

```
S3:               alguien sube un archivo       → Lambda procesa el archivo
API Gateway:      petición HTTP llega            → Lambda responde como servidor web
DynamoDB Streams: item cambia en tabla           → Lambda reacciona al cambio
SQS:              mensaje en cola                → Lambda procesa el mensaje
EventBridge:      cron job programado            → Lambda se ejecuta a la hora configurada
```

### Cold Start vs Warm Start

```
Cold start:   primera invocación o después de inactividad
              AWS inicializa el entorno → tarda más
              Python: ~80-300ms extra
              Java:   ~1-3 segundos extra (JVM lenta de arrancar)

Warm start:   Lambda ya estaba caliente
              ejecuta directamente tu código sin inicialización
```

Para DynamoDB Streams y tareas asíncronas el cold start no importa.
Para APIs con requisitos de latencia baja sí importa.

### Execution Role — sin credenciales en el código

```python
# MAL — nunca hagas esto
s3 = boto3.client('s3',
    aws_access_key_id='AKIA...',
    aws_secret_access_key='...'
)

# BIEN — boto3 detecta el Role automáticamente
s3 = boto3.client('s3', region_name='eu-west-1')
```

### Trust Policy vs Permission Policy

El IAM Role de Lambda tiene dos partes:

```
Trust Policy:       quién puede ASUMIR el Role
                    para Lambda: {"Service": "lambda.amazonaws.com"}
                    sin esto AWS no deja a Lambda usar el Role

Permission Policy:  qué puede HACER quien tenga el Role
                    AWSLambdaDynamoDBExecutionRole → leer Streams
                    AWSLambdaBasicExecutionRole    → escribir logs CloudWatch
```

### El Event Source Mapping — el cable que conecta todo

```
DynamoDB Stream ──── Event Source Mapping ────► Lambda
```

Sin él Lambda no sabe que existe el Stream y DynamoDB no sabe que existe Lambda.

```
starting-position LATEST:        procesa solo eventos nuevos desde ahora
starting-position TRIM_HORIZON:  procesa todos los eventos desde el inicio
batch-size 1:                    Lambda se dispara con cada item individualmente
```

### Cómo leer los logs de CloudWatch

```
INIT_START:      Lambda inicializando el entorno (cold start)
START:           comienza tu función handler()
...prints...     todo lo que hiciste print() en tu código
END:             termina tu función
REPORT:
  Duration:        cuánto tardó tu código exactamente
  Billed Duration: cuánto te cobra AWS (redondean al alza a 1ms)
  Memory Size:     RAM configurada
  Max Memory Used: RAM que realmente usó tu función
  Init Duration:   cuánto tardó el cold start
```

---

## Lab 2 — DynamoDB: crear tabla e insertar con boto3

### Tabla creada

```bash
aws dynamodb create-table \
  --table-name gastos-tracker \
  --attribute-definitions \
    AttributeName=user_id,AttributeType=S \
    AttributeName=timestamp,AttributeType=S \
  --key-schema \
    AttributeName=user_id,KeyType=HASH \
    AttributeName=timestamp,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST
```

### Inserción con boto3

```python
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
tabla = dynamodb.Table('gastos-tracker')

tabla.put_item(Item={
    "user_id":     "usuario-001",
    "timestamp":   "2026-03-12T08:00:00",
    "descripcion": "Café",
    "cantidad":    "2.50",
    "categoria":   "alimentacion"
})
```

### Query con Partition Key y Sort Key

```python
from boto3.dynamodb.conditions import Key

# Todos los gastos de un usuario
respuesta = tabla.query(
    KeyConditionExpression=Key('user_id').eq('usuario-001')
)

# Gastos después de una fecha usando la Sort Key
respuesta = tabla.query(
    KeyConditionExpression=
        Key('user_id').eq('usuario-001') &
        Key('timestamp').gte('2026-03-12T12:00:00')
)
```

### Lo que demostró el lab

Los items tenían atributos distintos: Gasolina tenía `litros` y `estacion`,
Gimnasio tenía `tipo_pago`, Café no tenía ninguno extra.
En PostgreSQL esas columnas existirían en todas las filas aunque estuvieran vacías.
En DynamoDB cada item solo guarda lo que necesita.

El Scan devolvió los items en orden diferente al de inserción porque DynamoDB
distribuye datos por Partition Key internamente. No garantiza orden en Scan.

---

## Lab 3 — DynamoDB Streams + Lambda

### Lo que se construyó

```
Script boto3 inserta gasto en DynamoDB
          │
          ▼
DynamoDB Streams captura el evento (NEW_IMAGE)
          │
          ▼
Event Source Mapping detecta el evento
          │
          ▼
Lambda procesar-gastos se ejecuta automáticamente
          │
          ▼
CloudWatch Logs guarda los prints de la función
```

### Infraestructura creada

```
Tabla:         gastos-tracker con Streams activados (NEW_IMAGE)
IAM Role:      lambda-dynamodb-streams-role
               AWSLambdaDynamoDBExecutionRole (leer Streams)
               AWSLambdaBasicExecutionRole    (escribir logs)
Función:       procesar-gastos, Python 3.12, 128MB, timeout 30s
Trigger:       Event Source Mapping Stream → Lambda, LATEST, batch-size 1
```

### El código de la función

```python
def handler(event, context):
    for record in event['Records']:
        evento_tipo = record['eventName']   # INSERT, MODIFY, REMOVE

        if evento_tipo == 'INSERT':
            nuevo_item = record['dynamodb']['NewImage']

            # DynamoDB envuelve valores con el tipo: {"S": "valor"}
            user_id     = nuevo_item['user_id']['S']
            descripcion = nuevo_item['descripcion']['S']
            cantidad    = nuevo_item['cantidad']['S']
            timestamp   = nuevo_item['timestamp']['S']

            print(f"Nuevo gasto: {descripcion} — {cantidad}€ — {user_id}")

    return {"statusCode": 200, "body": "Procesado"}
```

### Crear y desplegar la función

```bash
# Empaquetar código
zip lambda-gastos.zip handler.py

# Obtener ARN del Role
ROLE_ARN=$(aws iam get-role \
  --role-name lambda-dynamodb-streams-role \
  --query "Role.Arn" --output text)

# Crear función
aws lambda create-function \
  --function-name procesar-gastos \
  --runtime python3.12 \
  --handler handler.handler \
  --zip-file fileb://lambda-gastos.zip \
  --role $ROLE_ARN \
  --timeout 30 \
  --memory-size 128
```

### Conectar el Stream con Lambda

```bash
STREAM_ARN=$(aws dynamodb describe-table \
  --table-name gastos-tracker \
  --query "Table.LatestStreamArn" --output text)

aws lambda create-event-source-mapping \
  --function-name procesar-gastos \
  --event-source-arn $STREAM_ARN \
  --starting-position LATEST \
  --batch-size 1
```

### Invocar Lambda manualmente para debugging

```bash
aws lambda invoke \
  --function-name procesar-gastos \
  --payload '{"Records":[{"eventName":"INSERT","dynamodb":{"NewImage":{"user_id":{"S":"usuario-001"},"timestamp":{"S":"2026-03-15T11:00:00"},"descripcion":{"S":"Test"},"cantidad":{"S":"10.00"}}}}]}' \
  --cli-binary-format raw-in-base64-out \
  response.json
```

Útil para verificar que el código funciona independientemente del trigger.

### Ver logs en tiempo real

```bash
aws logs tail /aws/lambda/procesar-gastos --follow
```

---

## Lo que aprendí rompiendo cosas

**El Bastion tiene sg-public-web, no sg-app**
sg-database solo acepta tráfico desde sg-app → timeout al conectar.
En producción la capa de aplicación tiene sg-app, el Bastion no necesita acceso a la BD.

**La versión 16.3 de PostgreSQL ya no estaba disponible**
Siempre verificar versiones disponibles antes de crear:
```bash
aws rds describe-db-engine-versions --engine postgres \
  --query "DBEngineVersions[*].EngineVersion" --output table
```

**El trigger de DynamoDB Streams tardó en activarse**
Event Source Mapping decía Enabled pero LastProcessingResult era No records processed.
AWS tiene propagación eventual en algunos cambios de configuración.
Solución: esperar 2-3 minutos y reintentar antes de asumir que hay un bug.

**La invocación manual para debugging**
Cuando el trigger no funciona, invocar Lambda manualmente con payload de prueba
permite verificar que el código está bien independientemente del trigger.
Si la invocación manual funciona el problema está en la conexión, no en el código.

---

## Comandos útiles

### RDS

```bash
# Crear subnet group
aws rds create-db-subnet-group \
  --db-subnet-group-name NOMBRE \
  --db-subnet-group-description "descripción" \
  --subnet-ids subnet-xxx subnet-yyy

# Ver instancias
aws rds describe-db-instances \
  --query "DBInstances[*].{ID:DBInstanceIdentifier,Estado:DBInstanceStatus,Endpoint:Endpoint.Address}" \
  --output table

# Ver versiones disponibles
aws rds describe-db-engine-versions \
  --engine postgres \
  --query "DBEngineVersions[*].EngineVersion" \
  --output table

# Eliminar instancia
aws rds delete-db-instance \
  --db-instance-identifier NOMBRE \
  --skip-final-snapshot \
  --delete-automated-backups
```

### DynamoDB

```bash
# Crear tabla
aws dynamodb create-table --table-name NOMBRE ...

# Describir tabla
aws dynamodb describe-table --table-name NOMBRE

# Activar Streams
aws dynamodb update-table \
  --table-name NOMBRE \
  --stream-specification StreamEnabled=true,StreamViewType=NEW_IMAGE

# Desactivar Streams
aws dynamodb update-table \
  --table-name NOMBRE \
  --stream-specification StreamEnabled=false
```

### Lambda

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

# Ver función
aws lambda get-function --function-name NOMBRE

# Invocar manualmente
aws lambda invoke \
  --function-name NOMBRE \
  --payload '{}' \
  --cli-binary-format raw-in-base64-out \
  response.json

# Eliminar función
aws lambda delete-function --function-name NOMBRE

# Ver logs en tiempo real
aws logs tail /aws/lambda/NOMBRE --follow

# Ver Event Source Mappings
aws lambda list-event-source-mappings --function-name NOMBRE
```

---

## Cuándo usaría esto en trabajo real

```
RDS:
  API con datos relacionales: usuarios, pedidos, productos con relaciones
  Cualquier proyecto que ya use PostgreSQL o MySQL
  Cuando necesitas JOINs, transacciones ACID, esquema estricto

DynamoDB:
  Sesiones de usuarios        → clave: session_id, muy baja latencia
  Carritos de compra          → clave: user_id, items variables
  Historial de eventos        → clave: user_id + timestamp
  Configuración de features   → clave: feature_name, acceso instantáneo

Lambda + DynamoDB Streams:
  Email automático al registrarse un usuario
  Invalidar caché cuando cambia un producto
  Auditoría automática de cambios en datos sensibles
  Notificaciones push cuando llega un pedido nuevo
  Sincronización entre servicios desacoplados

Lambda standalone:
  Cron job que para EC2s de dev fuera de horario
  Procesamiento de archivos subidos a S3
  API REST serverless con API Gateway
  Cualquier tarea puntual que no justifica una EC2 encendida 24/7
```
