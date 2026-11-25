#!/usr/bin/env python3
import matplotlib
matplotlib.use('Agg')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.tri import Triangulation
from scipy.spatial import Delaunay
from pathlib import Path
import matplotlib.animation as animation

BASE = Path("/mnt/c/Users/Maria Engracia/Desktop/Andre/IA/Microplastico/EHD8L_BaiaGuanabara")
CSV = BASE / "02_Malha_e_Geometria/Nos_e_Elementos"
OUT_PNG = Path("/mnt/c/Users/Maria Engracia/Desktop/baia_3d_definitivo.png")
OUT_GIF = Path("/mnt/c/Users/Maria Engracia/Desktop/baia_3d_mare.gif")

print("="*70)
print("GERANDO VISUALIZACAO 3D DEFINITIVA - BAIA DE GUANABARA")
print("="*70)

# 1. Carregar dados
print("\n[1/4] Carregando dados SisBaHiA...")
df_nos = pd.read_csv(CSV / "no.csv")
df_elem = pd.read_csv(CSV / "elemento.csv")

nos = df_nos.iloc[:, 1:4].values
elems = df_elem.iloc[:, 1:4].values - 1

print(f"  OK {len(nos)} nos, {len(elems)} elementos")
print(f"  OK Z (batimetria): min={nos[:,2].min():.1f}m, max={nos[:,2].max():.1f}m")

# 2. Triangulacao
print("\n[2/4] Preparando triangulacao...")
tri = Delaunay(nos[:, :2])
triang = Triangulation(nos[:, 0], nos[:, 1], tri.simplices)

# Concentracao inicial
cx = np.mean(nos[:, 0])
cy = np.mean(nos[:, 1])
ux = cx - 8000
uy = cy - 12000
dist = np.sqrt((nos[:, 0] - ux)**2 + (nos[:, 1] - uy)**2)
C0 = np.exp(-2.0 * (dist / dist.max())**2)

# Correntes de mare
dx = nos[:, 0] - cx
dy = nos[:, 1] - cy
r = np.sqrt(dx**2 + dy**2) + 1e-6
vx = -dy / r
vy = dx / r

# 3. Imagem 3D estatica
print("\n[3/4] Gerando imagem 3D estatica (PNG)...")
fig = plt.figure(figsize=(16, 12))
ax = fig.add_subplot(111, projection='3d')

surf = ax.plot_trisurf(nos[:, 0], nos[:, 1], nos[:, 2],
                       triangles=tri.simplices,
                       cmap='viridis',
                       alpha=0.9,
                       edgecolor='none',
                       antialiased=True)

ax.set_title('Baia de Guanabara - Visualizacao 3D\nBatimetria Real + Microplasticos',
             fontsize=16, fontweight='bold', pad=20)
ax.set_xlabel('Coordenada X (UTM)', fontsize=12, labelpad=10)
ax.set_ylabel('Coordenada Y (UTM)', fontsize=12, labelpad=10)
ax.set_zlabel('Profundidade (m)', fontsize=12, labelpad=10)
ax.view_init(elev=30, azim=-60)

plt.colorbar(surf, ax=ax, shrink=0.5, aspect=10, label='Concentracao MP')
plt.tight_layout()
plt.savefig(OUT_PNG, dpi=150, bbox_inches='tight')
plt.close()
print(f"  OK PNG salvo: {OUT_PNG}")
print(f"  OK Tamanho: {OUT_PNG.stat().st_size / 1024:.1f} KB")

# 4. Animacao GIF
print("\n[4/4] Gerando animacao do ciclo de mare (GIF)...")
PERIODO = 12.42 * 3600
N_FRAMES = 20
frames_time = np.linspace(0, PERIODO, N_FRAMES)

fig_anim = plt.figure(figsize=(14, 10))
ax_anim = fig_anim.add_subplot(111, projection='3d')

ax_anim.set_xlim(nos[:, 0].min(), nos[:, 0].max())
ax_anim.set_ylim(nos[:, 1].min(), nos[:, 1].max())
ax_anim.set_zlim(nos[:, 2].min(), nos[:, 2].max())
ax_anim.view_init(elev=30, azim=-60)

# Titulo com fonte configurada corretamente
title = ax_anim.set_title('Ciclo de Mare - Baia de Guanabara', fontsize=14, fontweight='bold')

# Superficie base
ax_anim.plot_trisurf(nos[:, 0], nos[:, 1], nos[:, 2],
                     triangles=tri.simplices,
                     cmap='Blues', alpha=0.3, edgecolor='none')

# Scatter dos microplasticos
scatter = ax_anim.scatter(nos[:, 0], nos[:, 1], nos[:, 2],
                          c=C0, cmap='hot', s=5, alpha=0.8, vmin=0, vmax=1)
plt.colorbar(scatter, ax=ax_anim, shrink=0.5, label='Concentracao MP')

ax_anim.set_xlabel('X (UTM)')
ax_anim.set_ylabel('Y (UTM)')
ax_anim.set_zlabel('Z (m)')

def animate(i):
    t = frames_time[i]
    fator = np.sin(2 * np.pi * t / PERIODO)
    
    desloc_x = vx * fator * 5000
    desloc_y = vy * fator * 5000
    
    x_novo = nos[:, 0] + desloc_x
    y_novo = nos[:, 1] + desloc_y
    
    dist_novo = np.sqrt((x_novo - ux)**2 + (y_novo - uy)**2)
    C_t = np.exp(-2.0 * (dist_novo / dist.max())**2)
    
    scatter._offsets3d = (nos[:, 0], nos[:, 1], nos[:, 2])
    scatter.set_array(C_t)
    
    hora = t / 3600
    # CORRECAO: set_text() nao aceita fontsize, apenas o texto
    title.set_text(f'Ciclo de Mare - t = {hora:.2f}h | Fator = {fator:+.2f}')
    
    return [scatter, title]

print("  Renderizando frames (aguarde)...")
anim = animation.FuncAnimation(fig_anim, animate, frames=N_FRAMES,
                                interval=400, blit=False)

try:
    anim.save(OUT_GIF, writer='pillow', fps=3, dpi=100)
    print(f"  OK GIF salvo: {OUT_GIF}")
    print(f"  OK Tamanho: {OUT_GIF.stat().st_size / 1024:.1f} KB")
except Exception as e:
    print(f"  AVISO: GIF falhou ({e})")
    print("  Tentando salvar como multiplos PNGs...")
    for i in range(N_FRAMES):
        animate(i)
        frame_path = OUT_GIF.parent / f"baia_frame_{i:03d}.png"
        fig_anim.savefig(frame_path, dpi=80, bbox_inches='tight')
    print(f"  OK {N_FRAMES} frames PNG salvos em: {OUT_GIF.parent}")

plt.close()

print("\n" + "="*70)
print("SUCESSO! Arquivos no Desktop:")
print(f"  1. {OUT_PNG.name} (imagem 3D estatica)")
print(f"  2. {OUT_GIF.name} (animacao do ciclo de mare)")
print("="*70)
