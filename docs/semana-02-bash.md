# Semana 2 — Bash profesional

## Fecha: 27 Feb 2026

## La plantilla profesional
- set -euo pipefail: esta linea de código sirve para captar errores del bash de manera profesional
-e cuando un comando falla para todo el script
-u: si hay una variable no definida en vez de hacer la vista gorda salta un error de variable no definida
-o pipefail: si cualquier parte del pipe falla, falla todo el script
- Por qué los logs van a stderr y no a stdout: stdout es para la salida útil del script — los datos que produce. stderr es para todo lo que el humano necesita leer: logs, warnings, errores. Así se pueden separar — si alguien usa el script en un pipe o redirige la salida a un fichero, los logs no contaminan los datos.
- Para qué sirve el trap: Sirve para capturar el EXIT de un script y hacer un cleanup de los archivos para que no queden sueltos tras un
error en el script

## Funciones en bash
Primero se pone el nombre de la funcion acompañado de (), ejemplo(), luego abres corchetes { escribes la lógica de la funcion y la cierras } y la llamas simplemente poniendo el nombre, ejemplo, y si tiene argumentos se los pones al lado, ejemplo 2 3

## Argumentos
- $1, $2, $#: $1 se refiere al primer argumento del script, $2 al segundo y $# el número de argumentos
- Valor por defecto con ${1:-valor}: el valor por defecto sería el que pongas después de - donde en el ejemplo pone -valor
- Validación con expresiones regulares: && es si la sentencia de la izquierda es verdadera haz lo siguiente y || es si la sentencia de la
derecha no es verdadera haz lo siguiente

## awk
awk sirve para sacar las columnas y poder elegir una en concreto por ejemplo: CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}') ahí dice
CPU es igual a el comando de la cpu la parte de CPUs exactamente (awk) el segundo elemento de la columna y con NR puedes elegir la linea exacta de la columna
## Lo que me costó entender
awk al principio me costó un poco, la sintaxis general de Bash es algo que me costó y que sigo aprendiendo
