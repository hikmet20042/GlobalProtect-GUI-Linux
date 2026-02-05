.PHONY: test lint package-deb package-rpm package-mint

test:
	python -m unittest discover -s tests -v

lint:
	python -m py_compile app.py gp_gui/*.py
	bash -n scripts/build-deb.sh scripts/build-rpm.sh scripts/globalprotect-gui

package-deb:
	./scripts/build-deb.sh

package-mint:
	./scripts/build-deb.sh

package-rpm:
	./scripts/build-rpm.sh
