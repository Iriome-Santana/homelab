# Semana 1 — Linux Filesystem y Permisos

## Fecha: 25 Feb 2026

## Lo que aprendí hoy

### /proc
Es un directorio del sistema que abre una ventana a nivel de kernel que no se puede escribir pero si leer, cada vez que lees algo de dentro el kernel lo genera y borra sin tocar el disco

### Árbol de procesos
El árbol de procesos está definido por PID1 que es el padre directa o indirectamente de todos los procesos de Linux y es el primer proceso que se abre

### Permisos
Los permisos son lo que dejas hacer al usuario, grupo o otros, se pueden dar y quitar de 2 formas:
1. Con sintaxis más legible: chmod u+w fichero.txt. La idea principal es poner a quien va dirigido (en este caso u user), si das o quitas (en este caso + dar) y que permiso (en este caso w escribir)
2. Con números: r = 4. w = 2, x = 1, y se suman en cada uno, por ejemplo 755, 7 corresponde a 4 + 2 + 1 para el user osea que tendría todos los permisos, 5 corresponde a 4 + 1 osea que grupos podrían leer y ejecutar, y lo mismo para otros. 

## Comandos que debo recordar
chmod (número) (archivo o directorio)

## Lo que me costó entender
Todo lo relacionado a los procesos me costó pillarlo al principio

## Sesión 2 — Systemd y servicios

### Systemd
Systemd es lo que mantiene vivo todos los servicios de Linux, como cron, ssh, etc... los mantiene vivos y usables.

### Comandos systemctl importantes
sudo systemctl daemon-reload: systemd relee todos los servicios, obligatorio cuando se añade uno nuevo.
sudo systemctl enable (servicio): activa el servicio para que se use siempre aunque reinicies el servidor
sudo systemctl start (servicio): empieza el servicio que seguirá las instrucciones puestas en el .service.
sudo systemctl stop (servicio): para el servicio de manera premeditada y sin fallos
sudo systemctl restart (servicio): reinicar el servicio, cambiando también la fecha.
systemctl status (servicio): ver el estado del servicio en ese momento

### Lo que aprendí sobre logs
journalctl es el comando para ver los logs del servicio especificado.

### Mi primer servicio
Hice un servicio de un script básico de monitoreo, lo creé en /opt luego creé el .service lo empecé y
vi los logs en journalctl en tiempo real con sudo journalctl -u monitor.service -f, luego hice
un pequeño experimento en el que mientras corria el servicio y veia los logs maté el proceso con kill -9
eso hizo que diera un pequeño error y luego automaticamente se reiniciara, diferente a lo que pasaria si lo "matas"
con systemctl stop

## Sesión 3 — Almacenamiento y rendimiento

### Comandos de disco
- df -h: espacio usado por filesystem
- du -sh /*: qué directorio ocupa más
- iostat -x 1 3: rendimiento del disco, %util es lo importante

### Comandos de memoria
- free -h: RAM total, usada, disponible
- Diferencia free vs available: free es RAM vacía, available incluye caché que se puede liberar

### Comandos de CPU
- top / htop: procesos ordenados por CPU
- Columnas CPU: us=usuario, sy=kernel, id=idle, wa=esperando disco

### Diagnóstico de un servidor lento
Al notar un servidor lento lo primero que se debe hacer es top o htop (top preferiblemente para un script,
htop en general) y matar o investigar procesos sospechosos, luego vemos la RAM con free -h, nos fijamos en
el available y no en el free y comprobar swap, luego comprobamos disco con iostat nos fijamos en %util y await 
