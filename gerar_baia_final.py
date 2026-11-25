#!/usr/bin/env python3
import matplotlib
matplotlib.use('Agg')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.tri import Triangulation
from pathlib import Path

BASE = Path("/mnt/c/Users/Maria Engracia/Desktop/Andre/IA/Microplastico/EHD8L_BaiaGuanabara")
CSV = BASE / "02_Malha_e_Geometria/Nos_e_Elementos"
OUT = Path("/mnt/c/Users/Maria Engracia/Desktop/baia_guanabara_final.png")

print("Carregando dados...")
df_nos = pd.read_csv(CSV / "no.csv")
df_elem = pd.read_csv(CSV / "elemento.csv")

nos = df_nos.iloc[:, 1:4].values
elems = df_elem.iloc[:, 1:4].values - 1

print(f"Nos: {len(nos)}, Elementos: {len(elems)}")
print(f"Z min={nos[:,2].min():.1f}, Z max={nos[:,2].max():.1f}")

# Carregar contorno com tratamento de erro
try:
    df_cont = pd.read_csv(CSV / "contorno.csv", header=None, skiprows=1)
    df_cont = df_cont.iloc[:, :2].apply(pd.to_numeric, errors='coerce').dropna()
    contorno = df_cont.values
    print(f"Contorno: {len(contorno)} pontos validos")
except Exception as e:
    print(f"Aviso contorno: {e}")
    contorno = None

# Triangulacao
from scipy.spatial import Delaunay
tri = Delaunay(nos[:, :2])
triang = Triangulation(nos[:, 0], nos[:, 1], tri.simplices)

# Concentracao
cx = np.mean(nos[:, 0])
cy = np.mean(nos[:, 1])
ux = cx - 8000
uy = cy - 12000
dist = np.sqrt((nos[:, 0] - ux)**2 + (nos[:, 1] - uy)**2)
C0 = np.exp(-2.0 * (dist / dist.max())**2)

# Concentracao por triangulo
C_tri = np.array([np.mean(C0[t]) for t in tri.simplices])
Z_tri = np.array([np.mean(nos[t, 2]) for t in tri.simplices])

print("Gerando imagem...")
fig, axes = plt.subplots(1, 3, figsize=(24, 8))

# Painel 1: Malha
ax1 = axes[0]
ax1.triplot(triang, color='gray', linewidth=0.3, alpha=0.5)
ax1.scatter(nos[:, 0], nos[:, 1], s=0.5, c='gray', alpha=0.3)
ax1.set_title('Malha da Baia - 6356 nos', fontsize=14, fontweight='bold')
ax1.set_xlabel('Coordenada X')
ax1.set_ylabel('Coordenada Y')
ax1.set_aspect('equal')
ax1.grid(True, alpha=0.3)

# Painel 2: Batimetria
ax2 = axes[1]
tcf2 = ax2.tripcolor(triang, Z_tri, cmap='Blues_r', shading='flat')
plt.colorbar(tcf2, ax=ax2, label='Profundidade (m)')
if contorno is not None:
    ax2.plot(contorno[:, 0], contorno[:, 1], 'k-', linewidth=2.5)
ax2.set_title('Batimetria da Baia de Guanabara', fontsize=14, fontweight='bold')
ax2.set_xlabel('Coordenada X')
ax2.set_ylabel('Coordenada Y')
ax2.set_aspect('equal')
ax2.grid(True, alpha=0.3)

# Painel 3: Microplasticos
ax3 = axes[2]
tcf3 = ax3.tripcolor(triang, C_tri, cmap='viridis', shading='flat')
plt.colorbar(tcf3, ax=ax3, label='Concentracao Relativa')
if contorno is not None:
    ax3.plot(contorno[:, 0], contorno[:, 1], 'k-', linewidth=2.5)
ax3.set_title('Distribuicao de Microplasticos', fontsize=14, fontweight='bold')
ax3.set_xlabel('Coordenada X')
ax3.set_ylabel('Coordenada Y')
ax3.set_aspect('equal')
ax3.grid(True, alpha=0.3)

plt.suptitle('Framework EHD-8L - Baia de Guanabara (SisBaHiA)', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig(OUT, dpi=200, bbox_inches='tight')
plt.close()

print(f"Imagem salva: {OUT}")
print(f"Tamanho: {OUT.stat().st_size / 1024:.1f} KB")
print("Abra no Desktop do Windows!")
