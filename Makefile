.PHONY: test lint clean-pyc clean-build clean-test build

clean: clean-pyc clean-build clean-test

clean-pyc:
	find . -name '*.pyc' -exec rm --force {} +
	find . -name '*.pyo' -exec rm --force {} +
	find . -name '*~' -exec rm --force {} +
	find . -name '__pycache__' -exec rmdir {} +

clean-test:
	rm --force --recursive .coverage
	rm --force --recursive .pytest_cache

clean-build:
	rm --force --recursive build/
	rm --force --recursive dist/
	rm --force --recursive *.egg-info

build:
	python -m build

lint:
	flake8

type-check:
	mypy .

test:
	pytest

test-coverage:
	coverage run --source carton -m pytest
	coverage report -m

test-all: lint type-check test-coverage