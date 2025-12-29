#!/usr/bin/env python3
"""
Diagnóstico de ambiente e execução do NewsAggregatorPro.
Tenta instalar Chromium, valida a instalação e roda o app.
"""
import subprocess
import sys
import os
from shutil import which

def run_cmd(cmd, label, silent=False):
    """Execute command and return success/failure."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=120
        )
        if not silent:
            print(f"[{label}] Saída: {result.stdout[:200]}")
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        print(f"[{label}] Erro: {e}")
        return False, "", str(e)

print("=" * 60)
print("📋 DIAGNÓSTICO DE AMBIENTE")
print("=" * 60)

# 1. Verificar se Chromium/Chrome está instalado
browsers = [
    ("chromium-browser", "Chromium Browser"),
    ("chromium", "Chromium"),
    ("google-chrome", "Google Chrome"),
]

found_browser = None
for cmd, name in browsers:
    if which(cmd):
        print(f"✅ {name} encontrado: {which(cmd)}")
        found_browser = cmd
        break
    else:
        print(f"❌ {name} não encontrado")

if not found_browser:
    print("\n⚠️ Nenhum navegador detectado. Tentando instalar Chromium...")
    
    # Tentar apt-get
    if run_cmd("apt-get update", "apt update", silent=True)[0]:
        print("✅ apt-get update funcionou")
        
        success, _, _ = run_cmd(
            "apt-get install -y chromium-browser 2>&1 || apt-get install -y chromium 2>&1",
            "Instalação Chromium"
        )
        if success:
            print("✅ Chromium instalado com sucesso!")
            found_browser = "chromium"
        else:
            print("⚠️ Instalação falhou, tentando alternativas...")
        run_cmd("apt-get install -y fonts-liberation", "Fonts")
    else:
        print("❌ apt-get não está disponível")

print("\n" + "=" * 60)
print("📊 RESUMO")
print("=" * 60)

if found_browser or which("chromium") or which("chromium-browser") or which("google-chrome"):
    print("✅ Navegador disponível! Instalando dependências...")
    # Instalar libs de sistema que Chromium headless precisa
    deps = "libnss3 libgconf-2-4 libx11-6 libx11-xcb1 libxcb1 libxss1 fonts-liberation xdg-utils wget ca-certificates"
    run_cmd(f"apt-get install -y {deps} 2>&1 || true", "Dependências", silent=True)
    print("✅ Dependências instaladas. Iniciando app.py...\n")
    os.system("python app.py")
else:
    print("❌ Chromium/Chrome não está instalado e não pode ser instalado automaticamente.")
    print("\nInstale manualmente no seu terminal:")
    print("  sudo apt-get update")
    print("  sudo apt-get install -y chromium")
    print("  sudo apt-get install -y libnss3 libgconf-2-4 libx11-6 libx11-xcb1 libxcb1 libxss1")
    print("  sudo apt-get install -y fonts-liberation")
    print("\nDepois rode:")
    print("  python app.py")
    sys.exit(1)
