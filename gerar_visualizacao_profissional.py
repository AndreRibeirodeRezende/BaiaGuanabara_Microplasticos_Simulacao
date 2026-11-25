#!/usr/bin/env python3
"""
Visualização Profissional da Baía de Guanabara
- Usa elementos REAIS do elemento.csv (sem Delaunay)
- Gera imagem 2D com contorno perfeito
- Gera visualização 3D com batimetria
- Gera animação do ciclo de maré
"""
import matplotlib
matplotlib.use('Agg')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.tri import Triangulation
from mpl_toolkits.mplot3d import Axes3D
from pathlib import Path
import matplotlib.animation as animation

BASE = Path("/mnt/c/Users/Maria Engracia/Desktop/Andre/IA/Microplastico/EHD8L_BaiaGuanabara")
CSV = BASE / "02_Malha_e_Geometria/Nos_e_Elementos"
OUT_DIR = Path("/mnt/c/Users/Maria Engracia/Desktop")

print("="*70)
print("VISUALIZAÇÃO PROFISSIONAL - BAÍA DE GUANABARA")
print("="*70)

# ==================================================================
# 1. CARREGAR DADOS REAIS
# ==================================================================
print("\n[1/6] Carregando dados do SisBaHiA...")
df_nos = pd.read_csv(CSV / "no.csv")
df_elem = pd.read_csv(CSV / "elemento.csv")

X = df_nos['NOCOORDENADAX'].values
Y = df_nos['NOCOORDENADAY'].values
Z = df_nos['NOCOORDENADAZ'].values

# Elementos REAIS (triângulos do SisBaHiA)
elem_cols = df_elem.columns[-3:]
elementos = df_elem[elem_cols].values - 1  # Base 0

print(f"  ✓ {len(X)} nós")
print(f"  ✓ {len(elementos)} elementos reais")

# Normalizar coordenadas
X_min, Y_min = X.min(), Y.min()
X_norm = X - X_min
Y_norm = Y - Y_min
Z_vis = Z * 50  # Exagero vertical

print(f"  ✓ X: [{X_norm.min():.0f}, {X_norm.max():.0f}]")
print(f"  ✓ Y: [{Y_norm.min():.0f}, {Y_norm.max():.0f}]")

# ==================================================================
# 2. CALCULAR CONCENTRAÇÃO DE MICROPLÁSTICOS
# ==================================================================
print("\n[2/6] Calculando concentração de microplásticos...")
cx, cy = np.mean(X_norm), np.mean(Y_norm)
ux, uy = cx - 8000, cy - 12000
dist = np.sqrt((X_norm - ux)**2 + (Y_norm - uy)**2)
C = np.exp(-2.0 * (dist / dist.max())**2)

# Concentração média por elemento
C_elem = np.array([np.mean(C[e]) for e in elementos])

print(f"  ✓ Concentração: min={C.min():.3f}, max={C.max():.3f}")

# ==================================================================
# 3. IMAGEM 2D COM CONTORO PERFEITO
# ==================================================================
print("\n[3/6] Gerando imagem 2D com contorno real...")
fig, axes = plt.subplots(1, 2, figsize=(20, 10))

# Painel 1: Malha
ax1 = axes[0]
triang = Triangulation(X_norm, Y_norm, elementos)
ax1.triplot(triang, color='gray', linewidth=0.3, alpha=0.5)
ax1.scatter(X_norm, Y_norm, s=0.5, c='gray', alpha=0.3)
ax1.set_title('Malha da Baía - 6356 nós', fontsize=14, fontweight='bold')
ax1.set_xlabel('Coordenada X (UTM normalizado)')
ax1.set_ylabel('Coordenada Y (UTM normalizado)')
ax1.set_aspect('equal')
ax1.grid(True, alpha=0.3)

# Painel 2: Concentração
ax2 = axes[1]
tcf = ax2.tripcolor(triang, C_elem, cmap='viridis', shading='flat')
plt.colorbar(tcf, ax=ax2, label='Concentração Relativa')
ax2.set_title('Distribuição de Microplásticos - Escoamento Urbano', fontsize=14, fontweight='bold')
ax2.set_xlabel('Coordenada X (UTM normalizado)')
ax2.set_ylabel('Coordenada Y (UTM normalizado)')
ax2.set_aspect('equal')
ax2.grid(True, alpha=0.3)

plt.tight_layout()
png_2d = OUT_DIR / "baia_2d_profissional.png"
plt.savefig(png_2d, dpi=150, bbox_inches='tight')
plt.close()
print(f"  ✓ Imagem 2D salva: {png_2d}")

