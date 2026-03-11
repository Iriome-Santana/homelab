##Fase 02 — VPC y Networking

#El problema que resuelve VPC

Sin VPC todos los recursos de AWS estarían en la misma red plana y accesibles entre sí.
Un servidor web público, una base de datos con datos de clientes y sistemas internos
todos en la misma red sin separación es un desastre de seguridad.
Si alguien compromete el servidor web, tiene acceso directo a la base de datos.

VPC — Virtual Private Cloud es tu red privada virtual dentro de AWS.
Control total sobre rangos de IPs, segmentación en subnets, qué accede a internet y qué no,
y qué puede hablar con qué.

#CIDR — Rangos de IPs

Forma de expresar un rango de IPs:
10.0.0.0/16  →  65,536 IPs  (los primeros 16 bits fijos)
10.0.0.0/24  →  256 IPs     (los primeros 24 bits fijos)
10.0.0.0/32  →  1 IP exacta (todos los bits fijos)

Cuanto más grande el número después de /, menos IPs disponibles.
Para una VPC se usa típicamente /16.

#Subnets públicas y privadas

Una VPC bien diseñada separa los recursos en subnets según si necesitan
acceso desde internet o no.
VPC: 10.0.0.0/16
├── Subnet Pública AZ-a:  10.0.1.0/24  → recursos accesibles desde internet
├── Subnet Pública AZ-b:  10.0.2.0/24  → alta disponibilidad
├── Subnet Privada AZ-a:  10.0.3.0/24  → recursos internos, sin acceso directo
└── Subnet Privada AZ-b:  10.0.4.0/24  → alta disponibilidad
El servidor web recibe tráfico de internet → subnet pública.
La base de datos nunca debería ser accesible desde internet → subnet privada.
Si alguien compromete el servidor web, todavía tiene que superar otra capa para llegar a la BD.
Se crearon dos subnets en AZs distintas de cada tipo para alta disponibilidad.
Si una AZ falla, la otra sigue funcionando.

#Internet Gateway (IGW)

Puerta de entrada y salida a internet para la VPC.
Sin IGW nada en la VPC puede comunicarse con internet.
Se adjunta a la VPC, no a una subnet específica.

#Route Tables

Tablas de enrutamiento que dicen a cada subnet hacia dónde mandar el tráfico
Subnet pública:
10.0.0.0/16  →  local        (tráfico interno a la VPC)
0.0.0.0/0    →  igw-xxx      (todo lo demás va a internet)
Subnet privada:
10.0.0.0/16  →  local        (tráfico interno a la VPC)
0.0.0.0/0    →  nat-xxx      (todo lo demás va al NAT Gateway)
La diferencia clave: la pública manda tráfico externo al IGW,
la privada lo manda al NAT Gateway.

#NAT Gateway

Permite que recursos en subnets privadas salgan a internet
pero bloquea cualquier conexión entrante desde internet.
Subnet Privada → NAT Gateway (en subnet pública) → IGW → Internet
                                         NO entra tráfico ◄───┘

El NAT Gateway vive en la subnet pública porque necesita acceso bidireccional.
Tiene coste por hora aunque no pase tráfico (~$32/mes). Se crea solo cuando se necesita.

#Security Groups

Firewall virtual que se aplica a nivel de recurso individual (EC2, RDS, ECS...).
Define qué tráfico puede entrar (inbound) y salir (outbound).
Por defecto al crear un Security Group:

Todo inbound está bloqueado
Todo outbound está permitido

Son stateful: si permites una conexión entrante, la respuesta saliente
se permite automáticamente sin regla explícita de salida.
Referencia entre Security Groups: en lugar de poner una IP como origen,
puedes poner otro Security Group. Solo el tráfico de recursos con ese SG puede entrar.

##Arquitectura en capas creada:

sg-public-web  →  puerto 80/443 desde 0.0.0.0/0, puerto 22 desde mi IP
sg-app         →  puerto 8000 solo desde sg-public-web
sg-database    →  puerto 5432 solo desde sg-app

La base de datos nunca ve tráfico de internet. Solo habla con la API.
La API solo habla con el load balancer.

#NACLs — Network Access Control Lists

Otro nivel de firewall pero a nivel de subnet completa, no de recurso individual.
Diferencias con Security Groups:
Security Groups  →  stateful    →  nivel de recurso  →  solo Allow
NACLs            →  stateless   →  nivel de subnet   →  Allow y Deny explícitos

Stateless significa que si permites tráfico entrante en puerto 80,
tienes que crear también la regla de salida para la respuesta manualmente.
En la práctica los Security Groups son el mecanismo principal del día a día.

#VPC creada — devops-vpc
VPC:              devops-vpc     10.0.0.0/16
IGW:              devops-igw     adjunto a devops-vpc
public-subnet-1a: 10.0.1.0/24   eu-west-1a
public-subnet-1b: 10.0.2.0/24   eu-west-1b
private-subnet-1a: 10.0.3.0/24  eu-west-1a
private-subnet-1b: 10.0.4.0/24  eu-west-1b
Route table pública: 0.0.0.0/0 → devops-igw, asociada a las dos subnets públicas

##Comandos útiles VPC

bashaws ec2 describe-vpcs --filters "Name=tag:Name,Values=devops-vpc"

aws ec2 describe-subnets --filters "Name=vpc-id,Values=VPC-ID" --output table

aws ec2 describe-security-groups --filters "Name=vpc-id,Values=VPC-ID" --output table

#Lo que aprendí construyendo la VPC
Construirla manualmente componente a componente (VPC → subnets → IGW → route tables → SGs)
hace que Terraform tenga mucho más sentido después. Cuando automatices esto con código
sabrás exactamente qué está creando cada bloque porque lo hiciste a mano primero.
El orden importa: sin IGW no hay salida a internet, sin route table la subnet
no sabe a dónde mandar el tráfico aunque el IGW exista.

#Cuándo lo usaría en trabajo real

Toda infraestructura en producción vive en una VPC, nunca en la red por defecto de AWS
Separar subnets públicas y privadas es el estándar mínimo de seguridad
Los Security Groups en cadena (web → app → db) son la arquitectura estándar
Si algo falla con "connection refused" o "timeout", lo primero que revisas es
el Security Group del recurso destino y la route table de la subnet
