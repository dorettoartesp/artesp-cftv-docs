# artesp-cftv-docs

Documentação pública do CFTV da ARTESP: o roteiro da apresentação para a gestão de TI (`APRESENTACAO.md`) e o
deck de slides publicado no GitHub Pages com [reveal.js](https://revealjs.com/) vendorizado, sem npm.

**Site:** `https://dorettoartesp.github.io/artesp-cftv-docs/`

| Pasta | O que é |
|---|---|
| `APRESENTACAO.md` | Roteiro completo, com os diagramas Mermaid que também alimentam os slides. |
| `deck/` | Fonte dos slides: um HTML por slide em `slides/<id>.html`; `deck.json` dá a ordem. |
| `site/` | O que o Pages serve: `template.html`, `css/artesp.css`, `img/` (logos e diagramas SVG gerados), `vendor/reveal/`. `index.html` é gerado e não versionado. |
| `tools/` | `build-site.py` (deck → `site/index.html`), `render-diagrams.py` (roteiro → `site/img/diag-*.svg`) e `check-diagrams.py` (guarda). |
| `tests/` | `python3 -m unittest`. |

## Fluxo de trabalho

```bash
make build      # deck/ -> site/index.html
make check      # testes + build + diagramas em dia + guarda de texto público
make diagrams   # APRESENTACAO.md -> site/img/diag-*.svg (requer google-chrome)
make shots      # um PNG por slide em output/shots/ (requer google-chrome)
make serve      # http://localhost:8080
```

Para alterar um slide, edite `deck/slides/<id>.html` e rode `make check`. Para alterar um diagrama, edite o bloco
Mermaid no `APRESENTACAO.md` (a linha `<!-- diagrama: nome -->` acima dele dá o nome do arquivo) e rode
`make diagrams`; os SVGs são versionados.

## Publicação

Todo push em `main` dispara o workflow `pages.yml`, que roda os testes, gera `site/index.html` e publica `site/`
no GitHub Pages. Este repositório é público: não traga para cá especificações, planos, nomes de pessoas nem
configuração interna.
