#!/bin/bash
# Script para probar Petra directamente desde el código fuente sin instalar

# Obtener el directorio donde está este script
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

# Moverse a la carpeta src y ejecutar
cd "$DIR"
echo "Iniciando Petra en modo local..."
exec python3 src/main.py "$@"
