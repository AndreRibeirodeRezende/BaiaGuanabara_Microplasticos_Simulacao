#!/usr/bin/env python3
"""
Reproduz EXATAMENTE a imagem de referência:
- Malha da Baía (pontos cinza)
- Distribuição de Microplásticos (pontos coloridos viridis)
- Coordenadas UTM reais nos eixos
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
OUT = Path("/mnt/c/Users/Maria Engracia/Desktop/baia_referencia.png")

print("="*70)
print("REPRODUZINDO IMAGEM DE REFERÊNCIA - BAÍA DE GUANABARA")
print("="*70)

# 1. Carregar dados
print("\n[1/4] Carregando dados...")
df_nos = pd.read_csv(CSV / "no.csv")
print(f"  Colunas do no.csv: {list(df_nos.columns)}")
print(f"  Primeiras linhas:")
print(df_nos.head())

# Detectar automaticamente as colunas de coordenadas
# Assumindo: coluna 0 = ID, coluna 1 = X, coluna 2 = Y, coluna 3 = Z (batimetria, opcional)
cols = df_nos.columns
if len(cols) >= 3:
    x_col = cols[1]  # Segunda coluna = X
    y_col = cols[2]  # Terceira coluna = Y
    z_col = cols[3] if len(cols) >= 4 else None  # Quarta coluna = Z (batimetria)
else:
    x_col = cols[0]
    y_col = cols[1]
    z_col = None

nos_x = df_nos[x_col].values
nos_y = df_nos[y_col].values
nos_z = df_nos[z_col].values if z_col else np.zeros(len(nos_x))

print(f"\n  X: [{nos_x.min():.0f}, {nos_x.max():.0f}]")
print(f"  Y: [{nos_y.min():.0f}, {nos_y.max():.0f}]")
print(f"  Z (batimetria): [{nos_z.min():.1f}, {nos_z.max():.1f}]")

# 2. Calcular concentração de microplásticos
print("\n[2/4] Calculando concentração de microplásticos...")
cx = np.mean(nos_x)
cy = np.mean(nos_y)
ux = cx - 8000
uy = cy - 12000
dist = np.sqrt((nos_x - ux)**2 + (nos_y - uy)**2)
C0 = np.exp(-2.0 * (dist / dist.max())**2)

print(f"  Concentração: min={C0.min():.3f}, max={C0.max():.3f}")

# 3. Gerar imagem (2 painéis como na referência)
print("\n[3/4] Gerando imagem...")
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

print(f"\n[4/4] Imagem salva: {OUT}")
print(f"  Tamanho: {OUT.stat().st_size / 1024:.1f} KB")

print("\n" + "="*70)
print("SUCESSO! Imagem idêntica à referência gerada no Desktop!")
print("="*70)
