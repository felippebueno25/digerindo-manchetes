## Copilot Instructions for this Workspace

Concise guidance so agents can work productively here.

### Purpose and Flow
- Single entrypoint [app.py](../app.py) with class `NewsAggregatorPro`; fetches Google News story links, resolves the real article URL, summarizes via `smry.ai`, cleans text, and renders an HTML report.
- Pipeline: `run()` scrolls and captures up to 10 Google redirects → `get_real_url()` waits until the redirect leaves `news.google.com` → `extract_smry()` opens `https://smry.ai/<real_url>`, grabs `h1`/`body`, runs `clean_text()` → `generate_html()` writes `news_report.html`.

### Runtime Expectations
- Depends on Selenium + webdriver-manager (see [requirements.txt](../requirements.txt)); Chrome/Chromium must be installed and headless-friendly.
- Browser flags already set: `--headless=new`, `--no-sandbox`, `--disable-dev-shm-usage`, `--disable-gpu`, custom UA, `page_load_strategy="eager"`; keep them unless debugging.
- `safe_get()` wraps navigation with timeouts and `window.stop()` on slow loads; `restart_driver()` reinstantiates Chrome after hard failures.

### Data and Cleaning
- Text cleaning lives in `clean_text()`: drops empty/short lines and UI junk listed in `garbage_terms`; extend using the raw SMRY sample [noticias_bypass.txt](../noticias_bypass.txt).
- Link filtering in `run()` only accepts anchors containing `/articles/` or `/read/` on `google.com`; cap is 10 items—raise the slice to broaden coverage.

### Outputs and Styling
- HTML report is assembled inline in `generate_html()` with simple cards, meta text, and “Ler original” CTA; tweak CSS there. Default output path: `news_report.html` in repo root.
- JSON export is not built-in but easy: serialize `articles_data` after processing if needed.

### Developer Workflows
- Fast run (assumes deps installed): `python app.py`.
- Install + run helpers: [run.sh](../run.sh) installs Chromium if missing and launches the app; [install_and_run.sh](../install_and_run.sh) installs system libs then runs; [run_with_install.py](../run_with_install.py) performs env diagnostics, attempts Chromium install, installs critical libs, then executes the app; [debug_chromium.py](../debug_chromium.py) checks binary presence/versions/libs and finally runs the app.
- Changing the target story: edit `target_url` near the bottom of [app.py](../app.py).

### Troubleshooting Patterns
- Chrome missing: install `chromium-browser` or `chromium` plus libs (`libnss3`, `libgconf-2-4`, `libx11-*`, `libxss1`, `fonts-liberation`, etc.); scripts above automate this.
- Empty or short summaries: confirm `get_real_url()` leaves Google; log `current_url`, title, and body length; adjust link filtering if Google page layout changes.
- Anti-bot or slow loads: increase `WebDriverWait` durations in `extract_smry()`, temporarily remove `--headless`, or set `options.binary_location` to the detected Chromium path (`which("chromium-browser") or which("chromium")`).
