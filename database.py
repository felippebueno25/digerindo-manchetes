import sqlite3
import json
from datetime import datetime

DB_NAME = "news_intel.db"

def init_db():
    """Cria as tabelas se não existirem."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Tabela de Relatórios (A Análise da IA)
    c.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_url TEXT,
            topic_name TEXT,
            summary_text TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de Artigos (As Fontes usadas naquele relatório)
    # Usamos chave estrangeira para ligar ao relatório
    c.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER,
            title TEXT,
            source_domain TEXT,
            url TEXT,
            content_snippet TEXT,
            FOREIGN KEY(report_id) REFERENCES reports(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def save_full_report(topic_url, topic_name, summary_text, articles):
    """Salva o relatório e todas as suas fontes de uma vez (Transação Atômica)."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    try:
        # 1. Inserir Relatório
        c.execute("INSERT INTO reports (topic_url, topic_name, summary_text) VALUES (?, ?, ?)",
                  (topic_url, topic_name, summary_text))
        report_id = c.lastrowid
        
        # 2. Inserir Artigos vinculados
        for art in articles:
            # Pegamos só um pedaço do conteúdo para preview, para não pesar o banco
            snippet = str(art['content'])[:300] if art.get('content') else ""
            c.execute("""
                INSERT INTO articles (report_id, title, source_domain, url, content_snippet)
                VALUES (?, ?, ?, ?, ?)
            """, (report_id, art['title'], art['source_domain'], art['url'], snippet))
        
        conn.commit()
        return report_id
    except Exception as e:
        conn.rollback()
        print(f"Erro ao salvar no banco: {e}")
        raise e
    finally:
        conn.close()

def get_all_reports():
    """Busca o histórico para o menu lateral."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Para acessar colunas pelo nome
    c = conn.cursor()
    c.execute("SELECT id, topic_name, created_at FROM reports ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_report_details(report_id):
    """Recupera um relatório completo e suas fontes."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Pega o relatório
    c.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
    report = dict(c.fetchone())
    
    # Pega os artigos
    c.execute("SELECT * FROM articles WHERE report_id = ?", (report_id,))
    articles = [dict(row) for row in c.fetchall()]
    
    conn.close()
    return report, articles

# Inicializa o banco assim que o arquivo é importado
init_db()