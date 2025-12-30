import asyncio
import random
from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import sys

# Fix para Linux/Codespaces
if sys.platform.startswith("linux"):
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())

class NewsAggregatorPro:
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        ]
        self.base_url = "https://news.google.com"

    def _get_headers(self):
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://news.google.com/"
        }

    def _clean_image_url(self, url):
        if not url: return None
        if "googleusercontent.com" in url: return url
        if url.startswith("data:image"): return url
        if "/api/attachments/" in url: return None
        if "favicon" in url: return None
        if not url.startswith("http"): return None
        return url

    # --- 1. MENU ---
    async def _scan_menu(self, crawler):
        print("   🧭 Mapeando Menu...")
        url = "https://news.google.com/?hl=pt-BR&gl=BR&ceid=BR%3Apt-419"
        try:
            result = await crawler.arun(url=url, magic=True, bypass_cache=True, headers=self._get_headers())
            if not result.success: return []
            
            soup = BeautifulSoup(result.html, 'html.parser')
            topics = []
            seen = set()
            priority = ["Brasil", "Mundo", "Local", "Negócios", "Tecnologia", "Entretenimento", "Esportes", "Saúde"]

            for a in soup.find_all('a', href=True):
                href = a['href']
                txt = a.get_text(strip=True)
                if "./topics/" in href and len(txt) > 2 and len(txt) < 20:
                    if any(p.lower() in txt.lower() for p in priority):
                        full = href.replace(".", self.base_url, 1)
                        if full not in seen:
                            topics.append({"title": txt, "url": full})
                            seen.add(full)
            
            topics.sort(key=lambda x: next((i for i, p in enumerate(priority) if p.lower() in x['title'].lower()), 99))
            return topics
        except: return []

    # --- 2. MANCHETES (SEM <ARTICLE>) ---
    async def _scan_headlines(self, crawler, topic_url):
        print(f"   📂 Lendo Tópico: {topic_url}")
        js_scroll = "window.scrollBy(0, 1000); await new Promise(r => setTimeout(r, 400)); window.scrollBy(0, 1000);"
        try:
            result = await crawler.arun(url=topic_url, js_code=js_scroll, magic=True, headers=self._get_headers())
            if not result.success: return []

            soup = BeautifulSoup(result.html, 'html.parser')
            headlines = []
            seen = set()

            # CAÇADOR DE LINKS BRUTO (Foda-se a tag article)
            all_links = soup.find_all('a', href=True)
            
            for a in all_links:
                href = a['href']
                
                # Aceita stories (cobertura) E articles (manchetes diretas)
                is_story = "./stories/" in href
                is_article = "./articles/" in href
                
                if not (is_story or is_article): continue
                
                full_link = href.replace(".", self.base_url, 1)
                if full_link in seen: continue

                # Tenta pegar título do link
                title = a.get_text(strip=True)
                
                # Se título for ruim ("Veja mais"), sobe na árvore pra achar o pai
                card_block = None
                parent = a.parent
                # Sobe até achar um container que tenha imagem ou texto grande
                for _ in range(4):
                    if parent:
                        if parent.find('img') or parent.find('h3') or parent.find('h4'):
                            card_block = parent
                            break
                        parent = parent.parent
                
                if card_block:
                    # Tenta achar H3/H4
                    h = card_block.find(['h3', 'h4'])
                    if h: 
                        title = h.get_text(strip=True)
                    elif len(title) < 10:
                        # Pega o maior link de texto dentro do bloco
                        sub_links = card_block.find_all('a')
                        valid_texts = [l.get_text(strip=True) for l in sub_links]
                        if valid_texts: title = max(valid_texts, key=len)

                if len(title) < 10: continue

                # Imagem
                img_src = None
                if card_block:
                    img = card_block.find('img')
                    if img:
                        raw = img.get('src') or img.get('data-src') or img.get('srcset', '').split(' ')[0]
                        img_src = self._clean_image_url(raw)

                headlines.append({
                    "title": title,
                    "url": full_link,
                    "image": img_src,
                    "is_cluster": is_story
                })
                seen.add(full_link)

            print(f"   ✅ Itens: {len(headlines)}")
            return headlines[:30]
        except Exception as e:
            print(f"Erro scan: {e}")
            return []

    # --- 3. CONTEÚDO (COM RETORNO DE URL) ---
    async def _deep_dive(self, crawler, url, max_items):
        try:
            print(f"   🕵️ Mergulhando: {url}")
            result = await crawler.arun(url=url, magic=True, headers=self._get_headers())
            
            soup = BeautifulSoup(result.html, 'html.parser')
            links = set()
            
            # Pega links internos da página (seja story ou article redirecionado)
            for a in soup.find_all('a', href=True):
                if "./articles/" in a['href'] or "/read/" in a['href']:
                    full = a['href'].replace(".", self.base_url, 1) if a['href'].startswith(".") else a['href']
                    links.add(full)
            
            final_links = list(links)[:max_items]
            if not final_links: final_links = [url] # Se não achou filhos, tenta o próprio pai

            async def fetch(l):
                try:
                    await asyncio.sleep(random.uniform(0.1, 0.5))
                    res = await crawler.arun(url=l, magic=True, word_count_threshold=200)
                    
                    if res.success and res.markdown:
                        dom = urlparse(res.url).netloc.replace("www.", "")
                        return {
                            "title": res.media.get("title", "Sem Título"), 
                            "source_domain": dom, 
                            "content": res.markdown,
                            "url": res.url # <--- CORREÇÃO DO KEYERROR
                        }
                except: pass
                return None

            tasks = [fetch(l) for l in final_links]
            results = await asyncio.gather(*tasks)
            valid = [r for r in results if r is not None and len(r['content']) > 200]
            return valid
        except Exception as e: 
            print(f"Erro deep dive: {e}")
            return []

    # --- WRAPPERS ---
    def _run_sync(self, coro):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        crawler = AsyncWebCrawler(verbose=False)
        try:
            return loop.run_until_complete(coro(crawler))
        finally:
            try: loop.run_until_complete(crawler.crawler_strategy.close()) 
            except: pass
            loop.close()

    def get_menu_topics(self): return self._run_sync(self._scan_menu)
    def get_headlines_from_topic(self, url): return self._run_sync(lambda c: self._scan_headlines(c, url))
    def get_story_content(self, url): return self._run_sync(lambda c: self._deep_dive(c, url, 10))