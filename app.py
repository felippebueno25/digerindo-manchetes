import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

class NewsAggregatorPro:
    def __init__(self):
        self.options = Options()
        
        # --- Configurações Otimizadas ---
        self.options.add_argument("--headless=new") 
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--disable-extensions")
        self.options.page_load_strategy = "eager" 

        self.options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        
        self.driver = None
        self.start_driver()
        self.articles_data = [] 

    def start_driver(self):
        """Inicia o navegador."""
        if self.driver:
            try: self.driver.quit()
            except: pass
        
        print("   🔧 Iniciando navegador...")
        try:
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()), 
                options=self.options
            )
            self.driver.set_page_load_timeout(25) 
        except Exception as e:
            print(f"   ❌ Erro fatal ao iniciar driver: {e}")
            raise

    def safe_get(self, url):
        try:
            self.driver.get(url)
            return True
        except TimeoutException:
            try: self.driver.execute_script("window.stop();")
            except: pass
            return True
        except WebDriverException as e:
            print(f"   ⚠️ Erro driver ({str(e)[:40]}...). Reiniciando...")
            self.start_driver()
            try:
                self.driver.get(url)
                return True
            except:
                return False
        except Exception:
            return False

    def clean_text(self, raw_text):
        if not raw_text: return []
        lines = raw_text.split('\n')
        cleaned = []
        garbage = ["Summarize", "Listen", "Share", "Created with smry", "Menu", "Search", "Assine", "Login", "Cookies", "Subscribe"]

        for line in lines:
            line = line.strip()
            if len(line) < 40: continue 
            if any(term.lower() in line.lower() for term in garbage): continue
            cleaned.append(line)
        return cleaned

    def process_article(self, real_url):
        content = None
        title = "Sem Título"
        
        # Tenta acesso direto
        if self.safe_get(real_url):
            try:
                try: title = self.driver.find_element(By.TAG_NAME, "h1").text
                except: title = self.driver.title
                
                # Pega todo texto visível
                raw_text = self.driver.find_element(By.TAG_NAME, "body").text
                
                # Verifica se parece paywall ou erro
                if len(raw_text) > 500 and "exclusivo para assinantes" not in raw_text.lower():
                    content = self.clean_text(raw_text)
                    print(f"      ✨ Sucesso Direto: {title[:30]}...")
            except: pass

        # Fallback Smry
        if not content:
            print("      🔒 Bloqueado/Falha. Tentando Smry...")
            smry_url = f"https://smry.ai/{real_url}"
            if self.safe_get(smry_url):
                try:
                    time.sleep(3)
                    raw_text = self.driver.find_element(By.TAG_NAME, "body").text
                    content = self.clean_text(raw_text)
                    if content:
                        print(f"      ✨ Sucesso Smry: {title[:30]}...")
                except: pass

        if content:
            return {"title": title, "url": real_url, "content": content, "source_domain": real_url.split('/')[2]}
        return None

    def get_real_url(self, google_link):
        if not self.safe_get(google_link): return None
        try:
            # Aumentei para 10s para dar tempo do JS rodar
            WebDriverWait(self.driver, 10).until(lambda d: "news.google.com" not in d.current_url)
            return self.driver.current_url
        except:
            # Se falhar, retorna a URL onde parou para debug
            return self.driver.current_url

    def run(self, url, progress_callback=None):
        def update(msg, pct):
            print(msg)
            if progress_callback: progress_callback(msg, pct)

        update(f"🌐 Iniciando: {url}", 0.0)
        self.safe_get(url)
        time.sleep(2)
        
        # Carregamento agressivo (Scroll)
        update("📜 Carregando lista completa...", 0.1)
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        for i in range(8): # Tenta scrollar 8 vezes
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height: break 
            last_height = new_height

        # Coleta Links
        links_elems = self.driver.find_elements(By.TAG_NAME, "a")
        unique_links = set()
        for l in links_elems:
            try:
                h = l.get_attribute("href")
                if h and ("/articles/" in h or "/read/" in h) and "google.com" in h:
                    unique_links.add(h)
            except: pass
        
        link_list = list(unique_links)
        total = len(link_list)
        update(f"✅ {total} links identificados.", 0.2)
        
        for i, link in enumerate(link_list):
            pct = 0.2 + (0.8 * (i / total))
            update(f"[{i+1}/{total}] Processando...", pct)

            # --- REMOVIDO O RESTART A CADA 5 ITENS ---
            # Isso mantém a sessão quente e evita Captchas/Consent Screens

            real_url = self.get_real_url(link)
            
            # Debug: Por que pulou?
            if not real_url:
                print("      ⚠️ Pulo: URL nula")
                continue
            if "news.google.com" in real_url or "google.com" in real_url:
                print(f"      ⚠️ Pulo: Redirecionamento falhou ({real_url[:40]}...)")
                continue

            data = self.process_article(real_url)
            if data: self.articles_data.append(data)

        self.driver.quit()
        update("✨ Concluído!", 1.0)
        return self.articles_data