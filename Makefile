build:
	python setup.py sdist bdist_wheel
upload:
	twine upload dist/*

install: install-poetry
	poetry install

install-poetry:
	pip install poetry
	pip install poetry-dynamic-versioning

test-cov:
	poetry run pytest --cov=touchprice --cov-report=xml --cov-report=term