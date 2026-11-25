#!/usr/bin/env python3
"""
Gera VTK com coordenadas UTM REAIS e batimetria REAL do SisBaHiA.
Vista de cima (2D) com contorno nítido da Baía de Guanabara.
"""
import pandas as pd
import numpy as np
from scipy.spatial import Delaunay
from pathlib import Path

# CAMINHO REAL
BASE_DIR = Path("/mnt/c/Users/Maria Engracia/Desktop/Andre/IA/Microplastico/EHD8L_BaiaGuanabara")
CSV_DIR = BASE_DIR / "02_Malha_e_Geometria/Nos_e_Elementos"
# Salvar DIRETAMENTE no Desktop
OUTPUT_PATH = Path("/mnt/c/Users/Maria Engracia/Desktop/baia_guanabara_utm_real.vtk")

print("="*70)
print("GERANDO VTK COM COORDENADAS UTM REAIS + BATIMETRIA REAL")
print("="*70)

# 1. Carregar dados
print("\n[1/5] Carregando malha SisBaHiA...")
df_nos = pd.read_csv(CSV_DIR / "no.csv")
df_elem = pd.read_csv(CSV_DIR / "elemento.csv")
print(f"  OK {len(df_nos)} nos, {len(df_elem)} elementos")

# Extrair coordenadas UTM REAIS (X, Y, Z)
# Z é a batimetria real (profundidade negativa)
nos_utm = df_nos.iloc[:, 1:4].values
elementos = df_elem.iloc[:, 1:4].values - 1

print(f"\n[2/5] Coordenadas UTM reais:")
print(f"  X: [{nos_utm[:,0].min():.0f}, {nos_utm[:,0].max():.0f}]")
print(f"  Y: [{nos_utm[:,1].min():.0f}, {nos_utm[:,1].max():.0f}]")
print(f"  Z (batimetria): [{nos_utm[:,2].min():.1f}, {nos_utm[:,2].max():.1f}] m")

# 3. Triangulação Delaunay (usando apenas X e Y)
print("\n[3/5] Triangulação Delaunay...")
points_2d = nos_utm[:, :2]
tri = Delaunay(points_2d)
triangulos = tri.simplices
print(f"  OK {len(triangulos)} triangulos gerados")

# 4. Campo de concentração de microplásticos
print("\n[4/5] Calculando concentracao de microplasticos...")
centro_x = np.mean(nos_utm[:, 0])
centro_y = np.mean(nos_utm[:, 1])

# Centro urbano (Rio de Janeiro) - sudoeste da baía
centro_urbano_x = centro_x - 5000
centro_urbano_y = centro_y - 10000

dist_urbano = np.sqrt((nos_utm[:, 0] - centro_urbano_x)**2 + 
                      (nos_utm[:, 1] - centro_urbano_y)**2)
max_dist = np.max(dist_urbano)

# Concentração inicial (gaussiana)
concentracao = np.exp(-2.0 * (dist_urbano / max_dist)**2)

# 5. Exportar VTK (triângulos 2D com batimetria real)
print("\n[5/5] Exportando VTK...")

num_tri = len(triangulos)

with open(OUTPUT_PATH, 'w') as f:
    f.write("# vtk DataFile Version 3.0\n")
    f.write("Baia de Guanabara - Coordenadas UTM Reais + Batimetria\n")
    f.write("ASCII\n")
    f.write("DATASET UNSTRUCTURED_GRID\n")
    
    # Nós com coordenadas UTM REAIS e batimetria REAL
    f.write(f"POINTS {len(nos_utm)} float\n")
    for no in nos_utm:
        f.write(f"{no[0]:.2f} {no[1]:.2f} {no[2]:.2f}\n")
    
    # Triângulos
    f.write(f"CELLS {num_tri} {num_tri * 4}\n")
    for tri_elem in triangulos:
        f.write(f"3 {tri_elem[0]} {tri_elem[1]} {tri_elem[2]}\n")
    
    # Tipos de célula
    f.write(f"CELL_TYPES {num_tri}\n")
    for _ in range(num_tri):
        f.write("5\n")
    
    # Campo de concentração
    f.write(f"POINT_DATA {len(nos_utm)}\n")
    f.write("SCALARS Concentracao_Microplasticos float 1\n")
    f.write("LOOKUP_TABLE default\n")
    for c in concentracao:
        f.write(f"{c:.6f}\n")

print(f"\nOK SUCESSO! Arquivo salvo em: {OUTPUT_PATH}")
print(f"   Tamanho: {OUTPUT_PATH.stat().st_size / 1024:.1f} KB")
print("\nComo abrir no ParaView:")
print("   1. Abra o ParaView")
print("   2. File -> Open -> baia_guanabara_utm_real.vtk")
print("   3. Apply")
print("   4. Representation: Surface")
print("   5. Coloring: Concentracao_Microplasticos")
print("   6. Pressione 'R' para Reset Camera (vista de cima)")
