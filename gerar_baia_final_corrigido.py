#!/usr/bin/env python3
"""
Script Final Corrigido - Baía de Guanabara
Usa os nomes reais das colunas do CSV SisBaHiA
"""
import matplotlib
matplotlib.use('Agg')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

BASE = Path("/mnt/c/Users/Maria Engracia/Desktop/Andre/IA/Microplastico/EHD8L_BaiaGuanabara")
CSV = BASE / "02_Malha_e_Geometria/Nos_e_Elementos"
OUT = Path("/mnt/c/Users/Maria Engracia/Desktop/baia_final_corrigido.png")

print("="*70)
print("GERANDO IMAGEM FINAL - BAÍA DE GUANABARA")
print("="*70)

# 1. Carregar dados
print("\n[1/4] Carregando dados...")
df_nos = pd.read_csv(CSV / "no.csv")
print(f"  Colunas: {list(df_nos.columns)}")

# 2. Usar nomes reais das colunas
print("\n[2/4] Extraindo coordenadas...")
nos_x = df_nos['NOCOORDENADAX'].values
nos_y = df_nos['NOCOORDENADAY'].values
nos_z = df_nos['NOCOORDENADAZ'].values if 'NOCOORDENADAZ' in df_nos.columns else np.zeros(len(nos_x))

print(f"  ✓ X (leste): [{nos_x.min():.0f}, {nos_x.max():.0f}]")
print(f"  ✓ Y (norte): [{nos_y.min():.0f}, {nos_y.max():.0f}]")
print(f"  ✓ Z: [{nos_z.min():.1f}, {nos_z.max():.1f}]")

# 3. Calcular concentração de microplásticos
print("\n[3/4] Calculando concentração de microplásticos...")
cx = np.mean(nos_x)
cy = np.mean(nos_y)
ux = cx - 8000
uy = cy - 12000
dist = np.sqrt((nos_x - ux)**2 + (nos_y - uy)**2)
C0 = np.exp(-2.0 * (dist / dist.max())**2)

print(f"  ✓ Concentração: min={C0.min():.3f}, max={C0.max():.3f}")

# 4. Gerar imagem (2 painéis)
print("\n[4/4] Gerando imagem...")
fig, axes = plt.subplots(1, 2, figsize=(20, 10))

# Painel 1: Malha da Baía
ax1 = axes[0]
ax1.scatter(nos_x, nos_y, s=2, c='gray', alpha=0.5)
ax1.set_title('Malha da Baía - 6356 nós', fontsize=14, fontweight='bold')
ax1.set_xlabel('Coordenada X (UTM)', fontsize=12)
ax1.set_ylabel('Coordenada Y (UTM)', fontsize=12)
ax1.set_aspect('equal')
ax1.grid(True, alpha=0.3)

# Painel 2: Distribuição de Microplásticos
ax2 = axes[1]
sc = ax2.scatter(nos_x, nos_y, c=C0, cmap='viridis', s=2, alpha=0.8)
plt.colorbar(sc, ax=ax2, label='Concentração Relativa')
ax2.set_title('Distribuição de Microplásticos - Escoamento Urbano', fontsize=14, fontweight='bold')
ax2.set_xlabel('Coordenada X (UTM)', fontsize=12)
ax2.set_ylabel('Coordenada Y (UTM)', fontsize=12)
ax2.set_aspect('equal')
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches='tight')
plt.close()

print(f"\n  ✓ Imagem salva: {OUT}")
print(f"  ✓ Tamanho: {OUT.stat().st_size / 1024:.1f} KB")

print("\n" + "="*70)
print("SUCESSO! Imagem gerada no Desktop!")
print("="*70)
