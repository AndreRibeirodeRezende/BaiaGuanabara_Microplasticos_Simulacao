#!/usr/bin/env python3
import pandas as pd
import numpy as np
from scipy.spatial import Delaunay
from pathlib import Path

BASE = Path("/mnt/c/Users/Maria Engracia/Desktop/Andre/IA/Microplastico/EHD8L_BaiaGuanabara")
CSV = BASE / "02_Malha_e_Geometria/Nos_e_Elementos"
OUT = Path("/mnt/c/Users/Maria Engracia/Desktop/baia_com_contorno.vtk")

print("Carregando dados...")
df_nos = pd.read_csv(CSV / "no.csv")
df_elem = pd.read_csv(CSV / "elemento.csv")
df_cont = pd.read_csv(CSV / "contorno.csv")

X = df_nos['NOCOORDENADAX'].values
Y = df_nos['NOCOORDENADAY'].values
Z = df_nos['NOCOORDENADAZ'].values

# Normalizar coordenadas
X_min, Y_min = X.min(), Y.min()
X_norm = X - X_min
Y_norm = Y - Y_min

# Exagero vertical para batimetria ficar visível
Z_vis = Z * 50

print(f"Nos: {len(X)}")
print(f"X: [{X_norm.min():.0f}, {X_norm.max():.0f}]")
print(f"Y: [{Y_norm.min():.0f}, {Y_norm.max():.0f}]")
print(f"Z (exagerado x50): [{Z_vis.min():.1f}, {Z_vis.max():.1f}]")

# Triangulação para superfície
tri = Delaunay(np.column_stack([X_norm, Y_norm]))
triangulos = tri.simplices

# Concentração de microplásticos
cx, cy = np.mean(X_norm), np.mean(Y_norm)
ux, uy = cx - 8000, cy - 12000
dist = np.sqrt((X_norm - ux)**2 + (Y_norm - uy)**2)
C = np.exp(-2.0 * (dist / dist.max())**2)

# Contorno da baía (linhas)
# Pegar pontos únicos do contorno
contorno_pts = df_cont.iloc[:, 1:3].values  # Colunas de coordenadas
contorno_X = contorno_pts[:, 0] - X_min
contorno_Y = contorno_pts[:, 1] - Y_min

print(f"Contorno: {len(contorno_pts)} pontos")

# Escrever VTK com triângulos + linhas de contorno
with open(OUT, 'wb') as f:
    f.write(b"# vtk DataFile Version 3.0\n")
    f.write(b"Baia de Guanabara - Com Contorno Real\n")
    f.write(b"ASCII\n")
    f.write(b"DATASET UNSTRUCTURED_GRID\n")
    
    # Nós
    f.write(f"POINTS {len(X)} float\n".encode('ascii'))
    for i in range(len(X)):
        f.write(f"{X_norm[i]:.2f} {Y_norm[i]:.2f} {Z_vis[i]:.2f}\n".encode('ascii'))
    
    # Triângulos (superfície)
    n_tri = len(triangulos)
    f.write(f"CELLS {n_tri} {n_tri * 4}\n".encode('ascii'))
    for t in triangulos:
        f.write(f"3 {t[0]} {t[1]} {t[2]}\n".encode('ascii'))
    
    # Tipos de célula (triângulos = 5)
    f.write(f"CELL_TYPES {n_tri}\n".encode('ascii'))
    for _ in range(n_tri):
        f.write(b"5\n")
    
    # Dados dos pontos
    f.write(f"POINT_DATA {len(X)}\n".encode('ascii'))
    
    # Campo 1: Concentração de MP
    f.write(b"SCALARS Concentracao_MP float 1\n")
    f.write(b"LOOKUP_TABLE default\n")
    for c in C:
        f.write(f"{c:.6f}\n".encode('ascii'))
    
    # Campo 2: Batimetria
    f.write(b"SCALARS Batimetria float 1\n")
    f.write(b"LOOKUP_TABLE default\n")
    for z in Z_vis:
        f.write(f"{z:.6f}\n".encode('ascii'))

print(f"\nVTK salvo: {OUT}")
print(f"Tamanho: {OUT.stat().st_size / 1024:.1f} KB")
print("\nNo ParaView:")
print("  1. File -> Open -> baia_com_contorno.vtk")
print("  2. Apply")
print("  3. Representation: Surface")
print("  4. Coloring: Concentracao_MP (ou Batimetria)")
print("  5. Clique no botão -Z (vista de cima)")
print("  6. Pressione R (Reset Camera)")
print("  7. Para ver contorno: Filters -> Alphabetical -> Feature Edges")
print("     -> Marque Boundary Edges, cor preta, linha grossa")
