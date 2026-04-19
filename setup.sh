#!/usr/bin/env bash
# Setup rápido de db-backup-notifier en un comando
set -e

echo "==> Instalando dependencias..."
pip install -r requirements.txt --break-system-packages

echo "==> Copiando .env.example → .env..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "    Edita .env con tus credenciales antes de ejecutar."
else
    echo "    .env ya existe — omitiendo."
fi

echo ""
echo "✅ Setup completo."
echo "   Próximos pasos:"
echo "   1. Edita .env con tus credenciales de PostgreSQL y Telegram"
echo "   2. Ejecuta: python3 backup.py backup"
echo "   3. Agrega al cron: 0 3 * * * cd $(pwd) && python3 backup.py backup >> /var/log/db-backup.log 2>&1"
