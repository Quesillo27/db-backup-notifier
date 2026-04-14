FROM python:3.11-slim

# Instalar cliente PostgreSQL para pg_dump
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Directorio de backups por defecto
VOLUME ["/backups"]

# Ejecutar backup al iniciar el container
CMD ["python", "backup.py", "backup"]
