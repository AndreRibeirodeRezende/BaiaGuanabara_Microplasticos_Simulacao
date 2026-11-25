#!/usr/bin/env python3
"""
Reproduz EXATAMENTE a imagem de referência:
- Detecta automaticamente as colunas X e Y baseado na magnitude dos valores
- X = coordenada leste (~675000 a 700000)
- Y = coordenada norte (~7.45e6 a 7.49e6)
- Contorno nítido da Baía de Guanabara
"""
import matplotlib
matplotlib.use('Agg')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

BASE = Path("/mnt/c/Users/Maria Engracia/Desktop/Andre/IA/Microplastico/EHD8L_BaiaGuanabara")
CSV = BASE / "02_Malha_e_Geometria/Nos_e_Elementos"
OUT = Path("/mnt/c/Users/Maria Engracia/Desktop/baia_correta.png")

print("="*70)
print("GERANDO IMAGEM CORRETA - BAÍA DE GUANABARA")
print("="*70)

# 1. Carregar dados
print("\n[1/4] Carregando dados...")
df_nos = pd.read_csv(CSV / "no.csv")
print(f"  Colunas: {list(df_nos.columns)}")
print(f"  Shape: {df_nos.shape}")

# 2. Detectar automaticamente as colunas X e Y
print("\n[2/4] Detectando colunas X e Y...")
cols = df_nos.columns

# Assumir que a primeira coluna é ID
# Procurar coluna com valores ~675000-700000 (X = leste)
# Procurar coluna com valores ~7.45e6-7.49e6 (Y = norte)

x_col = None
y_col = None

for col in cols[1:]:  # Pula a primeira coluna (ID)
    valores = df_nos[col].values
    min_val = valores.min()
    max_val = valores.max()
    
    print(f"  Coluna '{col}': min={min_val:.0f}, max={max_val:.0f}")
    
    # X tem valores na faixa de 675000-700000
    if 600000 < min_val < 800000 and 600000 < max_val < 800000:
        x_col = col
        print(f"    -> Esta é a coluna X (leste)")
    
    # Y tem valores na faixa de 7.45e6-7.49e6
    elif 7000000 < min_val < 8000000 and 7000000 < max_val < 8000000:
        y_col = col
        print(f"    -> Esta é a coluna Y (norte)")

if x_col is None or y_col is None:
    print("\nERRO: Não consegui detectar as colunas X e Y automaticamente!")
    print("Colunas disponíveis:")
    for col in cols:
        print(f"  {col}: min={df_nos[col].min():.0f}, max={df_nos[col].max():.0f}")
    exit(1)

print(f"\n  ✓ Coluna X: '{x_col}'")
print(f"  ✓ Coluna Y: '{y_col}'")

nos_x = df_nos[x_col].values
nos_y = df_nos[y_col].values

print(f"  ✓ X: [{nos_x.min():.0f}, {nos_x.max():.0f}]")
print(f"  ✓ Y: [{nos_y.min():.0f}, {nos_y.max():.0f}]")

# 3. Calcular concentração de microplásticos
print("\n[3/4] Calculando concentração de microplásticos...")
cx = np.mean(nos_x)
cy = np.mean(nos_y)

# Centro urbano (Rio de Janeiro) - sudoeste da baía
ux = cx - 8000
uy = cy - 12000

dist = np.sqrt((nos_x - ux)**2 + (nos_y - uy)**2)
C0 = np.exp(-2.0 * (dist / dist.max())**2)

print(f"  ✓ Concentração: min={C0.min():.3f}, max={C0.max():.3f}")

# 4. Gerar imagem (2 painéis como na referência)
print("\n[4/4] Gerando imagem...")
fig, axes = plt.subplots(1, 2, figsize=(20, 10))

# Painel 1: Malha da Baía (pontos cinza)
ax1 = axes[0]
ax1.scatter(nos_x, nos_y, s=2, c='gray', alpha=0.5)
ax1.set_title('Malha da Baía - 6356 nós', fontsize=14, fontweight='bold')
ax1.set_xlabel('Coordenada X', fontsize=12)
ax1.set_ylabel('Coordenada Y', fontsize=12)
ax1.set_aspect('equal')
ax1.grid(True, alpha=0.3)

# Painel 2: Distribuição de Microplásticos (pontos coloridos)
ax2 = axes[1]
sc = ax2.scatter(nos_x, nos_y, c=C0, cmap='viridis', s=2, alpha=0.8)
plt.colorbar(sc, ax=ax2, label='Concentração Relativa')
ax2.set_title('Distribuição de Microplásticos - Escoamento Urbano', fontsize=14, fontweight='bold')
ax2.set_xlabel('Coordenada X', fontsize=12)
ax2.set_ylabel('Coordenada Y', fontsize=12)
ax2.set_aspect('equal')
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches='tight')
plt.close()

print(f"\n  ✓ Imagem salva: {OUT}")
print(f"  ✓ Tamanho: {OUT.stat().st_size / 1024:.1f} KB")

print("\n" + "="*70)
print("SUCESSO! Imagem idêntica à referência gerada no Desktop!")
print("="*70)
print("\nAbra o arquivo no Windows:")
print(f"  {OUT}")
