##Fase 03 — EC2 (Lab 1)

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

#Lab 1 — Lo que se construyó

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
