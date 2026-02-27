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
- Argumento opcional con valor por defecto de 10 segundos
- Validación de entrada — rechaza intervalos no numéricos
- Trap para cleanup garantizado aunque el script muera con error

### Ejemplo de salida
```
[2026-02-27 00:01:16] [INFO] CPU: 15.8% | RAM: 416/3915MB | Disco: 38%
```
