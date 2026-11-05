# artesp-cftv-docs

Documentação pública do CFTV da ARTESP: os roteiros da apresentação para a gestão de TI (`APRESENTACAO.md`, 35 a 40
minutos, e `RESUMO.md`, 15 minutos) e os dois decks de slides publicados no GitHub Pages com
[reveal.js](https://revealjs.com/) vendorizado, sem npm.

**Site:** `https://dorettoartesp.github.io/artesp-cftv-docs/` (completa) e `.../resumo.html` (resumida)

| Pasta | O que é |
|---|---|
| `APRESENTACAO.md` | Roteiro completo, com os diagramas Mermaid que também alimentam os slides. |
| `RESUMO.md` | Roteiro resumido de 15 minutos; reutiliza dois diagramas Mermaid do completo (mesmo nome, mesmo código) e dois SVG próprios. |
| `deck/`, `deck-resumo/` | Fonte dos slides de cada versão: um HTML por slide em `slides/<id>.html`; `deck.json` dá a ordem. |
| `site/` | O que o Pages serve: `template.html`, `css/artesp.css`, `img/` (logos, diagramas Mermaid gerados `diag-*.svg` e diagramas autorais `arq-*.svg`), `vendor/reveal/`. `index.html` e `resumo.html` são gerados e não versionados. |
| `tools/` | `build-site.py` (deck → `site/index.html`; `x-groups` transforma um mapa mental do roteiro em quadros), `render-diagrams.py` (roteiro → `site/img/diag-*.svg`), `check-diagrams.py` e `check-public.py` (guardas). |
| `tests/` | `python3 -m unittest`. |

## Fluxo de trabalho

```bash
make build      # deck/ -> site/index.html; deck-resumo/ -> site/resumo.html
make check      # testes + build + diagramas em dia + guarda de texto público
make diagrams   # APRESENTACAO.md e RESUMO.md -> site/img/diag-*.svg (requer google-chrome)
make shots      # um PNG por slide em output/shots/ e output/shots-resumo/ (requer google-chrome)
make serve      # http://localhost:8080
```

Para alterar um slide, edite `deck/slides/<id>.html` ou `deck-resumo/slides/<id>.html` e rode `make check`. Para alterar um diagrama, edite o bloco
Mermaid no `APRESENTACAO.md` (a linha `<!-- diagrama: nome -->` acima dele dá o nome do arquivo) e rode
`make diagrams`; os SVGs são versionados.

## Publicação

Todo push em `main` dispara o workflow `pages.yml`, que roda os testes, gera `site/index.html` e `site/resumo.html` e publica `site/`
no GitHub Pages. Este repositório é público: não traga para cá especificações, planos, nomes de pessoas nem
configuração interna. A guarda `tools/check-public.py` bloqueia endereços privados, URLs RTSP com credencial e
atribuições de senha ou token; termos confidenciais (nomes de servidores, domínios internos) ficam fora do
repositório, no arquivo ignorado `forbidden.local` (um por linha) e, no CI, no segredo `FORBIDDEN_EXTRA`.
