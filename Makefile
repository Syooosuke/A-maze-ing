PYTHON  ?= python3
VENV    := .venv
BIN     := $(VENV)/bin
CONFIG  ?= config.txt
MAIN    := a_maze_ing.py
ANALYZER:= maze_analyzer.py
OUTPUT  ?= maze.txt

# Development tools. They are not runtime dependencies: the project only
# needs the Python standard library to run.
DEV_TOOLS  := build flake8 mypy pytest

MYPY_FLAGS := --warn-return-any --warn-unused-ignores \
              --ignore-missing-imports --disallow-untyped-defs \
              --check-untyped-defs

# Directories flake8 must not walk into. They hold no source of ours, only
# the virtual environment and the build artefacts.
FLAKE8_FLAGS := --extend-exclude=.venv,venv,build,dist

.PHONY: all install run debug analyze clean fclean lint \
        lint-strict test build re help

all: run

## install: create a virtual environment and install the dev dependencies
install:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install $(DEV_TOOLS)

## run: generate and display a maze from $(CONFIG)
run:
	$(PYTHON) $(MAIN) $(CONFIG)

## debug: run the program under the Python debugger
debug:
	$(PYTHON) -m pdb $(MAIN) $(CONFIG)

## analyze: check $(OUTPUT) with the analysis script of the subject
analyze:
	@test -f $(ANALYZER) || { \
	    echo "$(ANALYZER) not found: copy it from the subject."; exit 1; }
	@$(PYTHON) $(MAIN) $(CONFIG) < /dev/null > /dev/null
	$(PYTHON) $(ANALYZER) $(OUTPUT)

## lint: flake8 + mypy with the flags required by the subject
lint:
	$(BIN)/flake8 . $(FLAKE8_FLAGS)
	$(BIN)/mypy . $(MYPY_FLAGS)

## lint-strict: flake8 + mypy in strict mode
lint-strict:
	$(BIN)/flake8 . $(FLAKE8_FLAGS)
	$(BIN)/mypy . --strict

## test: run the unit tests (tests/ is not part of the submission)
test:
	@test -d tests || { echo "no tests/ directory here."; exit 1; }
	PYTHONPATH=. $(BIN)/pytest -q tests

## build: rebuild the pip package and copy the wheel at the root
build:
	rm -rf dist build *.egg-info
	$(BIN)/python -m build --wheel
	cp dist/mazegen-*.whl .
	rm -rf build dist *.egg-info

## clean: remove caches and temporary files
clean:
	find . -path ./.venv -prune -o -name __pycache__ -type d -prune \
	    -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache
	rm -rf build dist *.egg-info
	find . -name '*.py[co]' -delete

## fclean: clean, and also drop the virtual environment and the output maze
fclean: clean
	rm -rf $(VENV)
	rm -f maze.txt

re: fclean install

## help: list the available rules
help:
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/^## //'
