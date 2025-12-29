#!/bin/bash
set -e

echo "🔧 Verificando ambiente..."

# Detectar se chromium está instalado
if ! command -v chromium &> /dev/null && ! command -v chromium-browser &> /dev/null && ! command -v google-chrome &> /dev/null; then
    echo "⚠️  Chromium não detectado. Tentando instalar..."
    
    # Tentar com sudo primeiro
    if sudo apt-get update &> /dev/null 2>&1; then
        sudo apt-get install -y chromium-browser 2>&1 || sudo apt-get install -y chromium 2>&1
        sudo apt-get install -y fonts-liberation 2>&1
    else
        # Tentar sem sudo (pode estar em container com user root)
        apt-get update 2>&1 || true
        apt-get install -y chromium-browser 2>&1 || apt-get install -y chromium 2>&1 || true
        apt-get install -y fonts-liberation 2>&1 || true
    fi
fi

# Verificar novamente
if command -v chromium &> /dev/null; then
    echo "✅ Chromium encontrado: $(which chromium)"
elif command -v chromium-browser &> /dev/null; then
    echo "✅ Chromium encontrado: $(which chromium-browser)"
elif command -v google-chrome &> /dev/null; then
    echo "✅ Chrome encontrado: $(which google-chrome)"
else
    echo "❌ Nenhum navegador detectado. Instale manualmente:"
    echo "   sudo apt-get update && sudo apt-get install -y chromium"
    exit 1
fi

echo ""
echo "🚀 Executando app.py..."
python app.py
