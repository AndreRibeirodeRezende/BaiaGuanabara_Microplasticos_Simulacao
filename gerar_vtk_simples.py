#!/usr/bin/env python3
import pandas as pd
import numpy as np
from scipy.spatial import Delaunay
from pathlib import Path

BASE = Path("/mnt/c/Users/Maria Engracia/Desktop/Andre/IA/Microplastico/EHD8L_BaiaGuanabara")
CSV = BASE / "02_Malha_e_Geometria/Nos_e_Elementos"
OUT = Path("/mnt/c/Users/Maria Engracia/Desktop/baia_simples.vtk")

print("Carregando dados...")
df_nos = pd.read_csv(CSV / "no.csv")
df_elem = pd.read_csv(CSV / "elemento.csv")

# Colunas REAIS do SisBaHiA
X = df_nos['NOCOORDENADAX'].values  # Leste: 675000-700000
Y = df_nos['NOCOORDENADAY'].values  # Norte: 7.45e6-7.49e6
Z = df_nos['NOCOORDENADAZ'].values  # Batimetria

# Triangulacao
tri = Delaunay(np.column_stack([X, Y]))
triangulos = tri.simplices

# Concentracao
cx, cy = np.mean(X), np.mean(Y)
ux, uy = cx - 8000, cy - 12000
dist = np.sqrt((X - ux)**2 + (Y - uy)**2)
C = np.exp(-2.0 * (dist / dist.max())**2)

# Exagero vertical para Z ficar visivel
Z_vis = Z * 100

print(f"Nos: {len(X)}, Triangulos: {len(triangulos)}")
print(f"X: [{X.min():.0f}, {X.max():.0f}]")
print(f"Y: [{Y.min():.0f}, {Y.max():.0f}]")
print(f"Z: [{Z.min():.1f}, {Z.max():.1f}]")

# Escrever VTK Legacy (formato que JA funcionou antes)
with open(OUT, 'w') as f:
    f.write("# vtk DataFile Version 3.0\n")
    f.write("Baia de Guanabara\n")
    f.write("ASCII\n")
    f.write("DATASET UNSTRUCTURED_GRID\n")
    
    f.write(f"POINTS {len(X)} float\n")
    for i in range(len(X)):
        f.write(f"{X[i]:.2f} {Y[i]:.2f} {Z_vis[i]:.2f}\n")
    
    f.write(f"CELLS {len(triangulos)} {len(triangulos) * 4}\n")
    for t in triangulos:
        f.write(f"3 {t[0]} {t[1]} {t[2]}\n")
    
    f.write(f"CELL_TYPES {len(triangulos)}\n")
    for _ in range(len(triangulos)):
        f.write("5\n")
    
    f.write(f"POINT_DATA {len(X)}\n")
    f.write("SCALARS Concentracao_MP float 1\n")
    f.write("LOOKUP_TABLE default\n")
    for c in C:
        f.write(f"{c:.6f}\n")

print(f"\nVTK salvo: {OUT}")
print(f"Tamanho: {OUT.stat().st_size / 1024:.1f} KB")
