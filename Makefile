.PHONY: install run test backup list rotate

install:
	pip install -r requirements.txt --break-system-packages

run:
	python backup.py backup

backup:
	python backup.py backup

list:
	python backup.py list

rotate:
	python backup.py rotate

test:
	python -m pytest tests/ -v --tb=short
