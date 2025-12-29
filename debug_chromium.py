#!/usr/bin/env python3
"""
Debug e diagnóstico completo do Chromium + Selenium.
"""
import subprocess
import sys
import os

def run(cmd):
    print(f"→ {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr[:500])
    return result.returncode == 0

print("=" * 70)
print("🔍 VERIFICANDO CHROMIUM E DEPENDÊNCIAS")
print("=" * 70)

print("\n1️⃣ Verificar Chromium instalado:")
run("which chromium-browser || which chromium || which google-chrome")

print("\n2️⃣ Verificar versão:")
run("chromium-browser --version 2>/dev/null || chromium --version 2>/dev/null || google-chrome --version")

print("\n3️⃣ Verificar libs críticas:")
libs = [
    "libnss3", "libgconf-2-4", "libx11-6", "libx11-xcb1", 
    "libxcb1", "libxss1", "fonts-liberation", "libglib2.0-0",
    "libxext6", "libxrender1", "libasound2", "libpangocairo-1.0-0"
]
for lib in libs:
    result = subprocess.run(f"dpkg -l | grep {lib}", shell=True, capture_output=True, text=True)
    status = "✅" if result.returncode == 0 else "❌"
    print(f"{status} {lib}")

print("\n4️⃣ Tentar instalar libs faltantes:")
run("apt-get update")
run("apt-get install -y libnss3 libgconf-2-4 libx11-6 libx11-xcb1 libxcb1 libxss1 fonts-liberation libglib2.0-0 libxext6 libxrender1 libasound2")

print("\n5️⃣ Executar app.py:")
print("")
os.system("cd /workspaces/codespaces-blank && python app.py")
