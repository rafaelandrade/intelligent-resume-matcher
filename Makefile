.PHONY: help setup format format-modified lint lint-fix test clean

VENV_DIR := .venv venv env
IGNORE_DIRS := $(VENV_DIR) __pycache__ .git .pytest_cache .mypy_cache build dist

EXCLUDE_PATTERN := $(shell echo $(IGNORE_DIRS) | sed 's/ /|/g')

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup:
	pip install black isort flake8 mypy pytest

format:
	black --exclude "($(EXCLUDE_PATTERN))" .
	isort --skip $(IGNORE_DIRS) .

format-modified:
	git ls-files --modified --others --exclude-standard "*.py" | xargs -r black
	git ls-files --modified --others --exclude-standard "*.py" | xargs -r isort

lint:
	flake8 --exclude $(EXCLUDE_PATTERN) .
	mypy --exclude $(EXCLUDE_PATTERN) .

lint-fix:
	$(MAKE) format-modified

test:
	pytest

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.eggs" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.dist-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +

venv:
	python -m venv .venv
	@echo "Execute 'source .venv/bin/activate' para ativar o ambiente"

default: help