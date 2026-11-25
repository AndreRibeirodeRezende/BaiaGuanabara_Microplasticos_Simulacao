#!/usr/bin/env python3
"""
Gera VTK com:
- Coordenadas UTM reais no plano horizontal (X, Y)
- Batimetria real como profundidade (Z negativo)
- Triangulação Delaunay para superfície contínua
- Contorno nítido da Baía de Guanabara
"""
import pandas as pd
import numpy as np
from scipy.spatial import Delaunay
from pathlib import Path

# CAMINHO REAL
BASE_DIR = Path("/mnt/c/Users/Maria Engracia/Desktop/Andre/IA/Microplastico/EHD8L_BaiaGuanabara")
CSV_DIR = BASE_DIR / "02_Malha_e_Geometria/Nos_e_Elementos"
OUTPUT_PATH = Path("/mnt/c/Users/Maria Engracia/Desktop/baia_guanabara_correta_final.vtk")

print("="*70)
print("GERANDO VTK FINAL - BAÍA DE GUANABARA (VISTA DE CIMA)")
print("="*70)

# 1. Carregar dados
print("\n[1/5] Carregando malha SisBaHiA...")
df_nos = pd.read_csv(CSV_DIR / "no.csv")
df_elem = pd.read_csv(CSV_DIR / "elemento.csv")
print(f"  OK {len(df_nos)} nos, {len(df_elem)} elementos")

nos = df_nos.iloc[:, 1:4].values
elementos = df_elem.iloc[:, 1:4].values - 1

# 2. Triangulação Delaunay (usando X e Y)
print("\n[2/5] Triangulação Delaunay...")
points_2d = nos[:, :2]
tri = Delaunay(points_2d)
triangulos = tri.simplices
print(f"  OK {len(triangulos)} triangulos gerados")

# 3. Campo de concentração
print("\n[3/5] Calculando concentracao...")
centro_x = np.mean(nos[:, 0])
centro_y = np.mean(nos[:, 1])
centro_urbano_x = centro_x - 5000
centro_urbano_y = centro_y - 10000

dist_urbano = np.sqrt((nos[:, 0] - centro_urbano_x)**2 + (nos[:, 1] - centro_urbano_y)**2)
max_dist = np.max(dist_urbano)
concentracao = np.exp(-2.0 * (dist_urbano / max_dist)**2)

# 4. Exportar VTK
print("\n[4/5] Exportando VTK...")
num_tri = len(triangulos)

with open(OUTPUT_PATH, 'w') as f:
    f.write("# vtk DataFile Version 3.0\n")
    f.write("Baia de Guanabara - Vista de Cima com Batimetria\n")
    f.write("ASCII\n")
    f.write("DATASET UNSTRUCTURED_GRID\n")
    
    # Nós: X, Y (UTM reais), Z (batimetria real, negativa)
    f.write(f"POINTS {len(nos)} float\n")
    for no in nos:
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
    f.write(f"POINT_DATA {len(nos)}\n")
    f.write("SCALARS Concentracao_Microplasticos float 1\n")
    f.write("LOOKUP_TABLE default\n")
    for c in concentracao:
        f.write(f"{c:.6f}\n")

print(f"\nOK SUCESSO! Arquivo: {OUTPUT_PATH}")
print(f"   Tamanho: {OUTPUT_PATH.stat().st_size / 1024:.1f} KB")
