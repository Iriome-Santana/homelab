#!/usr/bin/env python3
"""Monitor de recursos del sistema."""

import subprocess
import json
import logging
import argparse
import time
from datetime import datetime, timezone

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger(__name__)


def get_cpu() -> float:
    """Obtiene el porcentaje de CPU usado."""
    result = subprocess.run(
        ['top', '-bn1'],
        capture_output=True,
        text=True
    )
    for line in result.stdout.split('\n'):
        if 'Cpu(s)' in line:
            return float(line.split()[1])
    return 0.0


def get_ram() -> dict:
    """Obtiene el uso de RAM en MB."""
    result = subprocess.run(
        ['free', '-m'],
        capture_output=True,
        text=True
    )
    lines = result.stdout.split('\n')
    mem = lines[1].split()
    return {
        'total': int(mem[1]),
        'used': int(mem[2]),
        'available': int(mem[6])
    }


def get_disk() -> dict:
    """Obtiene el uso del disco raíz."""
    result = subprocess.run(
        ['df', '-h', '/'],
        capture_output=True,
        text=True
    )
    lines = result.stdout.split('\n')
    disk = lines[1].split()
    return {
        'total': disk[1],
        'used': disk[2],
        'percent': disk[4]
    }


def collect_metrics() -> dict:
    """Recoge todas las métricas y las devuelve como dict."""
    return {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'cpu_percent': get_cpu(),
        'ram': get_ram(),
        'disk': get_disk()
    }


def main():
    parser = argparse.ArgumentParser(description='Monitor de recursos')
    parser.add_argument(
        '--interval',
        type=int,
        default=10,
        help='Intervalo en segundos (default: 10)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output en formato JSON'
    )
    args = parser.parse_args()

    log.info(f"Monitor iniciado — intervalo: {args.interval}s")

    try:
        while True:
            metrics = collect_metrics()
            if args.json:
                print(json.dumps(metrics))
            else:
                log.info(
                    f"CPU: {metrics['cpu_percent']}% | "
                    f"RAM: {metrics['ram']['used']}/{metrics['ram']['total']}MB | "
                    f"Disco: {metrics['disk']['percent']}"
                )
            time.sleep(args.interval)
    except KeyboardInterrupt:
        log.info("Monitor detenido")


if __name__ == '__main__':
    main()
