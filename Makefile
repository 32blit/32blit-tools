LIBRARY_VERSION=$(shell grep version src/setup.cfg | awk -F" = " '{print $$2}')
LIBRARY_NAME=$(shell grep name src/setup.cfg | awk -F" = " '{print $$2}')

.PHONY: usage install uninstall
usage:
	@echo "${LIBRARY_NAME}"
	@echo "Version: ${LIBRARY_VERSION}\n"
	@echo "Usage: make <target>, where target is one of:\n"
	@echo "install:       install ${LIBRARY_NAME} locally from source"
	@echo "uninstall:     uninstall ${LIBRARY_NAME}"
	@echo "check:         peform basic integrity checks on the codebase"
	@echo "python-readme: generate src/README.md from README.md + src/CHANGELOG.txt"
	@echo "python-wheels: build python .whl files for distribution"
	@echo "python-sdist:  build python source distribution"
	@echo "python-clean:  clean python build and dist directories"
	@echo "python-dist:   build all python distribution files"
	@echo "python-testdeploy: build all and deploy to test PyPi"
	@echo "tag:           tag the repository with the current version"

install:
	./install.sh

uninstall:
	./uninstall.sh

check:
	@echo "Checking for trailing whitespace"
	@! grep -IUrn --color "[[:blank:]]$$" --exclude-dir=sphinx --exclude-dir=.tox --exclude-dir=.git --exclude=PKG-INFO
	@echo "Checking for DOS line-endings"
	@! grep -IUrn --color "" --exclude="*.tmx" --exclude-dir=sphinx --exclude-dir=.tox --exclude-dir=.git --exclude=Makefile
	@echo "Checking src/CHANGELOG.txt"
	@cat src/CHANGELOG.txt | grep ^${LIBRARY_VERSION}
	@echo "Checking src/ttblit/__init__.py"
	@cat src/ttblit/__init__.py | grep "^__version__ = '${LIBRARY_VERSION}'"

tag:
	git tag -a "v${LIBRARY_VERSION}" -m "Version ${LIBRARY_VERSION}"

python-readme: src/README.md

python-license: src/LICENSE.txt

src/README.md: README.md src/CHANGELOG.txt
	cp README.md src/README.md
	printf "\n\n# Changelog\n\n" >> src/README.md
	cat src/CHANGELOG.txt >> src/README.md

src/LICENSE.txt: LICENSE
	cp LICENSE src/LICENSE.txt

python-wheels: python-readme python-license
	cd src; python3 setup.py bdist_wheel

python-sdist: python-readme python-license
	cd src; python3 setup.py sdist

python-clean:
	-rm -r src/dist
	-rm -r src/build
	-rm -r src/*.egg-info

python-dist: python-clean python-wheels python-sdist
	ls src/dist
	-python3 -m twine check src/dist/*

python-testdeploy: python-dist
	twine upload --repository testpypi src/dist/*

python-deploy: check python-dist
	twine upload src/dist/*
