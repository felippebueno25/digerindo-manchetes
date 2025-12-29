# News Aggregator Pro (Selenium)

Coleta links de histórias no Google News, resolve a URL real, obtém um resumo via `smry.ai`, limpa o texto e gera um relatório HTML.

## Pré-requisitos
- Python 3.9+
- Linux (Codespaces/Ubuntu) recomendado

## Instalação
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Navegador (Chromium/Chrome)
```bash
sudo apt-get update
sudo apt-get install -y chromium-browser || sudo apt-get install -y chromium
sudo apt-get install -y fonts-liberation
```

Opcional: definir `binary_location` para Chromium em [app.py](app.py):
```python
from shutil import which
self.options.binary_location = which("chromium-browser") or which("chromium") or "/usr/bin/chromium"
```

## Execução
```bash
python app.py
```

Para alterar o alvo do Google News, edite `target_url` em [app.py](app.py).

## Saídas
- HTML: `news_report.html`
- (Opcional) JSON: `news_report.json`

Abrir relatório no navegador padrão:
```bash
"$BROWSER" news_report.html
```

## Dicas de desenvolvimento
- Ajuste `garbage_terms` em `clean_text()` com base em [noticias_bypass.txt](noticias_bypass.txt).
- Prefira `WebDriverWait` para esperar `h1` e `body` ao invés de `sleep` longo.
- Logs estão em pt‑BR com emojis; mantenha mensagens curtas e úteis.
