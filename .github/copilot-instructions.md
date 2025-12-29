# Copilot Instructions for this Workspace

These instructions help AI coding agents work productively in this repo.

## Overview
- Single-file app in [app.py](../app.py) orchestrates news aggregation via Selenium.
- Class `NewsAggregatorPro` fetches Google News links, resolves real article URLs, pulls summaries from `smry.ai`, cleans text, and renders an HTML report.
- Sample raw SMRY output lives in [noticias_bypass.txt](../noticias_bypass.txt) and informs text cleaning rules.

## Architecture & Flow
- `run(url)`: loads a Google News story page, scrolls to render links, filters up to 10 valid article links, and processes each.
- `get_real_url(google_link)`: opens the Google News redirect and waits until the final article URL is reached.
- `extract_smry(real_url)`: loads `https://smry.ai/<real_url>`, captures `h1`/title and `body` text, then applies `clean_text()`.
- `clean_text(raw_text)`: removes UI/marketing and short/noisy lines using `garbage_terms` and minimum length.
- `generate_html(filename)`: builds a styled single-page report from `articles_data` and writes to disk.

## Developer Workflow
- Install Python deps:
  ```bash
  pip install selenium webdriver-manager
  ```
- On Ubuntu/Codespaces, ensure a headless browser is available (Chrome/Chromium):
  ```bash
  sudo apt-get update
  sudo apt-get install -y chromium-browser || sudo apt-get install -y chromium
  # Optional: fonts for nicer rendering
  sudo apt-get install -y fonts-liberation
  ```
- Run locally:
  ```bash
  python app.py
  ```
- To target a different Google News story, edit `target_url` in [app.py](../app.py).

## Conventions & Patterns
- Headless Chrome is configured for Codespaces: `--headless`, `--no-sandbox`, `--disable-dev-shm-usage`, `--window-size=1920,1080`, custom user-agent.
- Logging is in pt‑BR with emojis; keep output user-friendly and actionable.
- Text cleaning is driven by `garbage_terms` and minimum length; expand the list using examples from [noticias_bypass.txt](../noticias_bypass.txt).
- Throughput: limits to 10 items; uses simple `sleep` and minimal `WebDriverWait`—prefer small, incremental timing tweaks over large refactors.

## Integration Points
- External sites: Google News and `smry.ai` (HTML body text extraction).
- Web automation: Selenium `webdriver.Chrome` with `webdriver_manager` automatically fetching the driver.
- If Chromium is installed instead of Chrome, set `Options.binary_location` to the Chromium binary path when needed.

## Extending Safely
- Increase coverage: raise the item limit or refine link filtering (see anchor `href` checks in `run`).
- Robustness: prefer `WebDriverWait` over fixed `sleep` for specific elements; keep headless-friendly flags.
- Output formats: add a JSON export alongside HTML by serializing `articles_data`.
- Styling: adjust CSS inside `generate_html()`; avoid external assets to keep output self-contained.

## Troubleshooting
- Driver failures: ensure Chrome/Chromium is installed; `webdriver_manager` downloads the driver, not the browser.
- Empty report: link filtering too strict or SMRY page structure changed—log `current_url`, title, and `body` length for diagnostics.
- Anti-bot issues: rotate/adjust user-agent, increase waits, or briefly disable `--headless` when debugging.

## Browser Setup Examples (Chromium)
- Detect and set Chromium binary automatically:
  ```python
  from shutil import which
  self.options.binary_location = which("chromium-browser") or which("chromium") or "/usr/bin/chromium"
  ```
- Toggle headless for debug:
  ```python
  self.options.add_argument("--headless=new")  # or remove to see UI
  self.options.add_argument("--user-data-dir=/tmp/chrome-profile")  # persist session to reduce blocks
  ```

## Link Filtering & Throughput
- In `run()`, links are accepted when `href` contains `/articles/` or `/read/` and domain inclui `google.com`. Para ampliar:
  ```python
  if h and "google.com" in h and any(p in h for p in ("/articles/", "/read/", "/topics/")):
      valid_links.add(h)
  ```
- Aumentar limite de itens com segurança:
  ```python
  link_list = list(valid_links)[:20]
  ```

## SMRY Extraction Waits (preferir WebDriverWait)
- Substituir `sleep` por esperas direcionadas quando possível:
  ```python
  from selenium.webdriver.support import expected_conditions as EC
  from selenium.webdriver.common.by import By
  WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
  title = self.driver.find_element(By.TAG_NAME, "h1").text
  ```
- Garantir corpo carregado antes da leitura:
  ```python
  WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
  raw_body = self.driver.find_element(By.TAG_NAME, "body").text
  ```

## Clean Text: Evolução guiada por amostras
- Use [noticias_bypass.txt](../noticias_bypass.txt) para ampliar `garbage_terms`:
  ```python
  garbage_terms += [
      "Go Pro", "Summary", "Share", "Copy page", "Toggle theme",
      "Smry Fast", "Smry Slow", "Wayback", "Jina.ai", "reader",
      "original", "iframe"
  ]
  ```

## JSON Export (exemplo rápido)
- Após processar `articles_data`, exporte JSON sem alterar o fluxo HTML:
  ```python
  import json
  with open("news_report.json", "w", encoding="utf-8") as jf:
      json.dump(self.articles_data, jf, ensure_ascii=False, indent=2)
  ```

## Abrir Relatório
- Em Linux/Codespaces, abra o HTML gerado com o navegador padrão:
  ```bash
  "$BROWSER" news_report.html
  ```

## Debug rápido
- Logar URLs e tempos:
  ```python
  import time
  t0 = time.time()
  self.driver.get(google_link)
  print(f"URL atual: {self.driver.current_url}")
  print(f"Latência de navegação: {time.time() - t0:.2f}s")
  ```
- Verificar título e fallback:
  ```python
  try:
      title = self.driver.find_element(By.TAG_NAME, "h1").text
  except:
      title = self.driver.title
  print(f"Título capturado: {title}")
  ```
- Medir tamanho do corpo e HTML:
  ```python
  raw_body = self.driver.find_element(By.TAG_NAME, "body").text
  print(f"Tamanho body: {len(raw_body)} | HTML: {len(self.driver.page_source)}")
  ```
- Screenshot para inspeção rápida (headless funciona):
  ```python
  self.driver.save_screenshot("/tmp/smry.png")
  ```
- Desativar headless temporariamente:
  ```python
  # Remova '--headless' nas opções ou use '--headless=new' para compatibilidade
  ```
