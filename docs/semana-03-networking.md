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
