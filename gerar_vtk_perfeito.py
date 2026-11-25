#!/usr/bin/env python3
import pandas as pd
import numpy as np
from scipy.spatial import Delaunay
from pathlib import Path

BASE = Path("/mnt/c/Users/Maria Engracia/Desktop/Andre/IA/Microplastico/EHD8L_BaiaGuanabara")
CSV = BASE / "02_Malha_e_Geometria/Nos_e_Elementos"
OUT = Path("/mnt/c/Users/Maria Engracia/Desktop/baia_perfeito.vtk")

print("Carregando dados...")
df_nos = pd.read_csv(CSV / "no.csv")
df_elem = pd.read_csv(CSV / "elemento.csv")

X = df_nos['NOCOORDENADAX'].values
Y = df_nos['NOCOORDENADAY'].values
Z = df_nos['NOCOORDENADAZ'].values

tri = Delaunay(np.column_stack([X, Y]))
triangulos = tri.simplices

cx, cy = np.mean(X), np.mean(Y)
ux, uy = cx - 8000, cy - 12000
dist = np.sqrt((X - ux)**2 + (Y - uy)**2)
C = np.exp(-2.0 * (dist / dist.max())**2)

Z_vis = Z * 100

print(f"Nos: {len(X)}, Triangulos: {len(triangulos)}")

# Abrir arquivo em modo binário para garantir LF puro
with open(OUT, 'wb') as f:
    # HEADER - cada linha termina com \n (LF Unix)
    f.write(b"# vtk DataFile Version 3.0\n")
    f.write(b"Baia de Guanabara\n")
    f.write(b"ASCII\n")
    f.write(b"DATASET UNSTRUCTURED_GRID\n")
    
    # POINTS
    f.write(f"POINTS {len(X)} float\n".encode('ascii'))
    for i in range(len(X)):
        f.write(f"{X[i]:.2f} {Y[i]:.2f} {Z_vis[i]:.2f}\n".encode('ascii'))
    
    # CELLS
    n_tri = len(triangulos)
    f.write(f"CELLS {n_tri} {n_tri * 4}\n".encode('ascii'))
    for t in triangulos:
        f.write(f"3 {t[0]} {t[1]} {t[2]}\n".encode('ascii'))
    
    # CELL_TYPES
    f.write(f"CELL_TYPES {n_tri}\n".encode('ascii'))
    for _ in range(n_tri):
        f.write(b"5\n")
    
    # POINT_DATA
    f.write(f"POINT_DATA {len(X)}\n".encode('ascii'))
    f.write(b"SCALARS Concentracao_MP float 1\n")
    f.write(b"LOOKUP_TABLE default\n")
    for c in C:
        f.write(f"{c:.6f}\n".encode('ascii'))

print(f"\nVTK salvo: {OUT}")
print(f"Tamanho: {OUT.stat().st_size / 1024:.1f} KB")

# Verificar primeiras linhas
print("\nPrimeiras 10 linhas do arquivo:")
with open(OUT, 'r') as f:
    for i, linha in enumerate(f):
        if i >= 10:
            break
        print(repr(linha))
