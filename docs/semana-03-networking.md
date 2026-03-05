# Semana 3 — Networking real

## Fecha: 01 Mar 2026

## Herramientas aprendidas

### tcpdump
tcpdump es una herramienta que sirve para capturar y ver el tráfico de red en tiempo real.
Permite observar los paquetes que entran y salen de una máquina, incluyendo direcciones IP, 
puertos y flags como SYN o ACK. Se usa para diagnosticar problemas de conectividad,
verificar si hay intentos de conexión y comprobar si existe respuesta desde el otro lado.
Es útil cuando necesitas ver qué está ocurriendo realmente a nivel de red entre cliente
y servidor
### TCP three-way handshake(explica SYN, SYN-ACK, ACK con tus palabras)
El TCP three-way handshake es el proceso inicial que establece una conexión TCP
entre cliente y servidor.
Primero el cliente envía un paquete SYN para iniciar la conexión, 
luego el servidor responde con SYN-ACK para confirmar que recibió
la solicitud y que está disponible,
y finalmente el cliente envía un ACK para confirmar que recibió la respuesta del servidor;
después de estos tres pasos la conexión queda establecida y pueden enviarse datos.
Es como un saludo formal de tres pasos antes de empezar una conversación.
### ss -tlnp
ss -tlnp muestra los puertos que están escuchando en el sistema, 
junto con el proceso que los está utilizando.
La opción -t filtra por TCP, -l muestra solo puertos en escucha, 
-n muestra números directamente, y -p indica el proceso asociado. 
Se usa para comprobar si un servicio realmente está activo y escuchando en el puerto esperado.

### dig
dig es una herramienta para consultar servidores DNS y obtener información sobre 
la resolución de nombres de dominio. Permite saber qué dirección IP está asociada a un dominio
y verificar si el DNS está funcionando correctamente.
Cuando devuelve NXDOMAIN significa que el dominio consultado no existe en el sistema DNS.

### curl -v
curl -v realiza una petición a un servidor y muestra información detallada del proceso de conexión, incluyendo resolución DNS, intento de conexión TCP, establecimiento de la conexión y respuesta HTTP. Si aparece "Connection refused", significa que la conexión llegó a la máquina pero no hay ningún servicio escuchando en ese puerto. Si aparece "timed out", significa que no se recibió ninguna respuesta dentro del tiempo esperado, lo que normalmente indica un problema de red, firewall o inaccesibilidad del host.

## Lo que me costó entender
Lo más difícil suele ser diferenciar en qué capa ocurre el problema: si es de DNS, de conexión TCP, de puerto no abierto o de aplicación no funcionando. Entender qué herramienta usar en cada caso y qué significa cada tipo de error requiere práctica y separar claramente resolución de nombres, establecimiento de conexión y respuesta del servicio.

## Sesión 2 — iptables

### Qué es iptables
Es la herramienta que controla el firewall, es como un portero que decide que entra, que sale y que pasa por
el servidor

### Las tres cadenas
Las tres cadenas son INPUT, FORWARD y OUTPUT:
INPUT se encarga de el tráfico que entra al servidor
FORWARD del que pasa por el servidor hacia otro destino
OUTPUT del tráfico que sale del servidor

### Lo que aprendí rompiendo cosas
Primero añadí una regla DROP a INPUT que SOLO permitía la entrada al servidor por SSH a mi IP, luego añadí una
una segunda regla DROP que no permitía a nadie entrar por SSH, en ese momento mi conexión por SSh se quedo congelada
y tuve que abrir la VM original para quitar la regla que prohibía la entrada a cualquier máquina.

### Por qué el orden importa
El orden importa ya que en mi ejemplo al primero colocar una regla DROP que solo excluía a mi IP pero no la salvaba
al añadir la segunsa regla DROP que bloqueaba todas las IPs ahí si fue cazada, si primero hubiera hecho
una regla ACCEPT y luego esa DROP no hubiera pasado nada ya que en orden ya estaba aceptada

## Sesión 3 — DNS en profundidad

### Cómo viaja una consulta DNS
Una consulta va desde tu servidor que la envía al resolver local, que lo manda a los servidores raíz 
que saben quien gestiona cada extensión, si por ejemplo estás intentando conectarte a google.com se comunican con 
el servidor .com y de ahí a Google y te devuelven su IP

### Qué es el resolver local
El resolver local es el proceso sytemd-resolved y es un intermediario entre la red local y la red pública
el resolver local recibe las consultas DNS del servidor, mira si tiene esa consulta en su caché para
usarla dierctamente, si no, pergunta a las adresses configuradas en tu netplan y guarda el caché y manda la 
consulta a los servidores raíz (las adresses de netplan)

