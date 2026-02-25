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
