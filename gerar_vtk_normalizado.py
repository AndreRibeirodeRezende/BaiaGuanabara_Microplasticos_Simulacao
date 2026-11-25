#!/usr/bin/env python3
import pandas as pd
import numpy as np
from scipy.spatial import Delaunay
from pathlib import Path

BASE = Path("/mnt/c/Users/Maria Engracia/Desktop/Andre/IA/Microplastico/EHD8L_BaiaGuanabara")
CSV = BASE / "02_Malha_e_Geometria/Nos_e_Elementos"
OUT = Path("/mnt/c/Users/Maria Engracia/Desktop/baia_normalizado.vtk")

print("Carregando dados...")
df_nos = pd.read_csv(CSV / "no.csv")
df_elem = pd.read_csv(CSV / "elemento.csv")

X = df_nos['NOCOORDENADAX'].values
Y = df_nos['NOCOORDENADAY'].values
Z = df_nos['NOCOORDENADAZ'].values

# NORMALIZAR: subtrair mínimo para ter valores pequenos (0-50000)
X_min = X.min()
Y_min = Y.min()
X_norm = X - X_min
Y_norm = Y - Y_min

# Exagero vertical
Z_vis = Z * 100

print(f"X original: [{X.min():.0f}, {X.max():.0f}]")
print(f"X normalizado: [{X_norm.min():.0f}, {X_norm.max():.0f}]")
print(f"Y original: [{Y.min():.0f}, {Y.max():.0f}]")
print(f"Y normalizado: [{Y_norm.min():.0f}, {Y_norm.max():.0f}]")
print(f"Z exagerado: [{Z_vis.min():.1f}, {Z_vis.max():.1f}]")

tri = Delaunay(np.column_stack([X_norm, Y_norm]))
triangulos = tri.simplices

cx, cy = np.mean(X_norm), np.mean(Y_norm)
ux, uy = cx - 8000, cy - 12000
dist = np.sqrt((X_norm - ux)**2 + (Y_norm - uy)**2)
C = np.exp(-2.0 * (dist / dist.max())**2)

print(f"\nNos: {len(X)}, Triangulos: {len(triangulos)}")

# Escrever VTK com modo binário (LF puro, sem CRLF)
with open(OUT, 'wb') as f:
    f.write(b"# vtk DataFile Version 3.0\n")
    f.write(b"Baia de Guanabara - Coordenadas Normalizadas\n")
    f.write(b"ASCII\n")
    f.write(b"DATASET UNSTRUCTURED_GRID\n")
    
    f.write(f"POINTS {len(X)} float\n".encode('ascii'))
    for i in range(len(X)):
        f.write(f"{X_norm[i]:.2f} {Y_norm[i]:.2f} {Z_vis[i]:.2f}\n".encode('ascii'))
    
    n_tri = len(triangulos)
    f.write(f"CELLS {n_tri} {n_tri * 4}\n".encode('ascii'))
    for t in triangulos:
        f.write(f"3 {t[0]} {t[1]} {t[2]}\n".encode('ascii'))
    
    f.write(f"CELL_TYPES {n_tri}\n".encode('ascii'))
    for _ in range(n_tri):
        f.write(b"5\n")
    
    f.write(f"POINT_DATA {len(X)}\n".encode('ascii'))
    f.write(b"SCALARS Concentracao_MP float 1\n")
    f.write(b"LOOKUP_TABLE default\n")
    for c in C:
        f.write(f"{c:.6f}\n".encode('ascii'))

print(f"\nVTK salvo: {OUT}")
print(f"Tamanho: {OUT.stat().st_size / 1024:.1f} KB")

# Mostrar primeiras linhas
print("\nPrimeiras 5 linhas:")
with open(OUT, 'r') as f:
    for i, linha in enumerate(f):
        if i >= 5:
            break
        print(linha.rstrip())
