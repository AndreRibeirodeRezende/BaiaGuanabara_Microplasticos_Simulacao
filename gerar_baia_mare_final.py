#!/usr/bin/env python3
"""
BAÍA DE GUANABARA - 3D + CICLO DE MARÉ
Gera: (1) Imagem PNG de alta qualidade (vista de cima com contorno)
      (2) VTK 3D com animação de maré para ParaView
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.tri import Triangulation
from scipy.spatial import Delaunay
from pathlib import Path

BASE = Path("/mnt/c/Users/Maria Engracia/Desktop/Andre/IA/Microplastico/EHD8L_BaiaGuanabara")
CSV = BASE / "02_Malha_e_Geometria/Nos_e_Elementos"
OUT_PNG = Path("/mnt/c/Users/Maria Engracia/Desktop/baia_mare_profissional.png")
OUT_VTK = Path("/mnt/c/Users/Maria Engracia/Desktop/baia_mare_3d.vtk")
OUT_GIF = Path("/mnt/c/Users/Maria Engracia/Desktop/baia_mare_animacao.gif")

print("Carregando dados SisBaHiA...")
df_nos = pd.read_csv(CSV / "no.csv")
df_cont = pd.read_csv(CSV / "contorno.csv")

nos = df_nos.iloc[:, 1:4].values
contorno = df_cont.iloc[:, 1:3].values

# Delaunay para superfície contínua
tri = Delaunay(nos[:, :2])
triang = Triangulation(nos[:, 0], nos[:, 1], tri.simplices)

# Batimetria real (Z negativo = profundidade)
batimetria = nos[:, 2]

# Centro urbano (Rio de Janeiro - sudoeste da baía)
cx, cy = np.mean(nos[:, 0]), np.mean(nos[:, 1])
ux, uy = cx - 8000, cy - 12000
dist = np.sqrt((nos[:, 0]-ux)**2 + (nos[:, 1]-uy)**2)
C0 = np.exp(-2.0 * (dist/dist.max())**2)

# ============================================================
# FIGURA 1: VISTA DE CIMA PROFISSIONAL (como sua referência)
# ============================================================
print("Gerando imagem profissional...")
fig, axes = plt.subplots(1, 2, figsize=(22, 9))

# Painel 1: Batimetria com contorno
ax1 = axes[0]
tcf1 = ax1.tricontourf(triang, batimetria, levels=30, cmap='terrain_r')
ax1.tricontour(triang, batimetria, levels=15, colors='black', linewidths=0.4, alpha=0.5)
ax1.plot(contorno[:, 0], contorno[:, 1], 'k-', linewidth=2.5)
plt.colorbar(tcf1, ax=ax1, label='Profundidade (m)')
ax1.set_title('Batimetria - Baía de Guanabara', fontsize=15, fontweight='bold')
ax1.set_xlabel('Coordenada X (UTM)', fontsize=11)
ax1.set_ylabel('Coordenada Y (UTM)', fontsize=11)
ax1.set_aspect('equal')
ax1.grid(True, alpha=0.3)

# Painel 2: Concentração de microplásticos com contorno
ax2 = axes[1]
tcf2 = ax2.tripcolor(triang, C0, cmap='viridis', shading='gouraud')
ax2.plot(contorno[:, 0], contorno[:, 1], 'k-', linewidth=2.5)
plt.colorbar(tcf2, ax=ax2, label='Concentração Relativa')
ax2.set_title('Distribuição de Microplásticos - t=0', fontsize=15, fontweight='bold')
ax2.set_xlabel('Coordenada X (UTM)', fontsize=11)
ax2.set_ylabel('Coordenada Y (UTM)', fontsize=11)
ax2.set_aspect('equal')
ax2.grid(True, alpha=0.3)

plt.suptitle('Framework EHD-8L - Baía de Guanabara (Dados SisBaHiA)', 
             fontsize=17, fontweight='bold', y=1.00)
plt.tight_layout()
plt.savefig(OUT_PNG, dpi=200, bbox_inches='tight')
plt.close()
print(f"  OK PNG: {OUT_PNG}")

# ============================================================
# FIGURA 2: ANIMAÇÃO DO CICLO DE MARÉ (12h25min)
# ============================================================
print("Gerando animação do ciclo de maré...")
import matplotlib.animation as animation

PERIODO = 12.42 * 3600  # 12h25min em segundos
N_FRAMES = 60
frames = np.linspace(0, PERIODO, N_FRAMES)

# Correntes de maré (rotacional)
dx = nos[:, 0] - cx
dy = nos[:, 1] - cy
r = np.sqrt(dx**2 + dy**2) + 1e-6
vx_base = -dy / r
vy_base = dx / r

fig_anim, ax_anim = plt.subplots(figsize=(12, 10))
ax_anim.set_xlim(nos[:, 0].min(), nos[:, 0].max())
ax_anim.set_ylim(nos[:, 1].min(), nos[:, 1].max())
ax_anim.set_aspect('equal')
ax_anim.grid(True, alpha=0.3)
ax_anim.set_xlabel('Coordenada X (UTM)')
ax_anim.set_ylabel('Coordenada Y (UTM)')
title = ax_anim.set_title('')

line_contorno, = ax_anim.plot(contorno[:, 0], contorno[:, 1], 'k-', linewidth=2.5)
pcm = ax_anim.tripcolor(triang, C0, cmap='viridis', shading='gouraud')
cb = plt.colorbar(pcm, ax=ax_anim, label='Concentração Relativa')

def animate(i):
    t = frames[i]
    fator = np.sin(2 * np.pi * t / PERIODO)
    # Advecção: deslocar a fonte de poluição com a maré
    desloc_x = vx_base * fator * 3000
    desloc_y = vy_base * fator * 3000
    x_novo = nos[:, 0] + desloc_x
    y_novo = nos[:, 1] + desloc_y
    dist_novo = np.sqrt((x_novo - ux)**2 + (y_novo - uy)**2)
    C_t = np.exp(-2.0 * (dist_novo / dist.max())**2)
    pcm.set_array(C_t)
    hora = t / 3600
    title.set_text(f'Ciclo de Maré - t = {hora:.2f} h (fator maré = {fator:+.2f})')
    return [pcm, title]

anim = animation.FuncAnimation(fig_anim, animate, frames=N_FRAMES, 
                                interval=100, blit=False)
anim.save(OUT_GIF, writer='pillow', fps=10, dpi=100)
plt.close()
print(f"  OK GIF: {OUT_GIF}")

# ============================================================
# FIGURA 3: VTK 3D PARA PARAVIEW (com animação de maré)
# ============================================================
print("Gerando VTK 3D para ParaView...")
num_tri = len(tri.simplices)

with open(OUT_VTK, 'w') as f:
    f.write("# vtk DataFile Version 3.0\n")
    f.write("Baia de Guanabara - 3D com Ciclo de Mare\n")
    f.write("ASCII\n")
    f.write("DATASET UNSTRUCTURED_GRID\n")
    f.write(f"POINTS {len(nos)} float\n")
    for no in nos:
        f.write(f"{no[0]:.2f} {no[1]:.2f} {no[2]:.2f}\n")
    f.write(f"CELLS {num_tri} {num_tri*4}\n")
    for t in tri.simplices:
        f.write(f"3 {t[0]} {t[1]} {t[2]}\n")
    f.write(f"CELL_TYPES {num_tri}\n")
    for _ in range(num_tri):
        f.write("5\n")
    f.write(f"POINT_DATA {len(nos)}\n")
    f.write("SCALARS Batimetria float 1\nLOOKUP_TABLE default\n")
    for z in batimetria:
        f.write(f"{z:.4f}\n")
    f.write("SCALARS Contorno float 1\nLOOKUP_TABLE default\n")
    # Marcar nós de contorno (1) vs interior (0)
    for i in range(len(nos)):
        is_cont = 0.0
        for c in contorno[:200]:  # Amostra
            if abs(nos[i,0]-c[0]) < 1 and abs(nos[i,1]-c[1]) < 1:
                is_cont = 1.0
                break
        f.write(f"{is_cont:.1f}\n")
    for i in range(N_FRAMES):
        t = frames[i]
        fator = np.sin(2 * np.pi * t / PERIODO)
        desloc_x = vx_base * fator * 3000
        desloc_y = vy_base * fator * 3000
        x_novo = nos[:, 0] + desloc_x
        y_novo = nos[:, 1] + desloc_y
        dist_novo = np.sqrt((x_novo - ux)**2 + (y_novo - uy)**2)
        C_t = np.exp(-2.0 * (dist_novo / dist.max())**2)
        f.write(f"SCALARS Concentracao_MP_t{i:02d} float 1\nLOOKUP_TABLE default\n")
        for c in C_t:
            f.write(f"{c:.6f}\n")

print(f"  OK VTK: {OUT_VTK}")

print("\n" + "="*70)
print("✅ TUDO GERADO COM SUCESSO!")
print("="*70)
print(f"\n📁 No Desktop você tem:")
print(f"   1. baia_mare_profissional.png  (imagem de alta qualidade)")
print(f"   2. baia_mare_animacao.gif      (animação do ciclo de maré)")
print(f"   3. baia_mare_3d.vtk            (para abrir no ParaView)")
print(f"\n🎬 No ParaView:")
print(f"   1. File -> Open -> baia_mare_3d.vtk")
print(f"   2. Apply")
print(f"   3. Representation: Surface")
print(f"   4. Coloring: Batimetria (ou Concentracao_MP_t00)")
print(f"   5. CLIQUE NO BOTÃO -Z na barra superior (vista de cima!)")
print(f"   6. Pressione R para resetar a câmera")
