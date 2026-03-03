LIBRARY_NAME := $(shell cd src && hatch project metadata name 2> /dev/null)
LIBRARY_VERSION := $(shell cd src && hatch version 2> /dev/null)

.PHONY: usage install uninstall check pytest qa build-deps check tag wheel sdist clean dist testdeploy deploy
usage:
ifdef LIBRARY_NAME
	@echo "Library: ${LIBRARY_NAME}"
	@echo "Version: ${LIBRARY_VERSION}\n"
else
	@echo "WARNING: You should 'make dev-deps'\n"
endif
	@echo "Usage: make <target>, where target is one of:\n"
	@echo "install:      install the library locally from source"
	@echo "dev-deps:     install Python dev dependencies"
	@echo "qa:           run linting and package QA"
	@echo "pytest:       run Python test fixtures"
	@echo "clean:        clean Python build and dist directories"
	@echo "build:        build Python distribution files"

version:
	@hatch version

install:
	pip install src/

dev-deps:
	python3 -m pip install -r requirements-dev.txt

qa:
	cd src && tox -e qa

pytest:
	cd src && tox -e py

build:
	@cd src && hatch build src/

clean:
	-rm -r src/dist
