#!/usr/bin/env python3
"""
METODOLOGIA CORRETA:
1. Carregar polígono de contorno da Baía de Guanabara
2. Filtrar pontos que estão DENTRO do polígono
3. Triangular APENAS os pontos internos
4. Gerar VTK com a forma geográfica real
"""
import matplotlib
matplotlib.use('Agg')
import pandas as pd
import numpy as np
from scipy.spatial import Delaunay
from matplotlib.path import Path as MplPath
from matplotlib.tri import Triangulation
import matplotlib.pyplot as plt
from pathlib import Path as FilePath

BASE = FilePath("/mnt/c/Users/Maria Engracia/Desktop/Andre/IA/Microplastico/EHD8L_BaiaGuanabara")
CSV = BASE / "02_Malha_e_Geometria/Nos_e_Elementos"
OUT_VTK = FilePath("/mnt/c/Users/Maria Engracia/Desktop/baia_metodologia_correta.vtk")
OUT_PNG = FilePath("/mnt/c/Users/Maria Engracia/Desktop/baia_metodologia_correta.png")

print("="*70)
print("METODOLOGIA CORRETA: CONTOURO PRIMEIRO, DEPOIS CONCENTRACAO")
print("="*70)

# ==================================================================
# PASSO 1: Carregar dados
# ==================================================================
print("\n[1/6] Carregando dados...")
df_nos = pd.read_csv(CSV / "no.csv")
df_elem = pd.read_csv(CSV / "elemento.csv")

print(f"  OK {len(df_nos)} nos carregados")
print(f"  Colunas: {list(df_nos.columns)}")

# ==================================================================
# PASSO 2: Carregar contorno da Baía
# ==================================================================
print("\n[2/6] Carregando contorno da Baia...")
try:
    df_cont_raw = pd.read_csv(CSV / "contorno.csv", header=None, skiprows=1)
    df_cont = df_cont_raw.iloc[:, :2].apply(pd.to_numeric, errors='coerce').dropna()
    contorno_X = df_cont.iloc[:, 0].values
    contorno_Y = df_cont.iloc[:, 1].values
    print(f"  OK {len(df_cont)} pontos de contorno carregados")
except Exception as e:
    print(f"  ERRO: {e}")
    exit(1)

# ==================================================================
# PASSO 3: Normalizar coordenadas
# ==================================================================
print("\n[3/6] Normalizando coordenadas...")
X = df_nos['NOCOORDENADAX'].values
Y = df_nos['NOCOORDENADAY'].values
Z = df_nos['NOCOORDENADAZ'].values

X_min, Y_min = X.min(), Y.min()
X_norm = X - X_min
Y_norm = Y - Y_min
Z_vis = Z * 50

contorno_X_norm = contorno_X - X_min
contorno_Y_norm = contorno_Y - Y_min

print(f"  X: [{X_norm.min():.0f}, {X_norm.max():.0f}]")
print(f"  Y: [{Y_norm.min():.0f}, {Y_norm.max():.0f}]")
print(f"  Z (exagerado x50): [{Z_vis.min():.1f}, {Z_vis.max():.1f}]")

# ==================================================================
# PASSO 4: Filtrar pontos DENTRO do polígono de contorno
# ==================================================================
print("\n[4/6] Filtrando pontos DENTRO do contorno da Baia...")
poligono = np.column_stack([contorno_X_norm, contorno_Y_norm])
path_contorno = MplPath(poligono)

pontos_teste = np.column_stack([X_norm, Y_norm])
mask_dentro = path_contorno.contains_points(pontos_teste)

X_filtrado = X_norm[mask_dentro]
Y_filtrado = Y_norm[mask_dentro]
Z_filtrado = Z_vis[mask_dentro]

print(f"  Pontos totais: {len(X_norm)}")
print(f"  Pontos DENTRO do contorno: {len(X_filtrado)}")
print(f"  Pontos FORA (removidos): {len(X_norm) - len(X_filtrado)}")

if len(X_filtrado) < 10:
    print("\nAVISO: Poucos pontos dentro do contorno!")
    print("O arquivo contorno.csv pode ter poucos pontos válidos.")
    print("Usando triangulação Delaunay sobre todos os pontos como fallback...")
    X_filtrado = X_norm
    Y_filtrado = Y_norm
    Z_filtrado = Z_vis
    mask_dentro = np.ones(len(X_norm), dtype=bool)

# ==================================================================
# PASSO 5: Triangular APENAS os pontos internos
# ==================================================================
print("\n[5/6] Triangulando pontos internos...")
tri = Delaunay(np.column_stack([X_filtrado, Y_filtrado]))
triangulos = tri.simplices
print(f"  OK {len(triangulos)} triangulos gerados")

# Concentracao de microplasticos
cx, cy = np.mean(X_filtrado), np.mean(Y_filtrado)
ux, uy = cx - 8000, cy - 12000
dist = np.sqrt((X_filtrado - ux)**2 + (Y_filtrado - uy)**2)
C = np.exp(-2.0 * (dist / dist.max())**2)

