##Fase 01 — IAM, Identidad y Seguridad base

#El problema que resuelve IAM

Sin IAM la única opción sería dar a todos las credenciales de Root.
Cualquiera podría hacer cualquier cosa, sin trazabilidad de quién hizo qué.
IAM permite definir quién puede hacer qué sobre qué recursos.

#Users — Usuarios - Personas

Representa a una persona o aplicación que necesita acceder a AWS.
Tiene sus propias credenciales: usuario y contraseña para la consola,
o Access Keys para la terminal.
En una empresa real: maria.garcia, juan.lopez, sistema-backups...

#Groups — Grupos

Colección de usuarios. En lugar de asignar permisos uno a uno,
los asignas al grupo y todos los usuarios del grupo los heredan.
Los grupos no pueden contener otros grupos, solo usuarios.
Ejemplo: grupo developers con permisos para desplegar en EC2 y ECS.

#Roles

No son para personas, son para servicios y aplicaciones.
Cuando un servidor EC2 necesita leer archivos de S3, no le das usuario y contraseña.
Le asignas un Role con los permisos necesarios. El servidor lo asume automáticamente
sin credenciales hardcodeadas en el código.

· Regla: Users para humanos, Roles para máquinas y procesos automatizados.
Un Role también sirve para dar acceso temporal a usuarios de otras cuentas AWS
o a identidades externas (como cuando una empresa usa Google como sistema de login).

#Policies — Políticas

Documento JSON que define qué acciones están permitidas o denegadas,
sobre qué recursos y bajo qué condiciones. Se asignan a Users, Groups o Roles.
Estructura básica:

{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::mi-bucket/*"
    }
  ]
}

Leído en voz alta: Permitir la acción s3:GetObject (descargar archivos) sobre el recurso mi-bucket y todo su contenido.

Effect: Allow o Deny
Action: qué operación (s3:GetObject, ec2:StartInstances, iam:CreateUser...)
Resource: sobre qué recurso específico usando el ARN

AdministratorAccess en JSON es simplemente:
json{ "Effect": "Allow", "Action": "*", "Resource": "*" }
Allow, cualquier acción, sobre cualquier recurso. El permiso más amplio posible.
Nunca se usa así en producción.

#ARN — Amazon Resource Name

Identificador único de cualquier recurso en AWS.
Formato:
arn:aws:SERVICIO:REGIÓN:ID-CUENTA:RECURSO

Ejemplos:
arn:aws:s3:::mi-bucket
arn:aws:ec2:eu-west-1:123456789012:instance/i-1234567890abcdef0
arn:aws:iam::123456789012:user/devops-admin

El * funciona como comodín. arn:aws:s3:::mi-bucket/* significa
"todos los objetos dentro de mi-bucket".

#Principio de mínimo privilegio

El principio de seguridad más importante en AWS y en seguridad en general.
Da siempre el mínimo permiso necesario para hacer el trabajo, nunca más.
En producción cada usuario, grupo y role tiene exactamente los permisos que necesita para su función, ni uno más.

#Access Keys

Cuando una aplicación o la terminal necesita hablar con AWS usa Access Keys.
Tienen dos partes:

Access Key ID: como el usuario
Secret Access Key: como la contraseña, solo se muestra una vez al crearla

Reglas de oro:

Nunca subirlas a GitHub (AWS tiene bots que las detectan en tiempo real)
Nunca meterlas directamente en el código
Rotarlas periódicamente
Si se comprometen, desactivarlas inmediatamente en IAM

#AWS CLI

Herramienta de línea de comandos oficial de AWS.
Permite hacer desde la terminal todo lo que harías en la consola web.

Instalación:
bashcurl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
aws --version

Configuración:
bashaws configure

# Pide: Access Key ID, Secret Access Key, región (eu-west-1), formato (json)
# Guarda credenciales en ~/.aws/credentials
# Guarda config en ~/.aws/config

Verificar que funciona:
bashaws sts get-caller-identity

#Orden de búsqueda de credenciales en CLI

Cuando ejecutas cualquier comando AWS CLI busca credenciales en este orden:

Variables de entorno (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
~/.aws/credentials
IAM Role (si estás en una instancia EC2 o servicio AWS)

Los servicios como EC2 o Lambda nunca usan ~/.aws/credentials.
Usan el IAM Role asignado automáticamente, que es más seguro
porque las credenciales rotan solas.

##Comandos IAM y STS útiles

bashaws sts get-caller-identity                                        # quién soy ahora mismo

aws iam list-users                                                 # listar usuarios IAM

aws iam list-groups                                                # listar grupos IAM

aws iam list-attached-user-policies --user-name devops-admin      # políticas de un usuario

aws ec2 describe-regions --output table                           # regiones disponibles

#IAM Policy Simulator

Herramienta para verificar si un usuario o role tiene permiso para hacer algo
antes de ejecutarlo en producción.

URL: policysim.aws.amazon.com

Seleccionas usuario, servicio y acción → Run Simulation → te dice allowed o denied.
Muy útil cuando tienes roles con permisos específicos y necesitas verificar
si pueden hacer algo concreto sin tener que ejecutarlo y ver si falla.

#Labs realizados

Creé el grupo devops-team con AdministratorAccess y añadí devops-admin al grupo
Inspeccioné el JSON de AdministratorAccess para entender cómo se ve una policy real
Creé la policy personalizada S3ReadOnly-custom con permisos solo de lectura en S3
Configuré AWS CLI y verifiqué autenticación con aws sts get-caller-identity
Usé el Policy Simulator para verificar permisos de devops-admin

#Lo que aprendí rompiendo cosas

El concepto de Roles no es intuitivo al principio porque estás acostumbrado a pensar
en credenciales como algo que tiene una persona. El cambio mental es entender que
una máquina o servicio nunca debería tener credenciales estáticas, siempre un Role
que AWS gestiona y rota automáticamente. Si metes Access Keys en el código y lo subes
a GitHub, aunque lo borres después el daño ya está hecho porque GitHub guarda el historial.

#Cuándo lo usaría en trabajo real

Alguien del equipo se va de la empresa: deshabilitas su usuario IAM, no cambias la contraseña de Root

Nuevo desarrollador entra: lo añades al grupo con los permisos correctos, no configuras permisos uno a uno

Un script de automatización necesita acceder a AWS: le creas un Role específico, no le das tus Access Keys

Algo falla con Access Denied: lo primero que revisas es qué políticas tiene el usuario o role que está 
ejecutando la acción

En producción: nadie tiene AdministratorAccess salvo el equipo de platform/infrastructure
