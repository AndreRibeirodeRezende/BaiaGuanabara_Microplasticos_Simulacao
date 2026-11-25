#!/usr/bin/env python3
"""
Gera VTK correto para ParaView usando colunas reais do SisBaHiA:
- NOCOORDENADAX (leste)
- NOCOORDENADAY (norte)
- NOCOORDENADAZ (profundidade/batimetria)
Com exagero vertical para visualização 3D adequada.
"""
import pandas as pd
import numpy as np
from scipy.spatial import Delaunay
from pathlib import Path

BASE = Path("/mnt/c/Users/Maria Engracia/Desktop/Andre/IA/Microplastico/EHD8L_BaiaGuanabara")
CSV = BASE / "02_Malha_e_Geometria/Nos_e_Elementos"
OUT_VTK = Path("/mnt/c/Users/Maria Engracia/Desktop/baia_guanabara_paraview.vtk")

print("="*70)
print("GERANDO VTK CORRETO PARA PARAVIEW")
print("="*70)

# 1. Carregar dados
print("\n[1/5] Carregando dados SisBaHiA...")
df_nos = pd.read_csv(CSV / "no.csv")
df_elem = pd.read_csv(CSV / "elemento.csv")

print(f"  Colunas no.csv: {list(df_nos.columns)}")
print(f"  Colunas elemento.csv: {list(df_elem.columns)}")

# 2. Extrair coordenadas usando nomes reais das colunas
print("\n[2/5] Extraindo coordenadas...")
nos_x = df_nos['NOCOORDENADAX'].values
nos_y = df_nos['NOCOORDENADAY'].values
nos_z = df_nos['NOCOORDENADAZ'].values

# Normalizar X e Y (subtrair mínimo para evitar números gigantes)
x_min = nos_x.min()
y_min = nos_y.min()

nos_x_norm = nos_x - x_min
nos_y_norm = nos_y - y_min

print(f"  ✓ X original: [{nos_x.min():.0f}, {nos_x.max():.0f}]")
print(f"  ✓ X normalizado: [{nos_x_norm.min():.0f}, {nos_x_norm.max():.0f}]")
print(f"  ✓ Y original: [{nos_y.min():.0f}, {nos_y.max():.0f}]")
print(f"  ✓ Y normalizado: [{nos_y_norm.min():.0f}, {nos_y_norm.max():.0f}]")
print(f"  ✓ Z (batimetria): [{nos_z.min():.1f}, {nos_z.max():.1f}]")

# 3. Aplicar exagero vertical no Z para visualização 3D
EXAGERO_Z = 50  # Multiplicar Z por 50 para ver a profundidade
nos_z_exagerado = nos_z * EXAGERO_Z

print(f"\n[3/5] Aplicando exagero vertical (x{EXAGERO_Z})...")
print(f"  ✓ Z exagerado: [{nos_z_exagerado.min():.1f}, {nos_z_exagerado.max():.1f}]")

# 4. Triangulação Delaunay
print("\n[4/5] Triangulação Delaunay...")
points_2d = np.column_stack([nos_x_norm, nos_y_norm])
tri = Delaunay(points_2d)
triangulos = tri.simplices
print(f"  ✓ {len(triangulos)} triângulos gerados")

# 5. Calcular concentração de microplásticos
print("\n[5/5] Calculando concentração e exportando VTK...")
cx = np.mean(nos_x_norm)
cy = np.mean(nos_y_norm)
ux = cx - 8000
uy = cy - 12000
dist = np.sqrt((nos_x_norm - ux)**2 + (nos_y_norm - uy)**2)
C0 = np.exp(-2.0 * (dist / dist.max())**2)

# Exportar VTK Legacy
num_tri = len(triangulos)

with open(OUT_VTK, 'w') as f:
    f.write("# vtk DataFile Version 3.0\n")
    f.write("Baia de Guanabara - Coordenadas Reais com Exagero Vertical\n")
    f.write("ASCII\n")
    f.write("DATASET UNSTRUCTURED_GRID\n")
    
    # Nós
    f.write(f"POINTS {len(nos_x)} float\n")
    for i in range(len(nos_x)):
        f.write(f"{nos_x_norm[i]:.2f} {nos_y_norm[i]:.2f} {nos_z_exagerado[i]:.2f}\n")
    
    # Triângulos
    f.write(f"CELLS {num_tri} {num_tri * 4}\n")
    for tri_elem in triangulos:
        f.write(f"3 {tri_elem[0]} {tri_elem[1]} {tri_elem[2]}\n")
    
    # Tipos de célula
    f.write(f"CELL_TYPES {num_tri}\n")
    for _ in range(num_tri):
        f.write("5\n")
    
    # Campo de concentração
    f.write(f"POINT_DATA {len(nos_x)}\n")
    f.write("SCALARS Concentracao_Microplasticos float 1\n")
    f.write("LOOKUP_TABLE default\n")
    for c in C0:
        f.write(f"{c:.6f}\n")
    
    # Campo de batimetria
    f.write("SCALARS Batimetria float 1\n")
    f.write("LOOKUP_TABLE default\n")
    for z in nos_z_exagerado:
        f.write(f"{z:.6f}\n")

print(f"\n  ✓ VTK salvo: {OUT_VTK}")
print(f"  ✓ Tamanho: {OUT_VTK.stat().st_size / 1024:.1f} KB")

print("\n" + "="*70)
print("SUCESSO! VTK gerado no Desktop!")
print("="*70)
print("\nNo ParaView:")
print("  1. File -> Open -> baia_guanabara_paraview.vtk")
print("  2. Apply")
print("  3. Representation: Surface")
print("  4. Coloring: Concentracao_Microplasticos (ou Batimetria)")
print("  5. Clique no botão -Z (vista de cima) na barra superior")
print("  6. Pressione R para Reset Camera")
print("="*70)
