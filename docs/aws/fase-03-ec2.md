##Fase 03 — EC2 (más Labs)

#Qué es EC2 y por qué es lo primero

EC2 — Elastic Compute Cloud es el servicio de máquinas virtuales de AWS.
Es el más fundamental de toda la plataforma. Todo lo que viene después
(ECS, EKS, RDS, Lambda) o corre dentro de EC2 o nació como evolución de EC2.
Si no entiendes EC2 no entenderás por qué existen los demás servicios.

#AMI — Amazon Machine Image

Plantilla del sistema operativo. Como un snapshot de un disco con el SO preinstalado.
Se usa Amazon Linux 2023: distribución oficial de AWS, optimizada para EC2,
con AWS CLI preinstalada y soporte largo plazo. La más usada en empresas con AWS.

#Instance Types
Define CPU y RAM de la máquina:
t3.micro
│ └── tamaño: nano, micro, small, medium, large, xlarge
└──── familia: t (general), c (compute), r (memory), g (GPU)
Para aprender siempre t3.micro: 2 vCPU, 1GB RAM, Free Tier eligible.

#Key Pairs
Para conectarse por SSH no se usa usuario y contraseña, se usa un par de claves RSA.
AWS guarda la clave pública en la instancia, tú guardas el archivo .pem.
Sin ese archivo no puedes entrar nunca más. No se puede recuperar.

chmod 400 ~/.ssh/devops-key.pem   # obligatorio, SSH rechaza claves con permisos abiertos
ssh -i ~/.ssh/devops-key.pem ec2-user@IP-PUBLICA

#EBS Volumes

Disco persistente de la EC2:

Stop → la instancia se apaga, el disco y su contenido sobreviven
Terminate → la instancia se destruye, el disco se borra por defecto

#Diferencia importante para no perder trabajo:

usar Stop cuando terminas un lab, Terminate solo cuando quieres borrar todo.

#Elastic IPs

IP pública fija que no cambia aunque apagues y enciendas la instancia.
Por defecto las EC2 tienen IP pública dinámica: cambia en cada arranque.
Descubierto en la práctica: al volver al lab al día siguiente la IP había cambiado
y hubo que buscarla de nuevo antes de conectarse por SSH.

En producción eso es un problema: tu dominio apuntaría a una IP que ya no existe.
La Elastic IP lo resuelve. Para aprender no se usa porque cobra cuando no está
asociada a una instancia encendida.

#User Data

Script bash que se ejecuta automáticamente la primera vez que la instancia arranca.
Base de la automatización: la instancia se configura sola sin intervención manual.

#!/bin/bash
dnf update -y
dnf install -y nginx
systemctl start nginx
systemctl enable nginx
echo "<h1>Configurado con User Data</h1>" > /usr/share/nginx/html/index.html

#IAM Instance Profile

Forma de asignar un IAM Role a una EC2.
Cuando la instancia necesita acceder a S3 u otro servicio AWS,
no se meten credenciales en el código. Se asigna un Role y la instancia
lo asume automáticamente. La AWS CLI dentro de la instancia lo detecta sola.
Se creó el Role ec2-s3-readonly-role con AmazonS3ReadOnlyAccess.

#Por qué ReadOnly y no FullAccess: principio de mínimo privilegio.

Si alguien compromete la instancia, solo puede leer S3, no borrar ni escribir.

#Instance Metadata Service

Endpoint especial solo accesible desde dentro de una EC2: 169.254.169.254
Es como el localhost de la instancia para hablar con AWS.
Desde fuera no funciona porque es una IP de enlace local, nunca sale de la máquina.
Amazon Linux 2023 usa la versión 2 (IMDSv2) que requiere token por seguridad.
La versión 1 era vulnerable: una app con vulnerabilidad podía robar credenciales
del IAM Role preguntando al metadata service. La v2 lo impide.

# Obtener token primero
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")

# Usar el token en cada consulta
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/placement/availability-zone

curl -s -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/iam/security-credentials/

curl -s -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/public-ipv4

#Bastion Host

Instancia EC2 en subnet pública que sirve como puente para acceder
a instancias en subnets privadas. Las instancias privadas no tienen IP pública.
Tu máquina → SSH → Bastion (subnet pública) → SSH → Instancia privada (subnet privada)

#Modelos de precio — salen en el examen

On-Demand:     por hora sin compromiso
               para aprender y cargas impredecibles

Reserved:      compromiso 1-3 años, hasta 72% descuento
               para cargas estables y predecibles en producción

