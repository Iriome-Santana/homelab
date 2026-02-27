#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

LOGFILE="/tmp/monitor.log"
INTERVALO=${1:-10}

log()  { echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO]  $*" | tee -a "$LOGFILE" >&2; }
error(){ echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $*" | tee -a "$LOGFILE" >&2; }
die()  { error "$*"; exit 1; }

cleanup() {
    log "Monitor detenido"
}
trap cleanup EXIT

[[ $# -gt 1 ]] && die "Uso: $0 [intervalo_segundos]"
[[ $INTERVALO =~ ^[0-9]+$ ]] || die "El intervalo debe ser un número"

log "Monitor iniciado — intervalo: ${INTERVALO}s"

while true; do
    CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}')
    RAM_USADO=$(free -m | awk 'NR==2{print $3}')
    RAM_TOTAL=$(free -m | awk 'NR==2{print $2}')
    DISCO=$(df -h / | awk 'NR==2{print $5}')

    log "CPU: ${CPU}% | RAM: ${RAM_USADO}/${RAM_TOTAL}MB | Disco: ${DISCO}"
    sleep "$INTERVALO"
done
