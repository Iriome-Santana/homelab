# Scripts

## monitor-pro.sh

Script de monitoreo de recursos del sistema.

### Uso
```bash
./monitor-pro.sh [intervalo_segundos]
```

### Qué monitorea
- CPU: porcentaje de uso
- RAM: MB usados sobre total
- Disco: porcentaje de uso de la partición raíz

### Decisiones de diseño
- Logs con timestamp a stderr y a /tmp/monitor.log
- Logs a la carpeta /tmp ya que se eliminan tras reiniciar para evitar perder almacenamiento para un proyecto de
aprendizaje pero poder usar y comprobar logs
- Argumento opcional con valor por defecto de 10 segundos
- Validación de entrada — rechaza intervalos no numéricos
- Trap para cleanup garantizado aunque el script muera con error

### Ejemplo de salida
```
[2026-02-27 00:01:16] [INFO] CPU: 15.8% | RAM: 416/3915MB | Disco: 38%
```

## monitor.py

Script de monitoreo de recursos del sistema en Python.

### Uso
```bash
python3 monitor.py [--interval SEGUNDOS] [--json]
```

### Argumentos
- `--interval` — intervalo en segundos (default: 10)
- `--json` — output en formato JSON en lugar de logs

### Cuándo usar Python vs Bash
- Bash: scripts rápidos del sistema, pipes simples
- Python: cuando necesitas JSON, APIs, o lógica más compleja

### Ejemplo de output JSON
```json
{"timestamp": "2026-02-27T13:16:40+00:00", "cpu_percent": 0.0, 
 "ram": {"total": 3915, "used": 469, "available": 3446}, 
 "disk": {"total": "19G", "used": "7.3G", "percent": "42%"}}
```
