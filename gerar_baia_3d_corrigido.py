#!/usr/bin/env python3
"""
Script Corrigido: Visualização 3D da Baía de Guanabara
- Backend Agg para funcionar no WSL sem display gráfico
- Tratamento correto do arquivo contorno.csv (pula cabeçalhos de texto)
- Gera imagem 3D estática e animação GIF
"""
import matplotlib
matplotlib.use('Agg')  # CRÍTICO: Evita erro de display no WSL

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.tri import Triangulation
from scipy.spatial import Delaunay
from pathlib import Path
import matplotlib.animation as animation

# ==========================================
# 1. CONFIGURAÇÕES E CAMINHOS
# ==========================================
BASE_DIR = Path("/mnt/c/Users/Maria Engracia/Desktop/Andre/IA/Microplastico/EHD8L_BaiaGuanabara")
CSV_DIR = BASE_DIR / "02_Malha_e_Geometria/Nos_e_Elementos"
OUTPUT_DIR = Path("/mnt/c/Users/Maria Engracia/Desktop")

print("="*70)
print("GERANDO VISUALIZAÇÃO 3D COMPLETA - BAÍA DE GUANABARA")
print("="*70)

# ==========================================
# 2. CARREGAR DADOS REAIS
# ==========================================
print("\n[1/5] Carregando dados do SisBaHiA...")
df_nos = pd.read_csv(CSV_DIR / "no.csv")
df_elem = pd.read_csv(CSV_DIR / "elemento.csv")

# CRÍTICO: Ler contorno pulando linhas de texto/cabeçalho
# Tenta ler o CSV e converte apenas colunas numéricas
df_contorno_raw = pd.read_csv(CSV_DIR / "contorno.csv", header=None, skiprows=1)

# Filtra apenas linhas que têm valores numéricos nas primeiras 2 colunas
df_contorno = df_contorno_raw.iloc[:, :2].apply(pd.to_numeric, errors='coerce').dropna()

print(f"  OK {len(df_nos)} nos carregados")
print(f"  OK {len(df_elem)} elementos carregados")
print(f"  OK {len(df_contorno)} pontos de contorno válidos")

# Extrair coordenadas
nos = df_nos.iloc[:, 1:4].values  # X, Y, Z (Batimetria real)
elementos = df_elem.iloc[:, 1:4].values - 1
contorno = df_contorno.values

print(f"\n  Batimetria: Z min={nos[:,2].min():.1f}m, Z max={nos[:,2].max():.1f}m")
print(f"  Contorno: X[{contorno[:,0].min():.0f}, {contorno[:,0].max():.0f}]")
print(f"  Contorno: Y[{contorno[:,1].min():.0f}, {contorno[:,1].max():.0f}]")

# ==========================================
# 3. PREPARAR MALHA PARA 3D
# ==========================================
print("\n[2/5] Preparando triangulação...")
tri = Delaunay(nos[:, :2])
triang = Triangulation(nos[:, 0], nos[:, 1], tri.simplices)

# Concentração inicial de microplásticos (foco urbano)
centro_x = np.mean(nos[:, 0])
centro_y = np.mean(nos[:, 1])
centro_urbano_x = centro_x - 8000
centro_urbano_y = centro_y - 12000
dist = np.sqrt((nos[:, 0] - centro_urbano_x)**2 + (nos[:, 1] - centro_urbano_y)**2)
C0 = np.exp(-2.0 * (dist / dist.max())**2)

# ==========================================
# 4. GERAR IMAGEM 3D ESTÁTICA (PNG)
# ==========================================
print("\n[3/5] Gerando imagem 3D estática (PNG)...")
fig = plt.figure(figsize=(16, 12))
ax = fig.add_subplot(111, projection='3d')

# Plotar superfície 3D com batimetria real
surf = ax.plot_trisurf(nos[:, 0], nos[:, 1], nos[:, 2], 
                       triangles=tri.simplices, 
                       cmap='viridis', 
                       alpha=0.8, 
                       edgecolor='none')

