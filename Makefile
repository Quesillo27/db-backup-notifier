.PHONY: install dev test lint docker clean backup list rotate stats help

## Instalar dependencias
install:
	pip install -r requirements.txt --break-system-packages

## Instalar en modo desarrollo (con virtualenv)
dev:
	python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

## Correr todos los tests
test:
	python3 -m pytest tests/ -v --tb=short

## Ejecutar backup
backup:
	python3 backup.py backup

## Listar backups existentes
list:
	python3 backup.py list

## Solo rotar backups viejos
rotate:
	python3 backup.py rotate

## Ver estadísticas de backups
stats:
	python3 backup.py stats --output table

## Build Docker multi-stage
docker:
	docker build -t db-backup-notifier .

## Limpiar artefactos
clean:
	rm -rf __pycache__ tests/__pycache__ .pytest_cache *.pyc

## Mostrar ayuda
help:
	@grep -E '^##' Makefile | sed 's/## //'
