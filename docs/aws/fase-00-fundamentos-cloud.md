AWS — Fase 00 y Fase 01
Fecha inicio: Marzo 2026

Configuración inicial de la cuenta

#Lo primero antes de tocar nada

Antes de aprender AWS hay que dejar la cuenta segura. Una cuenta mal configurada puede generar
cargos inesperados o problemas de seguridad graves.

#Cuenta Root

La cuenta Root es la que se crea al registrarse en AWS. Tiene acceso absoluto a todo y no se puede
restringir. Nunca se usa para el trabajo diario, solo para tareas administrativas puntuales.
Lo primero que hay que hacer es activarle MFA.

#MFA — Multi-Factor Authentication

El MFA añade una segunda capa de seguridad. Además de la contraseña, necesitas un código
de 6 dígitos que cambia cada 30 segundos desde una app como Google Authenticator o Authy.
Se activa en IAM → Security credentials → Assign MFA device.
Se activó MFA tanto en Root como en el usuario IAM devops-admin.

#Budget de alerta

Se configura en Billing → Budgets → Zero spend budget.
Manda un email en cuanto se gaste cualquier cosa fuera del Free Tier.
Es la red de seguridad para no llevarse sorpresas en la factura.

#Región

Todos los recursos son por región. Para aprender desde España se usa eu-west-1 (Irlanda)
porque es la región europea más cercana y tiene todos los servicios disponibles.
Si cambias de región en la consola, no verás los recursos de otra región.

#Usuario IAM devops-admin

Se creó un usuario IAM llamado devops-admin con la política AdministratorAccess para
usarlo en el día a día en lugar de Root. Tiene MFA activado.
La URL de login IAM tiene este formato:
https://ID-CUENTA.signin.aws.amazon.com/console

##Fase 00 — Fundamentos de Cloud

#El problema que existía antes de la nube

Antes de la nube, montar una aplicación requería comprar servidores físicos, instalarlos
en un datacenter, contratar electricidad, refrigeración y personal. Todo esto antes de
escribir una línea de código. Si la app crecía, repetías el proceso. Si fracasaba,
te quedabas con servidores caros que no usas. El problema no era solo el dinero,
era el tiempo y la rigidez.

#Qué cambió con AWS

AWS apareció en 2006 con la idea de que los servidores funcionaran como la electricidad:
no compras tu propio generador, simplemente conectas y pagas por lo que consumes.
En lugar de comprar servidores los alquilas por horas, en lugar de esperar semanas
los tienes en minutos, en lugar de pagar por capacidad máxima pagas por lo que usas.

#IaaS, PaaS y SaaS

Existen tres modelos de servicio cloud, de más a menos control:

· IaaS — Infrastructure as a Service
Te dan la infraestructura bruta y tú gestionas todo lo demás.
Como alquilar un piso vacío: las paredes son del casero pero tú pones los muebles.
Ejemplo en AWS: EC2. Te dan una máquina virtual y tú instalas el SO, la app, lo mantienes.
Máximo control, máxima responsabilidad.

· PaaS — Platform as a Service
Te dan una plataforma donde despliegas tu código y ellos gestionan la infraestructura.
Como alquilar un piso amueblado: solo traes tu ropa.
Ejemplo en AWS: Elastic Beanstalk. Subes tu app y AWS gestiona los servidores.
Menos control, menos responsabilidad.

· SaaS — Software as a Service
Usas directamente la aplicación final sin gestionar nada.
Ejemplos: Gmail, Slack, Notion.

#Regions y Availability Zones

Region: zona geográfica completa que contiene varias AZs.
Ejemplos: eu-west-1 (Irlanda), eu-central-1 (Frankfurt), us-east-1 (Virginia).
Cuanto más cerca la región de tus usuarios, menos latencia.
Muchas empresas europeas tienen obligación legal de que sus datos no salgan de la UE.

Availability Zone (AZ): uno o más datacenters físicos separados entre sí por kilómetros
dentro de una misma región, conectados con fibra de alta velocidad.
eu-west-1 tiene tres AZs: eu-west-1a, eu-west-1b, eu-west-1c.
REGION: eu-west-1 (Irlanda)
├── AZ: eu-west-1a  →  Datacenter(s) en ubicación A
├── AZ: eu-west-1b  →  Datacenter(s) en ubicación B
└── AZ: eu-west-1c  →  Datacenter(s) en ubicación C

Por qué existen las AZs: si un datacenter tiene un problema, los otros siguen funcionando.
Si tu aplicación está en múltiples AZs, un fallo en una no tumba el servicio.

#Modelo de responsabilidad compartida

AWS es responsable de la seguridad de la nube:
datacenters físicos, hardware, red global, refrigeración, hipervisores.
Tú eres responsable de la seguridad en la nube:
permisos IAM, cifrado de datos, vulnerabilidades de tu aplicación,
configuración de acceso a tus recursos.
Ejemplo concreto: si alguien hackea tu base de datos porque la dejaste abierta a internet
sin contraseña, es tu responsabilidad. Si alguien entra físicamente al datacenter de Irlanda
y roba un disco duro, es responsabilidad de AWS.

#Alta disponibilidad vs Tolerancia a fallos

Conceptos distintos con implicaciones distintas.

Alta disponibilidad: el sistema sigue funcionando aunque algo falle, pero puede haber
una interrupción breve mientras se recupera. Tu app está en dos AZs, si una cae
la otra toma el tráfico en segundos.

Tolerancia a fallos: el sistema sigue funcionando sin ninguna interrupción aunque algo falle.
Requiere redundancia activa en todo momento. Más caro y más complejo.
Ejemplo: un avión con dos motores, si falla uno el otro mantiene el vuelo sin que nadie note nada.
En la mayoría de aplicaciones web se busca alta disponibilidad, no tolerancia a fallos total,
porque el coste de tolerancia a fallos completa es enorme.

#Escalado horizontal vs vertical

· Escalado vertical: hacer más grande la máquina que tienes.
4 CPUs → 16 CPUs. Tiene límite físico y requiere apagar la máquina.
· Escalado horizontal: añadir más máquinas iguales en lugar de una grande.
Más resiliente (si una falla las otras siguen), más barato a escala, sin límite práctico.
La nube está diseñada para escalar horizontalmente.

#AWS Well-Architected Framework

Framework oficial de AWS que define cómo diseñar infraestructura bien hecha. 6 pilares:

Operational Excellence: automatizar operaciones, mejorar procesos
Security: proteger datos, gestionar identidades, detectar incidentes
Reliability: recuperarse de fallos, escalar según demanda
Performance Efficiency: usar recursos de forma eficiente
Cost Optimization: eliminar gasto innecesario
Sustainability: minimizar impacto medioambiental
