PYTHON  ?= python3
VENV    := .venv
BIN     := $(VENV)/bin
CONFIG  ?= config.txt
MAIN    := a_maze_ing.py
ANALYZER:= maze_analyzer.py
OUTPUT  ?= maze.txt
MLX_TGZ := mlx-2.2.tgz

# Development tools. They are not runtime dependencies: the project only
# needs the Python standard library to run.
DEV_TOOLS  := build flake8 mypy pytest

MYPY_FLAGS := --warn-return-any --warn-unused-ignores \
              --ignore-missing-imports --disallow-untyped-defs \
              --check-untyped-defs

# Directories flake8 must not walk into. They hold no source of ours, only
# the virtual environment and the build artefacts.
FLAKE8_FLAGS := --extend-exclude=.venv,venv,build,dist,.mlx

.PHONY: all install install-mlx run debug analyze clean fclean lint \
        lint-strict test build re help

all: run

## install: create a virtual environment and install the dev dependencies
install:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install $(DEV_TOOLS)

## install-mlx: install the optional MiniLibX wrapper (Linux only)
install-mlx:
	@test -f $(MLX_TGZ) || { \
	    echo "$(MLX_TGZ) not found: copy it from the subject."; exit 1; }
	@rm -rf .mlx && mkdir -p .mlx && tar xzf $(MLX_TGZ) -C .mlx
	@set -e; \
	if [ -f /etc/fedora-release ]; then flavour=fedora; else flavour=ubuntu; fi; \
	echo "Installing the $$flavour MiniLibX wheel..."; \
	$(BIN)/pip install --force-reinstall \
	    .mlx/$$flavour/mlx-2.2-py3-none-any.whl
	@rm -rf .mlx
	@echo "Now set DISPLAY=mlx in $(CONFIG) to open a graphical window."

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
	$(PYTHON) $(ANALYZER) $(OUTPUT) --max-dead-ends 0

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
	rm -rf __pycache__ */__pycache__ .mypy_cache .pytest_cache .mlx
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
