include $(HOME)/projects/py-tooling/Makefile.common

install-playwright:
	uv run playwright install chromium

.PHONY: install-playwright
