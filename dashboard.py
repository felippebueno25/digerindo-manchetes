import streamlit as st
from google import genai
from app import NewsAggregatorPro
import os
import json
from datetime import datetime
import glob

# --- Configuração da Página ---
st.set_page_config(
    page_title="News Intel AI (Pro)",
    page_icon="⚡",
    layout="wide"
)

# --- CSS (Visual Profissional) ---
st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    
    /* Card de Notícia */
    .news-card {
        background-color: white; padding: 15px; border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #e5e7eb;
        height: 100%; display: flex; flex-direction: column; color: #000;
    }
    .source-tag { font-size: 0.75rem; font-weight: 800; color: #4b5563; text-transform: uppercase; margin-bottom: 5px; }
    .card-title { font-size: 1rem; font-weight: 700; color: #111; margin-bottom: 8px; line-height: 1.3; }
    .card-preview { font-size: 0.85em; color: #374151; flex-grow: 1; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; margin-bottom: 10px;}
    .read-btn { font-size: 0.8rem; color: #2563eb; text-decoration: none; font-weight: 600; margin-top: auto; }
    
    /* Box do Relatório */
    .ai-box { 
        background-color: #f8fafc; border: 1px solid #cbd5e1; 
        border-radius: 12px; padding: 30px; margin-bottom: 30px; 
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .ai-box h1, .ai-box h2, .ai-box h3 { color: #0f172a !important; font-weight: 700; margin-top: 20px; }
    .ai-box p, .ai-box li { color: #334155 !important; line-height: 1.6; font-size: 1.05rem; }
    .ai-box strong { color: #000 !important; }
</style>
""", unsafe_allow_html=True)

# --- Sistema de Arquivos (Persistência) ---
REPORTS_DIR = "saved_reports"
if not os.path.exists(REPORTS_DIR):
    os.makedirs(REPORTS_DIR)

def save_report_to_disk(topic_url, report_text, articles):
    """Salva o resultado em JSON para histórico."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    # Tenta extrair um nome amigável da URL ou usa Timestamp
    try:
        topic_name = topic_url.split("topics/")[1].split("?")[0][:15]
    except:
        topic_name = "topic"
        
    filename = f"{timestamp}_{topic_name}.json"
    filepath = os.path.join(REPORTS_DIR, filename)
    
    data = {
        "timestamp": timestamp,
        "url": topic_url,
        "report": report_text,
        "articles_count": len(articles),
        "articles": articles  # Salvamos também as fontes para referência futura
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return filename

def load_report_from_disk(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

# --- Inteligência (Gemini 2.5 Flash Lite) ---
def generate_intel_report(articles, api_key, status_callback):
    client = genai.Client(api_key=api_key)
    
    status_callback(f"⚡ Gemini 2.5 lendo {len(articles)} fontes...", 0.2)
    
    full_context = ""
    for i, art in enumerate(articles):
        clean_content = " ".join(art['content']).replace("\n", " ")
        full_context += f"## FONTE {i+1} ({art['source_domain']}):\nTITULO: {art['title']}\nTEXTO: {clean_content}\n\n---\n\n"

    prompt = f"""
    Você é o Chefe de Inteligência de Mídia.
    Analise a cobertura completa ({len(articles)} matérias).
    
    ESTRUTURA DO RELATÓRIO (Markdown):
    # Relatório de Inteligência
    ## 🎯 O Fato Central
    (Resumo preciso).
    ## ⚔️ Campo de Batalha das Narrativas
    (Narrativas Dominantes vs Críticas).
    ## 📊 Dados Concretos & Contradições
    (Valores, datas, mortos. Destaque divergências).
    ## 🔍 Blindspots
    (Detalhes únicos).
    
    MATÉRIAS:
    {full_context}
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash-lite',
        contents=prompt
    )
    return response.text

# --- Interface Principal ---

# 1. Barra Lateral (Histórico)
with st.sidebar:
    st.header("🗄️ Histórico")
    
    # Lista arquivos JSON na pasta
    files = sorted(glob.glob(os.path.join(REPORTS_DIR, "*.json")), reverse=True)
    
    selected_file = None
    if files:
        file_options = {f: f.split("/")[-1].replace(".json", "") for f in files}
        selected_file = st.selectbox(
            "Selecione um relatório anterior:", 
            options=files, 
            format_func=lambda x: file_options[x]
        )
        if st.button("Carregar Histórico"):
            st.session_state['loaded_report'] = load_report_from_disk(selected_file)
            st.rerun()
    else:
        st.info("Nenhum relatório salvo ainda.")

# 2. Área Central
st.title("⚡ News Intel AI")

# Tenta pegar a chave do ambiente
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    st.error("❌ ERRO CRÍTICO: `GEMINI_API_KEY` não encontrada nas variáveis de ambiente.")
    st.stop()

# Se carregou um histórico, mostra ele. Se não, mostra a ferramenta de nova análise.
if 'loaded_report' in st.session_state:
    data = st.session_state['loaded_report']
    st.info(f"📂 Visualizando relatório salvo em: {data['timestamp']}")
    if st.button("⬅️ Voltar para Nova Análise"):
        del st.session_state['loaded_report']
        st.rerun()
    
    st.markdown(f'<div class="ai-box">{data["report"]}</div>', unsafe_allow_html=True)
    st.divider()
    st.subheader(f"📚 Fontes Originais ({data['articles_count']})")
    cols = st.columns(3)
    for i, row in enumerate(data['articles']):
        with cols[i%3]:
            st.markdown(f"""<div class="news-card"><div class="source-tag">{row['source_domain']}</div><div class="card-title">{row['title']}</div><a href="{row['url']}" target="_blank" class="read-btn">Ler original 🔗</a></div>""", unsafe_allow_html=True)

else:
    # Modo Nova Análise
    url_input = st.text_input("URL Google News (Cobertura Completa):", placeholder="https://news.google.com/topics/...")
    
    # Hardcoded para extração máxima (100 itens deve cobrir tudo)
    run_btn = st.button("Iniciar Análise Completa 🚀", type="primary")

    if run_btn and url_input:
        status_box = st.status("🚀 Iniciando motor de inteligência...", expanded=True)
        p_bar = status_box.progress(0)
        
        def update_ui(msg, pct):
            p_bar.progress(min(max(pct, 0.0), 1.0))
            status_box.write(f"**{msg}**")

        try:
            # 1. Scraper (Sempre MAX)
            agg = NewsAggregatorPro()
            articles = agg.run(url_input, progress_callback=update_ui, max_items=150) # Hardcoded MAX
            
            if articles:
                # 2. IA
                update_ui(f"✅ {len(articles)} extraídos. Gerando Inteligência...", 0.1)
                report = generate_intel_report(articles, API_KEY, update_ui)
                
                # 3. Salvar Automaticamente
                update_ui("💾 Salvando no histórico...", 0.9)
                filename = save_report_to_disk(url_input, report, articles)
                
                status_box.update(label="✅ Concluído e Salvo!", state="complete", expanded=False)
                
                # Exibe Resultado
                st.success(f"Relatório salvo em: `{filename}`")
                st.subheader("📄 Relatório de Inteligência")
                st.markdown(f'<div class="ai-box">{report}</div>', unsafe_allow_html=True)
                
                # Botão de Download TXT
                st.download_button("📥 Baixar TXT", report, file_name="relatorio.txt")
                
                # Grid de Fontes
                st.divider()
                st.subheader(f"📚 Fontes Processadas ({len(articles)})")
                cols = st.columns(3)
                for i, row in enumerate(articles):
                    with cols[i%3]:
                         st.markdown(f"""<div class="news-card"><div class="source-tag">{row['source_domain']}</div><div class="card-title">{row['title']}</div><a href="{row['url']}" target="_blank" class="read-btn">Ler original 🔗</a></div>""", unsafe_allow_html=True)
            else:
                status_box.update(label="❌ Nenhuma notícia encontrada", state="error")
                
        except Exception as e:
            st.error(f"Erro: {e}")