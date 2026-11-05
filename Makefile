.DEFAULT_GOAL := help
.PHONY: help build check diagrams shots _shots serve status

CHROME ?= google-chrome
SITE   := site
SHOTS  := output/shots

# Public-text guard: generic patterns live in tools/check-public.py; confidential terms come from the
# ignored file forbidden.local (one per line) or from FORBIDDEN_EXTRA (CI secret), never from this file.
PUBLIC_PATHS := APRESENTACAO.md RESUMO.md README.md deck deck-resumo $(SITE)/index.html $(SITE)/resumo.html $(wildcard $(SITE)/img/*.svg)

help: ## Lista os comandos
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-9s\033[0m %s\n", $$1, $$2}'

build: ## Gera site/index.html (deck/) e site/resumo.html (deck-resumo/)
	python3 tools/build-site.py deck $(SITE)/index.html
	python3 tools/build-site.py deck-resumo $(SITE)/resumo.html RESUMO.md

diagrams: ## Renderiza os diagramas Mermaid dos roteiros em site/img/diag-*.svg (requer google-chrome)
	python3 tools/render-diagrams.py APRESENTACAO.md $(SITE)/img --chrome $(CHROME)
	python3 tools/render-diagrams.py RESUMO.md $(SITE)/img --chrome $(CHROME)

check: build ## Testes, build, diagramas em dia e guarda de texto público
	@python3 -m unittest
	@python3 tools/check-diagrams.py APRESENTACAO.md RESUMO.md $(SITE)/img
	@python3 tools/check-public.py $(PUBLIC_PATHS)
	@echo "ok"

shots: build ## PNG por slide em output/shots/ e output/shots-resumo/ para conferência (requer google-chrome)
	@$(MAKE) -s _shots PAGE=index DIR=$(SHOTS)
	@$(MAKE) -s _shots PAGE=resumo DIR=$(SHOTS)-resumo

_shots:
	@mkdir -p $(DIR)
	@n=$$(grep -c '<section data-transition' $(SITE)/$(PAGE).html); i=0; \
	while [ $$i -lt $$n ]; do \
	  $(CHROME) --headless=new --disable-gpu --hide-scrollbars --no-sandbox --window-size=1920,1080 \
	    --virtual-time-budget=6000 --screenshot=$(DIR)/$$(printf '%02d' $$i).png \
	    "file://$(CURDIR)/$(SITE)/$(PAGE).html#/$$i" >/dev/null 2>&1; i=$$((i+1)); done; \
	echo "$$n slides em $(DIR)/"

serve: build ## Serve o site em http://localhost:8080
	cd $(SITE) && python3 -m http.server 8080

status: ## git status
	@git status --short
