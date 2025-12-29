# Diagnóstico de execução

Se você está recebendo `SessionNotCreatedException: Chrome instance exited`, normalmente significa que o navegador Chrome/Chromium não está instalado no container.

Soluções:

```bash
sudo apt-get update
sudo apt-get install -y chromium-browser || sudo apt-get install -y chromium
sudo apt-get install -y fonts-liberation
```

Após instalar, rode:

```bash
python app.py
```

Em casos de `HTTPConnectionPool(...): Read timed out`, o projeto já aplica:
- `page_load_strategy = "eager"`
- `set_page_load_timeout(30)`
- cancelamento do carregamento via `window.stop()` ao atingir timeout
- `WebDriverWait` para esperar elementos necessários em vez de `sleep` fixo
- reinício do driver em falhas duras
