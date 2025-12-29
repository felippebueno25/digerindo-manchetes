import streamlit as st
import pandas as pd
from google import genai
from app import NewsAggregatorPro
import os
import time

# --- Configuração da Página ---
st.set_page_config(
    page_title="News Intel AI (Full Context)",
    page_icon="🧠",
    layout="wide"
)

# --- CSS ---
st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    .news-card {
        background-color: white; padding: 15px; border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 15px;
        border: 1px solid #e5e7eb; height: 100%; display: flex; flex-direction: column;
    }
    .source-tag { font-size: 0.75rem; font-weight: 700; color: #6b7280; text-transform: uppercase; margin-bottom: 8px; }
    .card-title { font-size: 1rem; font-weight: 600; color: #111; margin-bottom: 8px; line-height: 1.4; }
    .card-preview { font-size: 0.9em; color: #555; margin-bottom:10px; flex-grow: 1; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; }
    .read-btn { font-size: 0.8rem; color: #2563eb; text-decoration: none; margin-top: auto; }
    .ai-box { background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 25px; margin-bottom: 30px; }
</style>
""", unsafe_allow_html=True)

# --- Lógica de IA (Contexto Integral) ---
def generate_synthesis_full_context(articles, api_key, status_callback):
    """
    Envia TODAS as notícias INTEIRAS em uma única requisição.
    Usa a capacidade de 1 milhão de tokens do Gemini 2.0 Flash.
    """
    if not api_key: return "⚠️ Insira a API Key."
    
    try:
        client = genai.Client(api_key=api_key)
        
        status_callback(f"🧠 Preparando contexto integral com {len(articles)} notícias...", 0.1)
        
        # 1. Monta o Prompt Gigante SEM CORTES
        all_context = ""
        total_chars = 0
        
        for i, art in enumerate(articles):
            # Limpeza apenas de formatação (quebras de linha excessivas), mas mantendo todo o texto
            # .replace("\n", " ") economiza tokens sem perder informação semântica
            clean_content = " ".join(art['content']).replace("\n", " ")
            
            # ADICIONA TUDO (Sem slicing [:2500])
            all_context += f"## FONTE {i+1}: {art['source_domain']}\nTITULO: {art['title']}\nTEXTO COMPLETO: {clean_content}\n\n---\n\n"
            total_chars += len(clean_content)

        # Estimativa de tokens (1 token ~= 4 caracteres)
        est_tokens = total_chars // 4
        status_callback(f"🧠 Enviando {est_tokens:,} tokens para análise (Conteúdo Completo)...", 0.3)

        # 2. O Prompt
        prompt = f"""
        Atue como um Analista de Inteligência Sênior. Você recebeu a transcrição COMPLETA de {len(articles)} fontes de notícias.
        
        SUA TAREFA:
        Cruze todas as informações e gere o RELATÓRIO EXECUTIVO DEFINITIVO em Português.
        
        DIRETRIZES AVANÇADAS:
        - **Deep Reading:** Como você tem o texto completo, procure por detalhes sutis que estariam no meio ou fim das matérias.
        - **Citações Precisas:** Se houver uma frase impactante de uma autoridade, cite-a textualmente.
        - **Consistência:** Verifique se os detalhes técnicos (datas, valores, nomes) batem entre as fontes.
        
        ESTRUTURA DO RELATÓRIO (Markdown):
        1. **Resumo Executivo**: O fato central e seus desdobramentos imediatos.
        2. **Análise de Narrativas**: 
           - Visão A (ex: Governo/Situação)
           - Visão B (ex: Oposição/Crítica)
           - Visão C (ex: Internacional/Mercado)
        3. **Fatos Concretos e Dados**: Tabela ou lista de números confirmados.
        4. **Pontos de Divergência**: Onde as histórias não batem?
        5. **Insights Profundos**: Detalhes que só aparecem na leitura completa (blindspots).
        
        DADOS DE ENTRADA:
        {all_context}
        """

        # 3. Chamada Única
        # gemini-2.0-flash aguenta isso tranquilamente
        response = client.models.generate_content(
            model='gemini-2.0-flash', 
            contents=prompt
        )
        
        return response.text

    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg:
            return """
            ⚠️ **Limite de Tokens por Minuto atingido.**
            Embora o modelo aguente, a conta gratuita tem um limite de velocidade de entrada.
            Tente novamente em 1 minuto ou reduza ligeiramente o número de notícias na próxima vez.
            """
        return f"Erro na IA: {e}"

# --- Interface ---
with st.sidebar:
    st.header("Configurações")
    api_key = st.text_input("Gemini API Key", type="password", value=os.getenv("GEMINI_API_KEY", ""))

st.title("🧠 News Intel AI (Full Context)")
url_input = st.text_input("URL Google News:", placeholder="https://news.google.com/topics/...")
run_btn = st.button("Iniciar Varredura Total 🚀", type="primary")

if run_btn and url_input:
    status_box = st.status("🚀 Iniciando motor...", expanded=True)
    p_bar = status_box.progress(0)
    
    def update_ui(msg, pct):
        p_bar.progress(min(max(pct, 0.0), 1.0))
        status_box.write(f"**{msg}**")

    # 1. Extração
    agg = NewsAggregatorPro()
    articles = agg.run(url_input, progress_callback=update_ui)
    
    if not articles:
        status_box.update(label="❌ Nenhuma notícia encontrada.", state="error")
    else:
        # 2. Análise Full Context
        update_ui(f"✅ {len(articles)} artigos extraídos. Iniciando IA (Leitura Completa)...", 0.1)
        
        if api_key:
            synthesis = generate_synthesis_full_context(articles, api_key, update_ui)
            
            if "Erro" in synthesis or "Cota" in synthesis:
                 status_box.update(label="⚠️ Erro na IA", state="error")
                 st.error(synthesis)
            else:
                status_box.update(label="✅ Concluído!", state="complete", expanded=False)
                st.subheader("📊 Relatório de Inteligência")
                st.markdown(f'<div class="ai-box">{synthesis}</div>', unsafe_allow_html=True)
        else:
            status_box.update(label="⚠️ Falta API Key", state="warning")

        # 3. Grid
        st.divider()
        st.subheader(f"📚 Fontes ({len(articles)})")
        cols = st.columns(3)
        for i, row in enumerate(articles):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="news-card">
                    <div class="source-tag">{row['source_domain']}</div>
                    <div class="card-title">{row['title']}</div>
                    <div class="card-preview">{" ".join(row['content'][:3])}...</div>
                    <a href="{row['url']}" target="_blank" class="read-btn">Ler original 🔗</a>
                </div>
                """, unsafe_allow_html=True)