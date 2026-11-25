#!/usr/bin/env python3
"""
Gera VTK 3D da Baía de Guanabara com:
- Coordenadas UTM reais (X, Y)
- Batimetria REAL mas EXAGERADA (Z * 100) para visualização
- Vista de cima (como mapa topográfico)
- Contorno nítido via triangulação Delaunay
"""
import pandas as pd
import numpy as np
from scipy.spatial import Delaunay
from pathlib import Path

# CAMINHO REAL
BASE_DIR = Path("/mnt/c/Users/Maria Engracia/Desktop/Andre/IA/Microplastico/EHD8L_BaiaGuanabara")
CSV_DIR = BASE_DIR / "02_Malha_e_Geometria/Nos_e_Elementos"
OUTPUT_PATH = Path("/mnt/c/Users/Maria Engracia/Desktop/baia_guanabara_3d_terrain.vtk")

print("="*70)
print("GERANDO VTK 3D TERRAIN - BAÍA DE GUANABARA")
print("="*70)

# 1. Carregar dados
print("\n[1/5] Carregando malha SisBaHiA...")
df_nos = pd.read_csv(CSV_DIR / "no.csv")
df_elem = pd.read_csv(CSV_DIR / "elemento.csv")
print(f"  OK {len(df_nos)} nos, {len(df_elem)} elementos")

nos = df_nos.iloc[:, 1:4].values
elementos = df_elem.iloc[:, 1:4].values - 1

# 2. NORMALIZAR coordenadas UTM para evitar números gigantes
# Subtrair o mínimo para ter coordenadas começando em 0
x_min = nos[:, 0].min()
y_min = nos[:, 1].min()

print(f"\n[2/5] Normalizando coordenadas UTM...")
print(f"  X: [{x_min:.0f}, {nos[:,0].max():.0f}] -> [0, {nos[:,0].max()-x_min:.0f}]")
print(f"  Y: [{y_min:.0f}, {nos[:,1].max():.0f}] -> [0, {nos[:,1].max()-y_min:.0f}]")

# 3. EXAGERAR batimetria (multiplicar por 100 para visualização)
EXAGERO_Z = 100  # Fator de exagero vertical

print(f"\n[3/5] Aplicando exagero vertical (x{EXAGERO_Z})...")
nos_3d = nos.copy()
nos_3d[:, 0] -= x_min  # Normalizar X
nos_3d[:, 1] -= y_min  # Normalizar Y
nos_3d[:, 2] *= EXAGERO_Z  # Exagerar Z (profundidade)

print(f"  Z (batimetria exagerada): [{nos_3d[:,2].min():.1f}, {nos_3d[:,2].max():.1f}] m")

# 4. Triangulação Delaunay
print("\n[4/5] Triangulação Delaunay...")
points_2d = nos_3d[:, :2]
tri = Delaunay(points_2d)
triangulos = tri.simplices
print(f"  OK {len(triangulos)} triangulos")

# 5. Campo de concentração
print("\n[5/5] Calculando concentracao e exportando...")
centro_x = np.mean(nos_3d[:, 0])
centro_y = np.mean(nos_3d[:, 1])
centro_urbano_x = centro_x - 5000
centro_urbano_y = centro_y - 10000

dist_urbano = np.sqrt((nos_3d[:, 0] - centro_urbano_x)**2 + (nos_3d[:, 1] - centro_urbano_y)**2)
max_dist = np.max(dist_urbano)
concentracao = np.exp(-2.0 * (dist_urbano / max_dist)**2)

# Exportar VTK
num_tri = len(triangulos)

with open(OUTPUT_PATH, 'w') as f:
    f.write("# vtk DataFile Version 3.0\n")
    f.write("Baia de Guanabara - 3D Terrain com Exagero Vertical\n")
    f.write("ASCII\n")
    f.write("DATASET UNSTRUCTURED_GRID\n")
    
    # Nós
    f.write(f"POINTS {len(nos_3d)} float\n")
    for no in nos_3d:
        f.write(f"{no[0]:.2f} {no[1]:.2f} {no[2]:.2f}\n")
    
    # Triângulos
    f.write(f"CELLS {num_tri} {num_tri * 4}\n")
    for tri_elem in triangulos:
        f.write(f"3 {tri_elem[0]} {tri_elem[1]} {tri_elem[2]}\n")
    
    # Tipos
    f.write(f"CELL_TYPES {num_tri}\n")
    for _ in range(num_tri):
        f.write("5\n")
    
    # Concentração
    f.write(f"POINT_DATA {len(nos_3d)}\n")
    f.write("SCALARS Concentracao_Microplasticos float 1\n")
    f.write("LOOKUP_TABLE default\n")
    for c in concentracao:
        f.write(f"{c:.6f}\n")

print(f"\nOK SUCESSO! Arquivo: {OUTPUT_PATH}")
print(f"   Tamanho: {OUTPUT_PATH.stat().st_size / 1024:.1f} KB")
print("\nNo ParaView:")
print("   1. File -> Open -> baia_guanabara_3d_terrain.vtk")
print("   2. Apply")
print("   3. Representation: Surface")
print("   4. Coloring: Concentracao_Microplasticos")
print("   5. Clique no botao +Z (vista de cima) na barra superior")
