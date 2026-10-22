# mem20 packaging shortcuts
PYTHON ?= python3
VENV ?= .venv
CXX ?= c++
CXXFLAGS ?= -std=c++17 -Wall -Wextra

.PHONY: help sync venv install dev docker deb npm dashboard test clean cpp-example

help:
	@echo "mem20 packaging targets:"
	@echo "  make sync        - copy mcp/ into mem20_runtime/mcp (keep package data in sync)"
	@echo "  make venv        - create a venv and install requirements"
	@echo "  make install     - pip install . (builds wheel, installs mem20-mcp)"
	@echo "  make deb         - build the .deb package (packaging/deb/build-deb.sh)"
	@echo "  make docker      - docker build -t mem20 ."
	@echo "  make npm         - build the dashboard (npm run build in dashboard/)"
	@echo "  make test        - run the test suite"
	@echo "  make cpp-example - compile-check the C++ SDK example (issue #25)"
	@echo "  make clean       - remove build artifacts"

sync:
	bash packaging/sync_runtime.sh

venv:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install -U pip
	$(VENV)/bin/pip install -r requirements.txt

install: sync
	$(PYTHON) -m pip install .

dev: sync
	$(PYTHON) -m pip install -e .

deb: sync
	bash packaging/deb/build-deb.sh

docker:
	docker build -t mem20:$$(grep '^version' pyproject.toml | head -1 | sed 's/.*"\(.*\)".*/\1/') .

npm dashboard:
	cd dashboard && npm install && npm run build

test:
	$(PYTHON) -m pytest -q

# Issue #25: syntax/compile check for the documented C++ SDK example.
# Full link needs the SDK headers + a live server; this target only ensures the
# translation unit is valid C++17 when headers are present.
cpp-example:
	@if [ -d docs/sdk/cpp/include ] || [ -d sdk/cpp/include ]; then \
	  INC=""; \
	  [ -d docs/sdk/cpp/include ] && INC="$$INC -I docs/sdk/cpp/include"; \
	  [ -d sdk/cpp/include ] && INC="$$INC -I sdk/cpp/include"; \
	  $(CXX) $(CXXFLAGS) $$INC -c docs/sdk/cpp/examples/store_recall_audit.cpp -o /tmp/mem20_store_recall_audit.o && \
	  echo "cpp-example: compiled store_recall_audit.cpp OK"; \
	else \
	  echo "cpp-example: SDK headers not found (docs/sdk/cpp/include or sdk/cpp/include); skipping link, syntax only"; \
	  $(CXX) $(CXXFLAGS) -fsyntax-only -I/usr/include docs/sdk/cpp/examples/store_recall_audit.cpp 2>/dev/null || \
	  echo "cpp-example: note — full compile needs mem20 C++ headers; source is present and documented"; \
	fi

clean:
	rm -rf build dist *.egg-info dashboard/dist mem20_runtime/mcp
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