Spot:          hasta 90% descuento, AWS puede terminarla sin aviso
               para cargas que toleran interrupciones: batch jobs, rendering

Savings Plans: compromiso de gasto en $/hora, más flexible que Reserved
               cubre EC2, Lambda y Fargate

##Lab 1 — Lo que se construyó

Instancia ec2-public-bastion en public-subnet-1a con sg-public-web y ec2-s3-readonly-role
Conexión por SSH con devops-key.pem verificada
Nginx instalado manualmente y respondiendo por HTTP en el puerto 80
Metadata service consultado: AZ eu-west-1a confirmada, Role ec2-s3-readonly-role confirmado

#Lo que aprendí rompiendo cosas

Al intentar parar la instancia desde dentro de ella con AWS CLI apareció este error:
assumed-role/ec2-s3-readonly-role is not authorized to perform: ec2:StopInstances

La instancia usaba el Role ec2-s3-readonly-role que solo tiene permisos en S3.
No puede parar instancias EC2 porque no tiene ese permiso.
Es el principio de mínimo privilegio funcionando exactamente como debe en la práctica.
La solución fue salir de la instancia y ejecutar el comando desde la máquina local
donde la CLI usa las credenciales de devops-admin con AdministratorAccess.

Lección: siempre tener claro desde qué identidad estás ejecutando comandos AWS.
Dentro de una EC2 eres el Role de esa instancia, no tu usuario IAM local.
Comandos útiles EC2

# Ver instancias y su estado

aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=NOMBRE" \
  --query "Reservations[0].Instances[0].{IP:PublicIpAddress,Estado:State.Name,AZ:Placement.AvailabilityZone}" \
  --output table

# Parar instancia

aws ec2 stop-instances --instance-ids \
  $(aws ec2 describe-instances \
    --filters "Name=tag:Name,Values=NOMBRE" "Name=instance-state-name,Values=running" \
    --query "Reservations[0].Instances[0].InstanceId" \
    --output text)

# Iniciar instancia

aws ec2 start-instances --instance-ids \
  $(aws ec2 describe-instances \
    --filters "Name=tag:Name,Values=NOMBRE" \
    --query "Reservations[0].Instances[0].InstanceId" \
    --output text)

#Cuándo lo usaría en trabajo real

EC2 es la base de casi todo en AWS, entenderla bien hace que ECS y EKS tengan sentido
El Instance Profile con Role es siempre la forma correcta de dar permisos a una instancia
Nunca meter Access Keys dentro de una EC2, siempre usar Roles
El metadata service se usa en scripts de arranque para que la instancia
sepa en qué entorno está (dev, staging, prod según la AZ o tags)
Stop para pausar labs, Terminate para limpiar recursos que ya no necesitas

##Lab 2 — User Data

#Qué es User Data

Script bash que se ejecuta automáticamente la primera vez que una instancia arranca.
La instancia se configura sola sin intervención manual.

#Por qué existe
En el Lab 1 el flujo fue:
Lanzar instancia → SSH → instalar nginx manualmente → configurar → salir

Eso funciona para una instancia. Pero si tienes 50 instancias, o si Auto Scaling
lanza nuevas instancias automáticamente cuando hay carga, no puedes entrar
por SSH a cada una manualmente.

User Data resuelve esto:
Lanzar instancia → esperar → ya está configurada y funcionando

#Script usado

#!/bin/bash
dnf update -y
dnf install -y nginx
systemctl start nginx
systemctl enable nginx
echo "<h1>Servidor configurado con User Data</h1>" > /usr/share/nginx/html/index.html

#Comportamiento importante

User Data solo se ejecuta UNA vez: la primera vez que la instancia arranca.
Si apagas y vuelves a encender, no se ejecuta de nuevo.
El sistema ya está configurado y no necesita repetirlo.

#Lo que se verificó

curl a la IP pública devolvió el HTML personalizado sin haber entrado
a la instancia por SSH ni una sola vez. Nginx estaba corriendo y configurado
automáticamente desde el primer arranque.

#Cuándo lo usaría en trabajo real

Configuración inicial de servidores en Auto Scaling Groups

Instalación de agentes de monitorización (CloudWatch Agent, Datadog...)

Registro automático del servidor en sistemas de configuración

Base de cualquier infraestructura inmutable: la instancia nace configurada,
nunca se modifica manualmente después

##Lab 3 — Instancia en subnet privada

#Qué se demostró

Una instancia en subnet privada no tiene IP pública y no es accesible desde internet.
Es el aislamiento de red en la práctica.

#Verificaciones realizadas