### Diagnóstico de DNS roto
Primero probé a hacer dig a google.com para ver si el DNS estaba correcto, me apareció un error de timed out lo que
significa que puede que haya un problema de DNS, para probarlo hago un curl a google.com y aparece un error, lo que 
me dice que hay un problema de DNS o de red, para comprobar a curl a http://8.8.8.8 y funciona lo que
me garantiza que no es un problema de red y por ende es de DNS, abro el archivo de /etc/netplan/... y encuentro el
nameserver mal configurado y lo arreglo y hago netplan apply

### Lo que aprendí rompiendo cosas
Cambié las adresses de los nameservers para forzar un error de DNS y luego seguí el diagnóstico de DNS roto ya
explicado paso a paso para llegar a la solución

## Sesión 4 — TLS y certificados

### Qué es un certificado TLS
TLS es el certificado que hace que http se convierta en https, lo que significa que cifra la información y da una identidad
para más seguridad, partes importantes del certificado TLS son: Subject que es el dueño del certificado, Issuer que es quien
lo firma y la cadena de confianza que es como confía tu máquina en ese certificado: No solo confias en el servidor
si no el servidor tiene el certificado, ese certificado fue firmado (Issuer) por una CA, y esa CA está en la lista
de autoridades confiables, si la firma tiene una CA todo bien, si no no confía.

### Self-signed vs CA firmado
Self-signed significa que el certificado del servidor fue firmado por sí mismo, osea no hay una CA detrás que apruebe ese TLS,
hace que el navegador diga Conexión no segura ya que no confía en ese certificado, mientras CA firmado es cuando una autoridad
reconocida firma el TLS

### Comandos importantes
- openssl x509 -text -noout: inspeccionar certificado
- openssl x509 -checkend 0: verificar si está caducado
- openssl s_client -connect host:443: conectar y ver el certificado

### Lo que aprendí rompiendo cosas
con este comando openssl x509 -checkend 0 -noout -in cert.pem veo si mi certificado está caducado, si devuelve 
Certificate will not expire está correcto si dice Certificate will expire está caducado, luego miro directamente las fechas con:
echo | openssl s_client -connect midominio.com 2>/dev/null | openssl x509 -noout -dates

## Día 1 Docker avanzado — Dockerfile multi-stage y optimización

### Por qué optimizar imágenes
Porque una imagen optimizada ocupa menos en el disco, es más rápido y al optimizar es más escalable y versátil

### Alpine vs Ubuntu
Alpine es una especie de versión más pequeña de Ubuntu (aunque tiene pequeñas diferencias), es mejor 
usarla para imágenes que estrictamente tengan que pesar poco y no influya que tipo de OS se use.

### Non-root user
Es importante correr las imágenes como non-root por seguridad, se debe tener el menor acceso a root posible
producción

### Multi-stage build
Hace que las imágenes pesen mucho menos de lo que pesarían de normal, separas la compilación
del código corriendo as builder y después corres el script, así la imagen final no contiene el compilador ni el
código fuente.

### Resultados
- mi-primer-contenedor: 233MB (Ubuntu + bash)
- mi-contenedor-optimizado: 11.6MB (Alpine + bash)
- mi-app-go: 22MB (multi-stage, binario Go)

## Día 2 Docker avanzado — Docker networking

### Tipos de red en Docker
Hay 3 tipos de red:
1. bridge: es la red por defecto, donde van los contenedores si no se especifica.
2. host: es la red que se comparte directamente a la red de la VM, sin ningún aislamiento.
3. none: es una red sin conexión

### Redes personalizadas
Una red personañizada se usa para localizar mejor los contenedores por nombre, una red personalizada
se usa para varias cosas, como poder encontrar los contenedores por nombre, tener mejor organización
y mejor aislamiento

### Resolución por nombre
Cuando dos contenedores están dentro de la misma red personalizada de Docker,
pueden encontrarse por nombre porque Docker crea automáticamente un DNS interno dentro de esa red.
Ese DNS funciona como un traductor que convierte el nombre del contenedor en su dirección IP interna

### Aislamiento de red
El aislamiento de red es lo que logras al poner dos contenedores en diferentes redes,
se usa normalmente por seguridad por ejemplo el frontend no debe poder hablar directamente con la base de datos
y para eso se colocan en redes diferentes

### Por qué Docker Compose funciona sin configurar redes
Porque Docker Compose automáticamente asigna una red por defecto a cada proyecto para que puedan comunicarse

## Día 3 Docker avanzado — Variables de entorno y secrets

### El problema
Al hardcodear credenciales se quedan expuestas a que cualquier persona las tenga y las use

### Solución con .env
Si creas un archivo llamado .env y ahi escribes el nombre de la variable y la credencial después en el compose
puedes llamar directamente a esa variables sin necesidad de hardcodearla

### La regla de oro
El .env nunca va al repo, ya que sería contraproducente, haces el .env para que las credenciales no sean públicas y
solo pueda leerlas la variable de entorno

### .env.example
El .env.example se usa para dar contexto y enseñar que variables has usado para el proyecto sin mostrar tus
credenciales reales