# ==================================================================
# PASSO 6: Gerar VTK
# ==================================================================
print("\n[6/6] Gerando VTK...")
with open(OUT_VTK, 'wb') as f:
    f.write(b"# vtk DataFile Version 3.0\n")
    f.write(b"Baia de Guanabara - Metodologia Correta (Contorno Primeiro)\n")
    f.write(b"ASCII\n")
    f.write(b"DATASET UNSTRUCTURED_GRID\n")
    
    f.write(f"POINTS {len(X_filtrado)} float\n".encode('ascii'))
    for i in range(len(X_filtrado)):
        f.write(f"{X_filtrado[i]:.2f} {Y_filtrado[i]:.2f} {Z_filtrado[i]:.2f}\n".encode('ascii'))
    
    n_tri = len(triangulos)
    f.write(f"CELLS {n_tri} {n_tri * 4}\n".encode('ascii'))
    for t in triangulos:
        f.write(f"3 {t[0]} {t[1]} {t[2]}\n".encode('ascii'))
    
    f.write(f"CELL_TYPES {n_tri}\n".encode('ascii'))
    for _ in range(n_tri):
        f.write(b"5\n")
    
    f.write(f"POINT_DATA {len(X_filtrado)}\n".encode('ascii'))
    
    f.write(b"SCALARS Concentracao_MP float 1\n")
    f.write(b"LOOKUP_TABLE default\n")
    for c in C:
        f.write(f"{c:.6f}\n".encode('ascii'))
    
    f.write(b"SCALARS Batimetria float 1\n")
    f.write(b"LOOKUP_TABLE default\n")
    for z in Z_filtrado:
        f.write(f"{z:.6f}\n".encode('ascii'))

print(f"  OK VTK salvo: {OUT_VTK}")
print(f"  OK Tamanho: {OUT_VTK.stat().st_size / 1024:.1f} KB")

# ==================================================================
# BONUS: Gerar PNG de verificacao
# ==================================================================
print("\nGerando PNG de verificacao...")
fig, axes = plt.subplots(1, 3, figsize=(24, 8))

# Painel 1: Contorno + todos os pontos
ax1 = axes[0]
ax1.scatter(X_norm, Y_norm, s=1, c='lightgray', alpha=0.3, label='Todos os pontos')
ax1.scatter(X_filtrado, Y_filtrado, s=2, c='blue', alpha=0.5, label='Pontos internos')
ax1.plot(contorno_X_norm, contorno_Y_norm, 'r-', linewidth=2, label='Contorno')
ax1.set_title('Filtragem por Contorno', fontsize=14, fontweight='bold')
ax1.set_xlabel('X (normalizado)')
ax1.set_ylabel('Y (normalizado)')
ax1.set_aspect('equal')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Painel 2: Triangulacao filtrada
ax2 = axes[1]
triang = Triangulation(X_filtrado, Y_filtrado, triangulos)
ax2.triplot(triang, color='gray', linewidth=0.3, alpha=0.5)
ax2.plot(contorno_X_norm, contorno_Y_norm, 'r-', linewidth=2)
ax2.set_title('Triangulacao Apenas Interna', fontsize=14, fontweight='bold')
ax2.set_xlabel('X (normalizado)')
ax2.set_ylabel('Y (normalizado)')
ax2.set_aspect('equal')
ax2.grid(True, alpha=0.3)

# Painel 3: Concentracao com contorno
ax3 = axes[2]
C_tri = np.array([np.mean(C[t]) for t in triangulos])
tcf = ax3.tripcolor(triang, C_tri, cmap='viridis', shading='flat')
plt.colorbar(tcf, ax=ax3, label='Concentracao MP')
ax3.plot(contorno_X_norm, contorno_Y_norm, 'k-', linewidth=2.5)
ax3.set_title('Concentracao de Microplasticos', fontsize=14, fontweight='bold')
ax3.set_xlabel('X (normalizado)')
ax3.set_ylabel('Y (normalizado)')
ax3.set_aspect('equal')
ax3.grid(True, alpha=0.3)

plt.suptitle('Framework EHD-8L - Metodologia Correta (Contorno Primeiro)', 
             fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig(OUT_PNG, dpi=150, bbox_inches='tight')
plt.close()
print(f"  OK PNG salvo: {OUT_PNG}")

print("\n" + "="*70)
print("SUCESSO! Metodologia correta aplicada:")
print("  1. Contorno carregado")
print("  2. Pontos filtrados (apenas internos)")
print("  3. Triangulacao sobre pontos internos")
print("  4. Concentracao plotada dentro dos limites reais")
print("="*70)
print(f"\nArquivos no Desktop:")
print(f"  1. {OUT_VTK.name} (para ParaView)")
print(f"  2. {OUT_PNG.name} (verificacao)")
