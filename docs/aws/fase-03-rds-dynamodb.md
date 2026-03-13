# AWS — Fase 03 RDS y DynamoDB

## Fecha: Marzo 2026

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

## DynamoDB

### Qué es

NoSQL gestionado por AWS. No gestiona otro motor por debajo, ES el motor.
Creado por AWS desde cero para escala masiva y latencia ultra baja.

No es como PostgreSQL. No tiene tablas con esquema fijo ni relaciones.
Cada item puede tener campos completamente distintos.

### Cuándo usar RDS y cuándo DynamoDB

```
RDS (SQL):
  Datos relacionales: usuarios, pedidos, productos relacionados entre sí
  Queries complejas con JOINs
  Transacciones ACID
  Esquema conocido y estable

DynamoDB (NoSQL):
  Escala masiva: millones de operaciones por segundo
  Datos simples: clave → valor o documentos JSON
  Latencia ultra baja garantizada
  Sin esquema fijo, datos variables
  Siempre gratis hasta 25GB → perfecto para aprender
```

### Conceptos core de DynamoDB

**Table**: equivalente a una tabla en SQL pero sin esquema fijo.
Cada item puede tener atributos distintos.

**Item**: equivalente a una fila en SQL. Conjunto de atributos.

**Attribute**: equivalente a una columna en SQL pero opcional por item.

**Primary Key**: obligatoria en todos los items, dos tipos:
```
Partition Key sola:      un atributo que identifica el item únicamente
                         ejemplo: user_id

Partition Key + Sort Key: dos atributos combinados que identifican el item
                          ejemplo: user_id + timestamp (para historial de eventos)
```

DynamoDB usa la Partition Key para distribuir los datos entre servidores internamente.
Elegir bien la Partition Key es crítico para el rendimiento.

---

## DynamoDB Streams

### Qué problema resuelve

Sin Streams si quieres reaccionar a cambios en DynamoDB tienes que
poner esa lógica dentro del mismo código que hace el cambio.
El código se complica, los servicios se acoplan, si falla un paso
puede afectar al guardado del dato.

Con Streams cada cambio en la tabla genera un evento automáticamente.
Otros servicios (Lambda principalmente) reaccionan a esos eventos
de forma independiente y desacoplada.

```
Tu código inserta pedido en DynamoDB
         │
         ▼
DynamoDB Streams captura el evento
         │
         ▼
Lambda se activa automáticamente
         │
         ├→ Lambda 1: envía email de confirmación
         ├→ Lambda 2: actualiza inventario
         └→ Lambda 3: notifica al almacén
```

Tu código que inserta el pedido no sabe nada de emails ni inventarios.
Solo inserta. El resto ocurre automáticamente.

### Tipos de información que captura el Stream

```
KEYS_ONLY:           solo la clave del item que cambió
NEW_IMAGE:           cómo quedó el item después del cambio
OLD_IMAGE:           cómo era el item antes del cambio
NEW_AND_OLD_IMAGES:  ambos, útil para auditoría
```

Los eventos se guardan durante 24 horas.

### Casos de uso reales

```
Pedido insertado          → email automático al cliente
Usuario actualiza perfil  → invalida caché automáticamente
Item borrado              → auditoría, quién borró qué y cuándo
Precio modificado         → notificación a usuarios con el producto en favoritos
```

Es el patrón event-driven: los servicios reaccionan a eventos
en lugar de llamarse entre sí directamente.
Más desacoplado, más escalable, más fácil de mantener.

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
-- Verificar versión
SELECT version();

-- Crear tabla
CREATE TABLE gastos (
    id SERIAL PRIMARY KEY,
    descripcion VARCHAR(100),
    cantidad DECIMAL(10,2),
    categoria VARCHAR(50),
    fecha DATE DEFAULT CURRENT_DATE
);

-- Insertar datos
INSERT INTO gastos (descripcion, cantidad, categoria) VALUES
    ('Supermercado', 45.50, 'alimentacion'),
    ('Gasolina', 60.00, 'transporte'),
    ('Netflix', 12.99, 'ocio'),
    ('Gimnasio', 35.00, 'salud');

-- Consultar todo
SELECT * FROM gastos;

-- Consultar con filtro
SELECT descripcion, cantidad FROM gastos WHERE categoria = 'alimentacion';
```

### Paso 7 — Verificar que desde internet no conecta

Desde la máquina local sin pasar por el Bastion:
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

RDS cobra por hora aunque esté parada.
Siempre eliminar al terminar el lab, nunca hacer stop.

---

## Lo que aprendí rompiendo cosas

**El Bastion tiene sg-public-web, no sg-app**
sg-database solo acepta tráfico desde sg-app.
Intentar conectarse desde el Bastion sin añadir la regla → timeout.
Lección: los Security Groups en cadena funcionan exactamente como se diseñaron.
En producción la app tiene sg-app, el Bastion no necesita acceso a la BD.

**La versión 16.3 de PostgreSQL ya no estaba disponible**
aws rds describe-db-engine-versions para ver versiones disponibles antes de crear.
Lección: las versiones disponibles cambian con el tiempo, siempre verificar.

---

## Ejemplo real de lo que construiste

```
Usuario abre la app de gastos en el móvil
      │
      ▼
Load Balancer (subnet pública)
      │
      ▼
Servidores FastAPI (subnet pública, sg-public-web + sg-app)
      │ la app necesita leer y escribir gastos
      ▼
RDS PostgreSQL (subnet privada, sg-database)
      │ solo acepta conexiones desde sg-app
      │ internet nunca llega aquí físicamente
      ▼
Datos del usuario guardados de forma segura
```

Si un atacante compromete el servidor web llega a la subnet pública.
Para llegar a la base de datos necesita sg-app, que solo tienen
los servidores de aplicación. Una capa más de seguridad que superar.

---

## Comandos útiles RDS

```bash
# Crear subnet group
aws rds create-db-subnet-group \
  --db-subnet-group-name NOMBRE \
  --db-subnet-group-description "descripción" \
  --subnet-ids subnet-xxx subnet-yyy

# Ver instancias RDS
aws rds describe-db-instances \
  --query "DBInstances[*].{ID:DBInstanceIdentifier,Estado:DBInstanceStatus,Endpoint:Endpoint.Address}" \
  --output table

# Ver versiones disponibles de un motor
aws rds describe-db-engine-versions \
  --engine postgres \
  --query "DBEngineVersions[*].EngineVersion" \
  --output table

# Eliminar instancia sin snapshot
aws rds delete-db-instance \
  --db-instance-identifier NOMBRE \
  --skip-final-snapshot \
  --delete-automated-backups
```
