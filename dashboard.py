import streamlit as st
from dotenv import load_dotenv
import os
from google import genai
from app import NewsAggregatorPro
import database as db

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

st.set_page_config(page_title="News Intel AI", page_icon="🧿", layout="wide")

st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { font-size: 14px; font-weight: 600; padding: 10px; }
    
    .news-container {
        border: 1px solid #444;
        border-radius: 8px;
        background-color: #262730; 
        margin-bottom: 16px;
        overflow: hidden;
        padding: 10px;
    }
    .news-container:hover { border-color: #3b82f6; }
    
    /* Botões */
    .stButton button {
        text-align: left;
        border: none;
        background: transparent;
        color: #ffffff !important;
        padding: 0;
        font-weight: 600;
        line-height: 1.4;
        margin-top: 5px;
    }
    .stButton button:hover { color: #60a5fa !important; text-decoration: underline; background: transparent; }
    
    .cluster-tag { font-size: 10px; background: #1e3a8a; color: #bfdbfe; padding: 2px 6px; border-radius: 4px; font-weight: bold; }
    .ai-box { background: #1e293b; padding: 20px; border-radius: 8px; border-left: 4px solid #3b82f6; color: white; }
</style>
""", unsafe_allow_html=True)

IMG_PLACEHOLDER = "https://fonts.gstatic.com/s/i/productlogos/news/v6/web-96dp/logo_strip.png"
BACKUP_BR = "https://news.google.com/topics/CAAqJggKIiBDQkFTRWvfQUwyXzhTblF5Y0c1bEpXNnRNU0FBUW9BQVAB?hl=pt-BR&gl=BR&ceid=BR%3Apt-419"

def generate_report(articles, api_key):
    if not articles: return None
    client = genai.Client(api_key=api_key)
    txt = "".join([f"## {a['source_domain']}\n{a['title']}\n{a['content'][:2500]}\n" for a in articles])
    prompt = f"Analista de Inteligência.\nGere dossiê executivo:\n\n{txt}"
    try: return client.models.generate_content(model='gemini-2.5-flash-lite', contents=prompt).text
    except: return "Erro na geração."

st.title("🧿 News Intel AI")
if not API_KEY: st.error("Falta API Key"); st.stop()

if 'menu_data' not in st.session_state:
    with st.spinner("Conectando..."):
        agg = NewsAggregatorPro()
        menu = agg.get_menu_topics()
        if not menu:
            menu = [{"title": "Brasil", "url": BACKUP_BR}, {"title": "Mundo", "url": BACKUP_BR}]
        st.session_state['menu_data'] = menu

menu = st.session_state['menu_data']
tabs = st.tabs([m['title'] for m in menu])

for i, tab in enumerate(tabs):
    with tab:
        topic = menu[i]
        t_key = f"news_{topic['title']}"
        
        # Auto-Load
        if i == 0 and t_key not in st.session_state:
            with st.spinner(f"Baixando {topic['title']}..."):
                agg = NewsAggregatorPro()
                st.session_state[t_key] = agg.get_headlines_from_topic(topic['url'])
                st.rerun()

        if t_key not in st.session_state:
            if st.button(f"📥 Carregar {topic['title']}", key=f"load_{i}"):
                with st.spinner("Buscando..."):
                    agg = NewsAggregatorPro()
                    st.session_state[t_key] = agg.get_headlines_from_topic(topic['url'])
                    st.rerun()
        
        elif st.session_state[t_key]:
            news = st.session_state[t_key]
            
            if st.button("🔄 Atualizar", key=f"re_{i}"):
                del st.session_state[t_key]
                st.rerun()
            
            st.write("")
            cols = st.columns(4)
            for j, item in enumerate(news):
                with cols[j % 4]:
                    with st.container():
                        img_url = item.get('image')
                        if not img_url: img_url = IMG_PLACEHOLDER
                        
                        try:
                            # CORREÇÃO: width="stretch" (Obrigatório no Streamlit novo)
                            st.image(img_url, width="stretch")
                        except:
                            st.image(IMG_PLACEHOLDER, width="stretch")

                        if item.get('is_cluster'):
                            st.markdown('<span class="cluster-tag">⚡ Cobertura</span>', unsafe_allow_html=True)
                        
                        if st.button(item['title'], key=f"read_{i}_{j}"):
                            st.session_state['reading_item'] = item
                            st.session_state['view'] = 'reader'
                            st.rerun()

if st.session_state.get('view') == 'reader':
    item = st.session_state['reading_item']
    with st.sidebar:
        st.header("🕵️ Dossiê")
        st.info(f"{item['title']}")
        if st.button("❌ Fechar", type="primary"):
            st.session_state['view'] = None
            st.rerun()
        
        st.divider()
        status = st.status("Processando...", expanded=True)
        ckey = f"rep_{item['url']}"
        
        if ckey not in st.session_state:
            agg = NewsAggregatorPro()
            status.write("Baixando fontes...")
            content = agg.get_story_content(item['url'])
            if content:
                status.write("Gerando IA...")
                rep = generate_report(content, API_KEY)
                st.session_state[ckey] = rep
                
                # Bloco seguro de salvamento
                try:
                    # Garantimos que a 'url' existe agora no app.py
                    db.save_full_report(item['url'], item['title'], rep, content)
                except Exception as e:
                    print(f"⚠️ Erro ao salvar no DB (mas vou mostrar o relatório): {e}")
                
                status.update(label="Pronto!", state="complete")
            else:
                status.update(label="Erro", state="error")
                st.error("Falha ao ler fontes.")
    
    if ckey in st.session_state:
        st.markdown(f'<div class="ai-box">{st.session_state[ckey]}</div>', unsafe_allow_html=True)