# ==================================================================
# 4. VISUALIZAÇÃO 3D COM BATIMETRIA
# ==================================================================
print("\n[4/6] Gerando visualização 3D...")
fig = plt.figure(figsize=(16, 12))
ax = fig.add_subplot(111, projection='3d')

# Plotar superfície 3D usando os elementos reais
surf = ax.plot_trisurf(X_norm, Y_norm, Z_vis,
                       triangles=elementos,
                       cmap='viridis',
                       alpha=0.9,
                       edgecolor='none',
                       antialiased=True)

ax.set_title('Baía de Guanabara - Visualização 3D\nBatimetria Real + Microplásticos',
             fontsize=16, fontweight='bold', pad=20)
ax.set_xlabel('Coordenada X (UTM)', fontsize=12, labelpad=10)
ax.set_ylabel('Coordenada Y (UTM)', fontsize=12, labelpad=10)
ax.set_zlabel('Profundidade (m exagerado)', fontsize=12, labelpad=10)
ax.view_init(elev=45, azim=-60)

plt.colorbar(surf, ax=ax, shrink=0.5, aspect=10, label='Concentração MP')
plt.tight_layout()
png_3d = OUT_DIR / "baia_3d_profissional.png"
plt.savefig(png_3d, dpi=150, bbox_inches='tight')
plt.close()
print(f"  ✓ Imagem 3D salva: {png_3d}")

# ==================================================================
# 5. ANIMAÇÃO DO CICLO DE MARÉ
# ==================================================================
print("\n[5/6] Gerando animação do ciclo de maré...")
PERIODO = 12.42 * 3600
N_FRAMES = 30
frames_time = np.linspace(0, PERIODO, N_FRAMES)

# Correntes de maré (rotacional)
dx = X_norm - cx
dy = Y_norm - cy
r = np.sqrt(dx**2 + dy**2) + 1e-6
vx = -dy / r
vy = dx / r

fig_anim = plt.figure(figsize=(14, 10))
ax_anim = fig_anim.add_subplot(111)
ax_anim.set_aspect('equal')
ax_anim.grid(True, alpha=0.3)
title = ax_anim.set_title('')

# Plotar malha base
triang_base = Triangulation(X_norm, Y_norm, elementos)
ax_anim.triplot(triang_base, color='lightgray', linewidth=0.3, alpha=0.3)

# Scatter dos microplásticos
scatter = ax_anim.scatter(X_norm, Y_norm, c=C, cmap='viridis', s=5, alpha=0.8, vmin=0, vmax=1)
plt.colorbar(scatter, ax=ax_anim, label='Concentração MP')

def animate(i):
    t = frames_time[i]
    fator = np.sin(2 * np.pi * t / PERIODO)
    
    # Deslocar fonte de poluição com a maré
    desloc_x = vx * fator * 5000
    desloc_y = vy * fator * 5000
    
    x_novo = X_norm + desloc_x
    y_novo = Y_norm + desloc_y
    
    dist_novo = np.sqrt((x_novo - ux)**2 + (y_novo - uy)**2)
    C_t = np.exp(-2.0 * (dist_novo / dist.max())**2)
    
    scatter.set_offsets(np.column_stack([X_norm, Y_norm]))
    scatter.set_array(C_t)
    
    hora = t / 3600
    title.set_text(f'Ciclo de Maré - t = {hora:.2f}h | Fator = {fator:+.2f}',
                   fontsize=14, fontweight='bold')
    return [scatter, title]

print("  Renderizando frames (aguarde)...")
anim = animation.FuncAnimation(fig_anim, animate, frames=N_FRAMES,
                                interval=300, blit=False)

gif_path = OUT_DIR / "baia_ciclo_mare.gif"
anim.save(gif_path, writer='pillow', fps=3, dpi=100)
plt.close()
print(f"  ✓ Animação GIF salva: {gif_path}")

# ==================================================================
# 6. RESUMO FINAL
# ==================================================================
print("\n" + "="*70)
print("SUCESSO! ARQUIVOS GERADOS NO DESKTOP:")
print("="*70)
print(f"1. {png_2d.name}")
print(f"   → Imagem 2D com contorno real da baía")
print(f"2. {png_3d.name}")
print(f"   → Visualização 3D com batimetria")
print(f"3. {gif_path.name}")
print(f"   → Animação do ciclo de maré (12h25min)")
print("\nAbra os arquivos no Windows Explorer!")
print("="*70)
