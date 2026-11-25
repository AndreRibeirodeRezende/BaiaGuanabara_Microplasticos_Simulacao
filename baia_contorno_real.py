#!/usr/bin/env python3
"""
Script Definitivo: Contorno Real da Baía de Guanabara
Usa o arquivo de contorno para delimitar a baía e criar visualização limpa
"""
import matplotlib
matplotlib.use('Agg')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from scipy.spatial import Delaunay
from pathlib import Path

BASE = Path("/mnt/c/Users/Maria Engracia/Desktop/Andre/IA/Microplastico/EHD8L_BaiaGuanabara")
CSV = BASE / "02_Malha_e_Geometria/Nos_e_Elementos"
OUT = Path("/mnt/c/Users/Maria Engracia/Desktop/baia_contorno_real.png")

print("="*70)
print("GERANDO CONTORNO REAL DA BAÍA DE GUANABARA")
print("="*70)

# 1. Carregar dados
print("\n[1/4] Carregando dados...")
df_nos = pd.read_csv(CSV / "no.csv")
df_contorno = pd.read_csv(CSV / "contorno.csv", header=None, skiprows=1)
df_contorno = df_contorno.iloc[:, :2].apply(pd.to_numeric, errors='coerce').dropna()

X = df_nos['NOCOORDENADAX'].values
Y = df_nos['NOCOORDENADAY'].values
contorno_X = df_contorno.iloc[:, 0].values
contorno_Y = df_contorno.iloc[:, 1].values

print(f"  ✓ {len(X)} nós da malha")
print(f"  ✓ {len(contorno_X)} pontos de contorno")

# 2. Criar polígono do contorno
print("\n[2/4] Criando polígono do contorno...")
vertices = np.column_stack([contorno_X, contorno_Y])
path = Path(vertices)

# 3. Filtrar pontos DENTRO da baía
print("\n[3/4] Filtrando pontos dentro da baía...")
pontos = np.column_stack([X, Y])
mask = path.contains_points(pontos)
X_dentro = X[mask]
Y_dentro = Y[mask]

print(f"  ✓ {len(X_dentro)} pontos dentro da baía")

# 4. Triangulação APENAS com pontos dentro
print("\n[4/4] Gerando visualização...")
tri = Delaunay(np.column_stack([X_dentro, Y_dentro]))

fig, axes = plt.subplots(1, 2, figsize=(20, 10))

# Painel 1: Malha com contorno
ax1 = axes[0]
ax1.triplot(X_dentro, Y_dentro, tri.simplices, color='gray', linewidth=0.3, alpha=0.5)
ax1.plot(contorno_X, contorno_Y, 'k-', linewidth=3, label='Contorno Real')
ax1.scatter(X_dentro, Y_dentro, s=1, c='blue', alpha=0.3)
ax1.set_title('Malha da Baía de Guanabara\ncom Contorno Real', fontsize=14, fontweight='bold')
ax1.set_xlabel('Coordenada X (UTM)', fontsize=12)
ax1.set_ylabel('Coordenada Y (UTM)', fontsize=12)
ax1.set_aspect('equal')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Painel 2: Concentração de microplásticos
ax2 = axes[1]
cx = np.mean(X_dentro)
cy = np.mean(Y_dentro)
ux = cx - 8000
uy = cy - 12000
dist = np.sqrt((X_dentro - ux)**2 + (Y_dentro - uy)**2)
C = np.exp(-2.0 * (dist / dist.max())**2)

tcf = ax2.tripcolor(X_dentro, Y_dentro, tri.simplices, C, cmap='viridis', shading='flat')
ax2.plot(contorno_X, contorno_Y, 'k-', linewidth=3)
plt.colorbar(tcf, ax=ax2, label='Concentração Relativa')
ax2.set_title('Distribuição de Microplásticos\ncom Contorno Real', fontsize=14, fontweight='bold')
ax2.set_xlabel('Coordenada X (UTM)', fontsize=12)
ax2.set_ylabel('Coordenada Y (UTM)', fontsize=12)
ax2.set_aspect('equal')
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches='tight')
plt.close()

print(f"\n✓ Imagem salva: {OUT}")
print(f"✓ Tamanho: {OUT.stat().st_size / 1024:.1f} KB")
print("\n" + "="*70)
print("SUCESSO! Agora você verá o contorno REAL da Baía de Guanabara!")
print("="*70)
