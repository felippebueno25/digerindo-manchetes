import streamlit as st
from google import genai # Usando a biblioteca nova que suporta o 2.5
from app import NewsAggregatorPro
import os

# --- Configuração ---
st.set_page_config(
    page_title="News Intel AI (Powered by Gemini 2.5)",
    page_icon="⚡",
    layout="wide"
)

# --- CSS (Texto Preto e Visual Limpo) ---
st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
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
    /* Força texto escuro no relatório */
    .ai-box h1, .ai-box h2, .ai-box h3 { color: #0f172a !important; font-weight: 700; margin-top: 20px; }
    .ai-box p, .ai-box li { color: #334155 !important; line-height: 1.6; font-size: 1.05rem; }
    .ai-box strong { color: #000 !important; }
</style>
""", unsafe_allow_html=True)

# --- Inteligência (Gemini 2.5 Flash Lite) ---
def generate_intel_report(articles, api_key, status_callback):
    if not api_key: return "⚠️ API Key ausente."
    
    try:
        client = genai.Client(api_key=api_key)
        
        # 1. Preparação do Contexto (Single Shot Massivo)
        status_callback(f"⚡ Gemini 2.5 lendo {len(articles)} fontes simultaneamente...", 0.2)
        
        full_context = ""
        total_chars = 0
        
        for i, art in enumerate(articles):
            # Limpeza leve: remove quebras de linha para compactar
            clean_content = " ".join(art['content']).replace("\n", " ")
            full_context += f"## FONTE {i+1} ({art['source_domain']}):\nTITULO: {art['title']}\nTEXTO: {clean_content}\n\n---\n\n"
            total_chars += len(clean_content)

        # 2. O Prompt de Analista Sênior
        prompt = f"""
        Você é o Chefe de Inteligência de Mídia.
        Você recebeu a cobertura completa ({len(articles)} matérias) sobre um tópico crítico.
        
        SUA MISSÃO:
        Escreva um RELATÓRIO EXECUTIVO coeso, direto e rico em detalhes.
        Não use frases genéricas como "existem opiniões diferentes". Diga QUAIS são e QUEM as defende.
        
        ESTRUTURA DO RELATÓRIO (Markdown):
        # Relatório de Inteligência
        
        ## 🎯 O Fato Central
        (Resumo jornalístico preciso do que aconteceu, sem lero-lero).
        
        ## ⚔️ Campo de Batalha das Narrativas
        * **Narrativa Dominante:** (O que a maioria diz)
        * **Narrativa Crítica/Oposição:** (Quem discorda e por quê)
        * **Nuances Internacionais/Mercado:** (Se houver)
        
        ## 📊 Dados Concretos & Contradições
        (Liste valores, datas, mortos, porcentagens. Se a Fonte A diz 10 e a B diz 100, DESTAQUE ISSO).
        
        ## 🔍 Blindspots (Ouro em Pó)
        (Ache aquele detalhe único que só apareceu em 1 ou 2 matérias e ninguém mais viu).
        
        MATÉRIAS PARA ANÁLISE:
        {full_context}
        """

        status_callback(f"🧠 Processando {total_chars//4} tokens com Gemini 2.5 Flash Lite...", 0.4)

        # 3. Chamada ao Modelo Vencedor
        response = client.models.generate_content(
            model='gemini-2.5-flash-lite', # <--- A ESTRELA DO SHOW
            contents=prompt
        )
        return response.text

    except Exception as e:
        return f"❌ Erro na IA: {e}"

# --- Sidebar & Setup ---
with st.sidebar:
    st.header("⚙️ Configuração")
    api_key = st.text_input("API Key", type="password", value=os.getenv("GEMINI_API_KEY", ""))
    
    st.divider()
    
    st.subheader("📡 Radar")
    # Agora podemos ser ousados no padrão
    max_news = st.slider("Alcance da Leitura", 10, 60, 40, help="2.5 Lite aguenta o tranco!")

# --- Main Interface ---
st.title("⚡ News Intel AI")
st.caption("Powered by Gemini 2.5 Flash Lite")

url_input = st.text_input("Cole o link do Google News (Cobertura Completa):", placeholder="https://news.google.com/topics/...")
run_btn = st.button(f"Iniciar Análise de {max_news} Fontes 🚀", type="primary")

if run_btn and url_input:
    status_box = st.status("🚀 Iniciando sistemas...", expanded=True)
    p_bar = status_box.progress(0)
    
    def update_ui(msg, pct):
        p_bar.progress(min(max(pct, 0.0), 1.0))
        status_box.write(f"**{msg}**")

    # 1. Scraper (O seu app.py robusto faz o trabalho sujo aqui)
    agg = NewsAggregatorPro()
    articles = agg.run(url_input, progress_callback=update_ui, max_items=max_news)
    
    if articles:
        # 2. IA (O momento da verdade)
        update_ui(f"✅ {len(articles)} extraídos. Acionando Rede Neural...", 0.1)
        
        if api_key:
            report = generate_intel_report(articles, api_key, update_ui)
            
            status_box.update(label="✅ Missão Cumprida!", state="complete", expanded=False)
            
            st.subheader("📄 Relatório de Inteligência")
            st.markdown(f'<div class="ai-box">{report}</div>', unsafe_allow_html=True)
        else:
            status_box.update(label="⚠️ Falta Chave API", state="error")
            
        # 3. Grid Visual
        st.divider()
        st.caption(f"Fontes Processadas: {len(articles)}")
        cols = st.columns(3)
        for i, row in enumerate(articles):
            with cols[i%3]:
                st.markdown(f"""
                <div class="news-card">
                    <div class="source-tag">{row['source_domain']}</div>
                    <div class="card-title">{row['title']}</div>
                    <div class="card-preview">{" ".join(row['content'][:3])}...</div>
                    <a href="{row['url']}" target="_blank" class="read-btn">Ler original 🔗</a>
                </div>
                """, unsafe_allow_html=True)
    else:
        status_box.update(label="❌ Falha na Extração", state="error")