# Adicionar contorno da baía (linha preta grossa)
z_contorno = np.mean(nos[:, 2])
ax.plot(contorno[:, 0], contorno[:, 1], z_contorno, 
        color='black', linewidth=2.5, label='Contorno Real')

ax.set_title('Baía de Guanabara - Visualização 3D com Batimetria Real', 
             fontsize=16, fontweight='bold', pad=20)
ax.set_xlabel('Coordenada X (UTM)', fontsize=12, labelpad=10)
ax.set_ylabel('Coordenada Y (UTM)', fontsize=12, labelpad=10)
ax.set_zlabel('Profundidade (m)', fontsize=12, labelpad=10)

# Ajustar ângulo da câmera para ver de cima e de lado (perspectiva 3D)
ax.view_init(elev=45, azim=-45)

plt.colorbar(surf, ax=ax, shrink=0.5, aspect=10, label='Concentração de Microplásticos')
plt.tight_layout()

png_path = OUTPUT_DIR / "baia_guanabara_3d_corrigida.png"
plt.savefig(png_path, dpi=150, bbox_inches='tight')
plt.close()
print(f"  OK Imagem 3D salva: {png_path}")

# ==========================================
# 5. GERAR ANIMAÇÃO DO CICLO DE MARÉ (GIF)
# ==========================================
print("\n[4/5] Gerando animação do ciclo de maré (GIF)...")

PERIODO_MARE = 12.42 * 3600  # 12h25min em segundos
N_FRAMES = 30
frames_time = np.linspace(0, PERIODO_MARE, N_FRAMES)

# Vetores de corrente rotacional
dx = nos[:, 0] - centro_x
dy = nos[:, 1] - centro_y
r = np.sqrt(dx**2 + dy**2) + 1e-6
vx_base = -dy / r
vy_base = dx / r

fig_anim = plt.figure(figsize=(14, 10))
ax_anim = fig_anim.add_subplot(111, projection='3d')

# Configuração inicial do gráfico 3D
ax_anim.set_xlim(nos[:, 0].min(), nos[:, 0].max())
ax_anim.set_ylim(nos[:, 1].min(), nos[:, 1].max())
ax_anim.set_zlim(nos[:, 2].min(), nos[:, 2].max())
ax_anim.set_xlabel('X (UTM)')
ax_anim.set_ylabel('Y (UTM)')
ax_anim.set_zlabel('Z (m)')
ax_anim.view_init(elev=40, azim=-60)
title_anim = ax_anim.set_title('')

# Plotar a superfície base (batimetria)
ax_anim.plot_trisurf(nos[:, 0], nos[:, 1], nos[:, 2], 
                     triangles=tri.simplices, 
                     cmap='Blues', alpha=0.3, edgecolor='none')

# Linha de contorno
ax_anim.plot(contorno[:, 0], contorno[:, 1], np.mean(nos[:, 2]), 
             color='black', linewidth=2)

# Scatter plot para os microplásticos (será atualizado na animação)
scatter = ax_anim.scatter(nos[:, 0], nos[:, 1], nos[:, 2], 
                          c=C0, cmap='hot', s=2, alpha=0.8, vmin=0, vmax=1)

plt.colorbar(scatter, ax=ax_anim, shrink=0.5, label='Concentração MP')

def animate(i):
    t = frames_time[i]
    fator_mare = np.sin(2 * np.pi * t / PERIODO_MARE)
    
    # Deslocar a fonte de poluição com a maré
    desloc_x = vx_base * fator_mare * 5000
    desloc_y = vy_base * fator_mare * 5000
    
    x_novo = nos[:, 0] + desloc_x
    y_novo = nos[:, 1] + desloc_y
    
    dist_novo = np.sqrt((x_novo - centro_urbano_x)**2 + (y_novo - centro_urbano_y)**2)
    C_t = np.exp(-2.0 * (dist_novo / dist.max())**2)
    
    scatter._offsets3d = (nos[:, 0],