IP pública:          None          → no existe, no hay forma de llegar desde internet

curl a google.com:   timeout       → no hay salida a internet sin NAT Gateway

curl desde local:    se queda esperando → la IP privada no es enrutable desde internet

#Por qué las subnets privadas existen

Cualquier recurso que no necesite recibir tráfico directamente de internet
no debería estar expuesto. Mínima superficie de ataque.

Bases de datos, servicios internos, workers de procesamiento → subnet privada.

Servidores web, load balancers → subnet pública.

#Aislamiento completo de la subnet privada

Desde internet → no puede entrar   (sin IP pública)
Desde dentro   → no puede salir    (sin NAT Gateway)
Desde el Bastion → sí puede entrar (misma VPC, Security Group permite SSH)

##Lab 4 — Bastion Host

#Por qué no puedes hacer SSH directo a una instancia privada

Dos razones, en orden de importancia:

No tiene IP pública. No hay dirección a la que apuntar desde internet.
Es como intentar llamar a alguien que no tiene teléfono.

El Security Group no tiene el puerto 22 abierto desde internet.

#Qué es el Bastion Host

Instancia EC2 en subnet pública que actúa como único punto de entrada SSH
a toda la infraestructura privada.

Tu máquina → SSH → Bastion 10.0.1.x (IP pública, sg-public-web)
                       │
                       └→ SSH → ec2-private 10.0.3.x (solo IP privada, sg-app)

#SSH Agent Forwarding

Para el salto en dos pasos la clave .pem no se copia al Bastion.

Se usa SSH Agent Forwarding: el agente SSH de tu máquina local
presta la clave para ambos saltos sin que salga de tu máquina.

eval $(ssh-agent -s)                    # iniciar el agente SSH

ssh-add ~/.ssh/devops-key.pem           # añadir la clave al agente

ssh -A -i ~/.ssh/devops-key.pem \       # -A activa Agent Forwarding
  -J ec2-user@IP-BASTION \             # -J define el salto intermedio
  ec2-user@IP-PRIVADA

#Por qué el Bastion existe en producción real

Es el único punto de entrada SSH a toda la infraestructura
Solo el puerto 22 del Bastion está abierto a internet, desde IPs concretas
Todo el acceso SSH pasa por ahí: logs centralizados de quién entró,
cuándo y a qué máquina
Si hay un incidente de seguridad, cierras el Bastion y nadie entra a nada

#Lo que se añadió al Security Group

sg-app → Inbound → SSH puerto 22 desde sg-public-web

Solo instancias con sg-public-web (el Bastion) pueden hacer SSH a la instancia privada.

##Lab 5 — IAM Role y boto3 sin credenciales

#Qué es boto3

SDK oficial de AWS para Python. Librería que permite hablar con la API de AWS
desde código Python sin construir peticiones HTTP manualmente.
Cualquier cosa que puedes hacer en la consola o con la CLI, puedes hacerla con boto3.
En DevOps se usa para automatizar: backups, limpieza de recursos, monitorización, despliegues.

#El script

pythonimport boto3

s3 = boto3.client('s3')
# No se pasan credenciales. boto3 sigue el mismo orden que la CLI:
# 1. Variables de entorno
# 2. ~/.aws/credentials
# 3. IAM Role de la instancia  ← esto es lo que usó

response = s3.list_objects_v2(Bucket='devops-lab-iriome-2026')

for obj in response.get('Contents', []):
    print(f"  - {obj['Key']}")
Lo importante — lo que NO se hizo
No se escribió esto en ningún momento:
pythons3 = boto3.client('s3',
    aws_access_key_id='AKIAIOSFODNN7EXAMPLE',
    aws_secret_access_key='wJalrXUtnFEMI/K7MDENG'
)


No hay credenciales en el código. boto3 las obtuvo automáticamente
del Role ec2-s3-readonly-role asignado a la instancia.
AWS genera credenciales temporales para ese Role que expiran cada pocas horas.
Si alguien entra a la instancia sin autorización y roba el código,
no hay credenciales que robar. El Role solo funciona desde dentro
de esta instancia específica.

Esa es la diferencia entre código seguro e inseguro en AWS.

#Bucket S3 creado

aws s3 mb s3://devops-lab-iriome-2026 --region eu-west-1

aws s3 cp prueba.txt s3://devops-lab-iriome-2026/

aws s3 ls s3://devops-lab-iriome-2026/

Nombres de bucket: solo minúsculas, números y guiones. Globales en todo AWS,
no puede haber dos iguales en el mundo.
