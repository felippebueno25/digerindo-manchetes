#!/bin/bash
# Script para instalar dependências do Chromium e rodar o app
# Execução: bash /workspaces/codespaces-blank/install_and_run.sh

echo "🔧 Instalando dependências do Chromium..."
sudo apt-get update && \
sudo apt-get install -y \
  libnss3 \
  libgconf-2-4 \
  libx11-6 \
  libx11-xcb1 \
  libxcb1 \
  libxss1 \
  fonts-liberation \
  xdg-utils \
  wget \
  ca-certificates

echo ""
echo "✅ Dependências instaladas!"
echo ""
echo "🚀 Executando app.py..."
python /workspaces/codespaces-blank/app.py
