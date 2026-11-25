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

X = df_nos['NOCOORDENADAX'].values
Y = df_nos['NOCOORDENADAY'].values
Z = df_nos['NOCOORDENADAZ'].values

# Normalizar coordenadas
X_min, Y_min = X.min(), Y.min()
X_norm = X - X_min
Y_norm = Y - Y_min

# Exagero vertical
Z_vis = Z * 50

print(f"Nos: {len(X)}")
print(f"X: [{X_norm.min():.0f}, {X_norm.max():.0f}]")
print(f"Y: [{Y_norm.min():.0f}, {Y_norm.max():.0f}]")
print(f"Z (exagerado x50): [{Z_vis.min():.1f}, {Z_vis.max():.1f}]")

# Triangulação
tri = Delaunay(np.column_stack([X_norm, Y_norm]))
triangulos = tri.simplices

# Concentração de microplásticos
cx, cy = np.mean(X_norm), np.mean(Y_norm)
ux, uy = cx - 8000, cy - 12000
dist = np.sqrt((X_norm - ux)**2 + (Y_norm - uy)**2)
C = np.exp(-2.0 * (dist / dist.max())**2)

# Carregar contorno com tratamento de erro
print("\nCarregando contorno...")
try:
    df_cont = pd.read_csv(CSV / "contorno.csv", header=None, skiprows=1)
    # Converter para numérico, ignorando erros
    df_cont = df_cont.iloc[:, :2].apply(pd.to_numeric, errors='coerce').dropna()
    contorno_X = df_cont.iloc[:, 0].values - X_min
    contorno_Y = df_cont.iloc[:, 1].values - Y_min
    print(f"Contorno: {len(df_cont)} pontos válidos")
except Exception as e:
    print(f"Aviso: Não foi possível carregar contorno ({e})")
    contorno_X = None
    contorno_Y = None

# Escrever VTK
with open(OUT, 'wb') as f:
    f.write(b"# vtk DataFile Version 3.0\n")
    f.write(b"Baia de Guanabara - Com Contorno\n")
    f.write(b"ASCII\n")
    f.write(b"DATASET UNSTRUCTURED_GRID\n")
    
    # Nós
    f.write(f"POINTS {len(X)} float\n".encode('ascii'))
    for i in range(len(X)):
        f.write(f"{X_norm[i]:.2f} {Y_norm[i]:.2f} {Z_vis[i]:.2f}\n".encode('ascii'))
    
    # Triângulos
    n_tri = len(triangulos)
    f.write(f"CELLS {n_tri} {n_tri * 4}\n".encode('ascii'))
    for t in triangulos:
        f.write(f"3 {t[0]} {t[1]} {t[2]}\n".encode('ascii'))
    
    # Tipos
    f.write(f"CELL_TYPES {n_tri}\n".encode('ascii'))
    for _ in range(n_tri):
        f.write(b"5\n")
    
    # Dados
    f.write(f"POINT_DATA {len(X)}\n".encode('ascii'))
    
    f.write(b"SCALARS Concentracao_MP float 1\n")
    f.write(b"LOOKUP_TABLE default\n")
    for c in C:
        f.write(f"{c:.6f}\n".encode('ascii'))
    
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
print("  4. Coloring: Concentracao_MP ou Batimetria")
print("  5. Clique no botão -Z (vista de cima)")
print("  6. Pressione R (Reset Camera)")
print("  7. Filters -> Alphabetical -> Feature Edges")
print("     -> Marque Boundary Edges, cor preta, Line Width: 3")
