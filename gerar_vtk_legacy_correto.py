#!/usr/bin/env python3
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path("/mnt/c/Users/Maria Engracia/Desktop/Andre/IA/Microplastico/EHD8L_BaiaGuanabara")
CSV_DIR = BASE_DIR / "02_Malha_e_Geometria/Nos_e_Elementos"
OUTPUT_PATH = Path("/mnt/c/Users/Maria Engracia/Desktop/baia_guanabara_correta.vtk")

print("="*70)
print("GERANDO VTK LEGACY - ORIENTACAO CORRETA")
print("="*70)

print("\n[1/5] Carregando malha SisBaHiA...")
df_nos = pd.read_csv(CSV_DIR / "no.csv")
df_elem = pd.read_csv(CSV_DIR / "elemento.csv")
print(f"  OK {len(df_nos)} nos, {len(df_elem)} elementos")

nos_2d = df_nos.iloc[:, 1:4].values
elementos_2d = df_elem.iloc[:, 1:4].values - 1

x_min = nos_2d[:, 0].min()
y_min = nos_2d[:, 1].min()
print(f"\n[2/5] Normalizando coordenadas...")
print(f"  X: [{x_min:.0f}, {nos_2d[:, 0].max():.0f}]")
print(f"  Y: [{y_min:.0f}, {nos_2d[:, 1].max():.0f}]")

print("\n[3/5] Extrudando para 3D...")
PROFUNDIDADE = 10.0
NIVEIS_Z = 3

nos_3d = []
for no in nos_2d:
    x_norm = no[0] - x_min
    y_norm = no[1] - y_min
    for k in range(NIVEIS_Z):
        z = -k * PROFUNDIDADE / (NIVEIS_Z - 1)
        nos_3d.append([x_norm, y_norm, z])

nos_3d = np.array(nos_3d)
print(f"  OK {len(nos_3d)} nos 3D gerados")

print("\n[4/5] Criando prismas...")
elementos_3d = []
num_nos_2d = len(nos_2d)

for elem in elementos_2d:
    n1, n2, n3 = elem
    for k in range(NIVEIS_Z - 1):
        n1_inf = n1 + k * num_nos_2d
        n2_inf = n2 + k * num_nos_2d
        n3_inf = n3 + k * num_nos_2d
        n1_sup = n1 + (k + 1) * num_nos_2d
        n2_sup = n2 + (k + 1) * num_nos_2d
        n3_sup = n3 + (k + 1) * num_nos_2d
        elementos_3d.append([n1_inf, n2_inf, n3_inf, n1_sup, n2_sup, n3_sup])

elementos_3d = np.array(elementos_3d)
print(f"  OK {len(elementos_3d)} prismas gerados")

print("\n[5/5] Calculando concentracao e exportando...")
centro_x = np.mean(nos_3d[:, 0])
centro_y = np.mean(nos_3d[:, 1])
dist = np.sqrt((nos_3d[:, 0] - centro_x)**2 + (nos_3d[:, 1] - centro_y)**2)
max_dist = np.max(dist)
concentracao = np.exp(-2.0 * (dist / max_dist)**2)

for i, no in enumerate(nos_3d):
    z = no[2]
    concentracao[i] *= (1.0 - 0.5 * (abs(z) / PROFUNDIDADE))

num_elem = len(elementos_3d)

with open(OUTPUT_PATH, 'w') as f:
    f.write("# vtk DataFile Version 3.0\n")
    f.write("Baia de Guanabara - Malha Real SisBaHiA\n")
    f.write("ASCII\n")
    f.write("DATASET UNSTRUCTURED_GRID\n")
    
    f.write(f"POINTS {len(nos_3d)} float\n")
    for no in nos_3d:
        f.write(f"{no[0]:.2f} {no[1]:.2f} {no[2]:.2f}\n")
    
    f.write(f"CELLS {num_elem} {num_elem * 7}\n")
    for elem in elementos_3d:
        f.write(f"6 {elem[0]} {elem[1]} {elem[2]} {elem[3]} {elem[4]} {elem[5]}\n")
    
    f.write(f"CELL_TYPES {num_elem}\n")
    for _ in range(num_elem):
        f.write("13\n")
    
    f.write(f"POINT_DATA {len(nos_3d)}\n")
    f.write("SCALARS Concentracao_Microplasticos float 1\n")
    f.write("LOOKUP_TABLE default\n")
    for c in concentracao:
        f.write(f"{c:.6f}\n")

print(f"\nOK SUCESSO! Arquivo salvo em: {OUTPUT_PATH}")
print(f"   Tamanho: {OUTPUT_PATH.stat().st_size / 1024:.1f} KB")
