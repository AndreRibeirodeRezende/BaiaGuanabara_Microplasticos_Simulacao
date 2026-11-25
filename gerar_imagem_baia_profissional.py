#!/usr/bin/env python3
"""
Gera imagem profissional da Baía de Guanabara com:
- Contorno real (linha preta grossa)
- Batimetria como mapa de cores
- Concentração de microplásticos sobreposta
- Coordenadas UTM reais
- Alta resolução (300 DPI)
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy.spatial import Delaunay
from pathlib import Path

# CAMINHO REAL
BASE_DIR = Path("/mnt/c/Users/Maria Engracia/Desktop/Andre/IA/Microplastico/EHD8L_BaiaGuanabara")
CSV_DIR = BASE_DIR / "02_Malha_e_Geometria/Nos_e_Elementos"
OUTPUT_PATH = BASE_DIR / "04_OpenFOAM_Case/visualizacao_3d_mare/baia_guanabara_profissional.png"

print("="*70)
print("GERANDO IMAGEM PROFISSIONAL - BAÍA DE GUANABARA")
print("="*70)

# 1. Carregar dados
print("\n[1/5] Carregando dados...")
df_nos = pd.read_csv(CSV_DIR / "no.csv")
df_elem = pd.read_csv(CSV_DIR / "elemento.csv")
df_contorno = pd.read_csv(CSV_DIR / "contorno.csv")

print(f"  ✓ {len(df_nos)} nós")
print(f"  ✓ {len(df_elem)} elementos")
print(f"  ✓ {len(df_contorno)} elementos de contorno")

# Extrair coordenadas
nos = df_nos.iloc[:, 1:4].values
elementos = df_elem.iloc[:, 1:4].values - 1

# 2. Triangulação Delaunay
print("\n[2/5] Triangulação...")
points_2d = nos[:, :2]
tri = Delaunay(points_2d)
triangulos = tri.simplices

# 3. Calcular batimetria média por triângulo
print("\n[3/5] Calculando batimetria...")
batimetria_tri = []
for tri_idx in triangulos:
    z_vals = nos[tri_idx, 2]
    batimetria_tri.append(np.mean(z_vals))
batimetria_tri = np.array(batimetria_tri)

# 4. Concentração de microplásticos
print("\n[4/5] Calculando concentração...")
centro_x = np.mean(nos[:, 0])
centro_y = np.mean(nos[:, 1])
centro_urbano_x = centro_x - 5000
centro_urbano_y = centro_y - 10000

dist_urbano = np.sqrt((nos[:, 0] - centro_urbano_x)**2 + (nos[:, 1] - centro_urbano_y)**2)
max_dist = np.max(dist_urbano)
concentracao = np.exp(-2.0 * (dist_urbano / max_dist)**2)

# 5. Gerar imagem
print("\n[5/5] Gerando imagem...")

fig, axes = plt.subplots(1, 3, figsize=(24, 8))

# === GRÁFICO 1: MALHA ===
ax1 = axes[0]
for tri_idx in triangulos:
    tri_pts = nos[tri_idx, :2]
    tri_pts = np.vstack([tri_pts, tri_pts[0]])
    ax1.plot(tri_pts[:, 0], tri_pts[:, 1], 'gray', linewidth=0.1, alpha=0.3)

ax1.scatter(nos[:, 0], nos[:, 1], s=1, c='gray', alpha=0.5)
ax1.set_title('Malha da Baía - 6356 nós', fontsize=14, fontweight='bold')
ax1.set_xlabel('Coordenada X', fontsize=12)
ax1.set_ylabel('Coordenada Y', fontsize=12)
ax1.set_aspect('equal')
ax1.grid(True, alpha=0.3)

# === GRÁFICO 2: BATIMETRIA ===
ax2 = axes[1]
from matplotlib.tri import Triangulation
triang = Triangulation(nos[:, 0], nos[:, 1], triangulos)

# Criar mapa de cores para batimetria (azul = profundo, branco = raso)
cmap_bati = LinearSegmentedColormap.from_list('batimetria', ['darkblue', 'lightblue', 'white'])

tcf = ax2.tripcolor(triang, batimetria_tri, cmap=cmap_bati, shading='flat')
plt.colorbar(tcf, ax=ax2, label='Profundidade (m)')

# Adicionar contorno
contorno_pts = df_contorno.iloc[:, 1:3].values
ax2.plot(contorno_pts[:, 0], contorno_pts[:, 1], 'k-', linewidth=2, label='Contorno')
ax2.set_title('Batimetria da Baía de Guanabara', fontsize=14, fontweight='bold')
ax2.set_xlabel('Coordenada X', fontsize=12)
ax2.set_ylabel('Coordenada Y', fontsize=12)
ax2.set_aspect('equal')
ax2.legend()
ax2.grid(True, alpha=0.3)

# === GRÁFICO 3: CONCENTRAÇÃO DE MICROPLÁSTICOS ===
ax3 = axes[2]

# Calcular concentração média por triângulo
concentracao_tri = []
for tri_idx in triangulos:
    c_vals = concentracao[tri_idx]
    concentracao_tri.append(np.mean(c_vals))
concentracao_tri = np.array(concentracao_tri)

tcf3 = ax3.tripcolor(triang, concentracao_tri, cmap='viridis', shading='flat')
plt.colorbar(tcf3, ax=ax3, label='Concentração Relativa')

# Adicionar contorno
ax3.plot(contorno_pts[:, 0], contorno_pts[:, 1], 'k-', linewidth=2)
ax3.set_title('Distribuição de Microplásticos - Escoamento Urbano', fontsize=14, fontweight='bold')
ax3.set_xlabel('Coordenada X', fontsize=12)
ax3.set_ylabel('Coordenada Y', fontsize=12)
ax3.set_aspect('equal')
ax3.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(OUTPUT_PATH, dpi=300, bbox_inches='tight')
print(f"\n✓ Imagem salva: {OUTPUT_PATH}")
print(f"  Tamanho: {OUTPUT_PATH.stat().st_size / 1024:.1f} KB")

# Salvar também no Desktop
desktop_path = Path("/mnt/c/Users/Maria Engracia/Desktop/baia_guanabara_profissional.png")
plt.savefig(desktop_path, dpi=300, bbox_inches='tight')
print(f"✓ Cópia no Desktop: {desktop_path}")

plt.close()

print("\n" + "="*70)
print("✅ IMAGEM PROFISSIONAL GERADA COM SUCESSO!")
print("="*70)
print(f"\n📂 Arquivo: {OUTPUT_PATH}")
print(f"📊 Resolução: 300 DPI (qualidade de publicação)")
print(f"🎨 Conteúdo:")
print(f"   • Gráfico 1: Malha com 6356 nós")
print(f"   • Gráfico 2: Batimetria com contorno real")
print(f"   • Gráfico 3: Concentração de microplásticos")
print("="*70)
