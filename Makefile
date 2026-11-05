.DEFAULT_GOAL := help
.PHONY: help build check diagrams shots serve status

CHROME ?= google-chrome
SITE   := site
SHOTS  := output/shots

# Text that must never go public: private addresses, RTSP URLs with credentials, keys, passwords, edge servers.
FORBIDDEN := (\b10\.[0-9]+\.[0-9]+\.[0-9]+\b|\b192\.168\.[0-9]+\.[0-9]+\b|\b172\.(1[6-9]|2[0-9]|3[01])\.[0-9]+\.[0-9]+\b|rtsp://[^[:space:]"]*@|cftvpub_|token[=:]|senha[=:]|password[=:]|mits-autoban|\.artesp\.local)

help: ## Lista os comandos
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-9s\033[0m %s\n", $$1, $$2}'

build: ## Gera site/index.html a partir de deck/
	python3 tools/build-site.py deck $(SITE)/index.html

diagrams: ## Renderiza os diagramas do APRESENTACAO.md em site/img/diag-*.svg (requer google-chrome)
	python3 tools/render-diagrams.py APRESENTACAO.md $(SITE)/img --chrome $(CHROME)

check: build ## Testes, build, diagramas em dia e guarda de texto público
	@python3 -m unittest
	@python3 tools/check-diagrams.py APRESENTACAO.md $(SITE)/img
	@! grep -E '$(FORBIDDEN)' $(SITE)/index.html APRESENTACAO.md \
	  || { echo "texto proibido em site/index.html ou APRESENTACAO.md"; exit 1; }
	@echo "ok"

shots: build ## Um PNG por slide em output/shots/ para conferência (requer google-chrome)
	@mkdir -p $(SHOTS)
	@n=$$(grep -c '<section data-transition' $(SITE)/index.html); i=0; \
	while [ $$i -lt $$n ]; do \
	  $(CHROME) --headless=new --disable-gpu --hide-scrollbars --no-sandbox --window-size=1920,1080 \
	    --virtual-time-budget=6000 --screenshot=$(SHOTS)/$$(printf '%02d' $$i).png \
	    "file://$(CURDIR)/$(SITE)/index.html#/$$i" >/dev/null 2>&1; i=$$((i+1)); done; \
	echo "$$n slides em $(SHOTS)/"

serve: build ## Serve o site em http://localhost:8080
	cd $(SITE) && python3 -m http.server 8080

status: ## git status
	@git status --short
