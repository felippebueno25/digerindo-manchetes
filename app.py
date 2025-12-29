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
from shutil import which

class NewsAggregatorPro:
    def __init__(self):
        self.options = Options()
        
        # --- Configurações (Codespaces/Headless) ---
        # preferir headless new para Chrome/Chromium recentes
        self.options.add_argument("--headless=new") 
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-gpu")
        self.options.page_load_strategy = "eager"

        self.options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        print("🚀 Iniciando Motor de Extração...")
        try:
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()), 
                options=self.options
            )
        except Exception as e:
            msg = str(e)
            print("❌ Não foi possível iniciar o navegador.")
            print(f"   Erro: {msg[:200]}")
            print("   Dica: pode faltar dependências do Chromium. Instale:")
            print("   sudo apt-get install -y libnss3 libgconf-2-4 libx11-6 libx11-xcb1 libxcb1 libxss1 fonts-liberation")
            raise
        # Limita tempo de carregamento de páginas para evitar bloqueios longos
        self.driver.set_page_load_timeout(30)
        # dá folga para comandos mais pesados sem estourar o HTTPConnectionPool
        try:
            self.driver.command_executor.set_timeout(180)
        except Exception:
            pass

        self.articles_data = [] # Lista para guardar os objetos das notícias

    def restart_driver(self):
        try:
            self.driver.quit()
        except Exception:
            pass
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=self.options
        )
        try:
            self.driver.set_page_load_timeout(30)
        except Exception:
            pass
        try:
            self.driver.command_executor.set_timeout(180)
        except Exception:
            pass

    def safe_get(self, url, timeout=30):
        try:
            if timeout:
                try:
                    self.driver.set_page_load_timeout(timeout)
                except Exception:
                    pass
            self.driver.get(url)
            return True
        except TimeoutException:
            print("⏱️ Carregamento lento — interrompendo e seguindo.")
            try:
                self.driver.execute_script("window.stop();")
            except Exception:
                pass
            return True
        except WebDriverException as e:
            msg = str(e)
            if "HTTPConnectionPool" in msg or "Read timed out" in msg:
                print("🌐 Driver demorou a responder — cancelando carregamento e retomando.")
                try:
                    self.driver.execute_script("window.stop();")
                except Exception:
                    pass
                return True
            print(f"   ❌ Falha ao navegar: {e}")
            return False
        except Exception as e:
            print(f"   ❌ Erro inesperado ao navegar: {e}")
            return False

    def clean_text(self, raw_text):
        lines = raw_text.split('\n')
        cleaned_lines = []
        garbage_terms = ["Summarize this", "Listen to this", "Share this", "Created with smry", "Menu", "Search", "Paste article URL", "Try it", "@michael_chomsky"]

        for line in lines:
            line = line.strip()
            if not line: continue
            if any(term.lower() in line.lower() for term in garbage_terms): continue
            if len(line) < 4: continue
            cleaned_lines.append(line)
            
        return cleaned_lines # Retorna lista de parágrafos

    def get_real_url(self, google_link):
        try:
            print(f"   ↳ Resolvendo link...")
            if not self.safe_get(google_link, timeout=20):
                # tenta reiniciar o driver e prosseguir uma vez
                self.restart_driver()
                if not self.safe_get(google_link, timeout=20):
                    return None
            try:
                WebDriverWait(self.driver, 10).until(lambda d: "news.google.com" not in d.current_url)
            except Exception:
                pass
            return self.driver.current_url
        except Exception:
            return None

    def extract_smry(self, real_url):
        if not real_url or "google.com" in real_url: return None
        smry_url = f"https://smry.ai/{real_url}"
        print(f"   ⚡ Processando via Smry: {smry_url}")
        
        try:
            if not self.safe_get(smry_url, timeout=25):
                # reinicia e tenta uma vez mais
                self.restart_driver()
                if not self.safe_get(smry_url, timeout=25):
                    return None

            # Aguarda elementos essenciais em vez de dormir fixo
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            try:
                title = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "h1"))).text
            except Exception:
                title = self.driver.title

            raw_body = self.driver.find_element(By.TAG_NAME, "body").text
            paragraphs = self.clean_text(raw_body)
            
            return {
                "title": title,
                "url": real_url,
                "content": paragraphs,
                "source_domain": real_url.split('/')[2]
            }
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            return None

    def generate_html(self, filename="news_report.html"):
        """Gera um arquivo HTML bonito com CSS embutido"""
        if not self.articles_data:
            print("⚠️ Nenhuma notícia para gerar relatório.")
            return

        html_content = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Resumo de Notícias - Cobertura Completa</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f9; color: #333; line-height: 1.6; margin: 0; padding: 20px; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
                h1 {{ text-align: center; color: #2c3e50; margin-bottom: 40px; border-bottom: 2px solid #ddd; padding-bottom: 10px; }}
                .card {{ background: white; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 30px; overflow: hidden; transition: transform 0.2s; }}
                .card:hover {{ transform: translateY(-2px); }}
                .card-header {{ background-color: #2c3e50; color: white; padding: 15px 20px; }}
                .card-header h2 {{ margin: 0; font-size: 1.2rem; }}
                .meta {{ font-size: 0.8rem; color: #bdc3c7; margin-top: 5px; display: block; }}
                .card-body {{ padding: 20px; }}
                .card-body p {{ margin-bottom: 15px; text-align: justify; }}
                .btn {{ display: inline-block; background-color: #3498db; color: white; padding: 8px 15px; text-decoration: none; border-radius: 4px; font-size: 0.9rem; margin-top: 10px; }}
                .btn:hover {{ background-color: #2980b9; }}
                .footer {{ text-align: center; margin-top: 50px; font-size: 0.8rem; color: #777; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📰 Relatório de Cobertura Completa</h1>
        """

        for article in self.articles_data:
            paragraphs_html = "".join([f"<p>{p}</p>" for p in article['content']])
            html_content += f"""
                <div class="card">
                    <div class="card-header">
                        <h2>{article['title']}</h2>
                        <span class="meta">Fonte: {article['source_domain']}</span>
                    </div>
                    <div class="card-body">
                        {paragraphs_html}
                        <a href="{article['url']}" target="_blank" class="btn">Ler original 🔗</a>
                    </div>
                </div>
            """

        html_content += """
                <div class="footer">Gerado automaticamente pelo seu Bot de Notícias 🤖</div>
            </div>
        </body>
        </html>
        """

        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"\n✨ Relatório visual gerado com sucesso: {filename}")

    def run(self, url):
        print(f"🌐 Acessando Google News...")
        if not self.safe_get(url, timeout=25):
            self.restart_driver()
            if not self.safe_get(url, timeout=25):
                print("❌ Falha ao acessar Google News.")
                return

        time.sleep(2)
        
        for _ in range(3):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.0)

        links = self.driver.find_elements(By.TAG_NAME, "a")
        valid_links = set()
        
        for link in links:
            try:
                h = link.get_attribute("href")
                if h and ("/articles/" in h or "/read/" in h) and "google.com" in h:
                    valid_links.add(h)
            except: continue
            
        link_list = list(valid_links)[:10] # Limite de 10 notícias
        print(f"🔍 Processando {len(link_list)} notícias...")

        for i, link in enumerate(link_list):
            print(f"[{i+1}/{len(link_list)}] Baixando...")
            real_url = self.get_real_url(link)
            if real_url:
                data = self.extract_smry(real_url)
                if data: self.articles_data.append(data)

        self.driver.quit()
        self.generate_html()

if __name__ == "__main__":
    # Substitua pelo link desejado
    target_url = "https://news.google.com/stories/CAAqNggKIjBDQklTSGpvSmMzUnZjbmt0TXpZd1NoRUtEd2pzbTlHZ0VCRUlGS0RIZXllZlJDZ0FQAQ?hl=pt-BR&gl=BR&ceid=BR%3Apt-419"
    
    app = NewsAggregatorPro()
    app.run(target_url)