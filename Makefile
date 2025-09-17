build:
	uv build

upload:
	uv publish

install: install-uv
	uv sync

install-uv:
	curl -LsSf https://astral.sh/uv/install.sh | sh

test:
	uv run --group test pytest tests/ -v

test-cov:
	uv run --group test pytest tests/ --cov=vnpy_sinopac --cov-report=xml --cov-report=term -v

dev-install:
	uv sync --extra dev

clean:
	rm -rf dist/ build/ *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

.PHONY: build upload install install-uv test test-cov dev-install clean