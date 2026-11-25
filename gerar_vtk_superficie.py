#!/usr/bin/env python3
"""
Gera VTK apenas da SUPERFÍCIE SUPERIOR da extrusão.
Mostra a Baía de Guanabara de CIMA (vista planimétrica).
"""
import pandas as pd
import numpy as np
from pathlib import Path

# CAMINHO REAL
BASE_DIR = Path("/mnt/c/Users/Maria Engracia/Desktop/Andre/IA/Microplastico/EHD8L_BaiaGuanabara")
CSV_DIR = BASE_DIR / "02_Malha_e_Geometria/Nos_e_Elementos"
OUTPUT_PATH = Path("/mnt/c/Users/Maria Engracia/Desktop/baia_guanabara_superficie.vtk")

print("="*70)
print("GERANDO VTK DA SUPERFÍCIE SUPERIOR (VISTA DE CIMA)")
print("="*70)

# Carregar dados
print("\n[1/4] Carregando malha...")
df_nos = pd.read_csv(CSV_DIR / "no.csv")
df_elem = pd.read_csv(CSV_DIR / "elemento.csv")
print(f"  ✓ {len(df_nos)} nós, {len(df_elem)} elementos")

nos_2d = df_nos.iloc[:, 1:4].values
elementos_2d = df_elem.iloc[:, 1:4].values - 1

# Normalizar coordenadas
x_min = nos_2d[:, 0].min()
y_min = nos_2d[:, 1].min()

print(f"\n[2/4] Normalizando coordenadas...")
nos_2d[:, 0] -= x_min
nos_2d[:, 1] -= y_min

# Usar apenas a camada SUPERIOR (Z = 10m)
print("\n[3/4] Extraindo superfície superior...")
# A camada superior está nos últimos N nós (onde N = número de nós 2D)
num_nos_2d = len(nos_2d)

# Criar nós da superfície (apenas X, Y, Z=10)
nos_superficie = []
for no in nos_2d:
    nos_superficie.append([no[0], no[1], 10.0])  # Z fixo em 10m

nos_superficie = np.array(nos_superficie)
print(f"  ✓ {len(nos_superficie)} nós da superfície")

# Usar os mesmos triângulos da malha 2D original
elementos_superficie = elementos_2d
print(f"  ✓ {len(elementos_superficie)} triângulos")

# Campo de concentração (mesma lógica)
print("\n[4/4] Calculando concentração e exportando...")
centro_x = np.mean(nos_superficie[:, 0])
centro_y = np.mean(nos_superficie[:, 1])
dist = np.sqrt((nos_superficie[:, 0] - centro_x)**2 + (nos_superficie[:, 1] - centro_y)**2)
max_dist = np.max(dist)
concentracao = np.exp(-2.0 * (dist / max_dist)**2)

# Exportar VTK Legacy (triângulos 2D)
num_elem = len(elementos_superficie)

with open(OUTPUT_PATH, 'w') as f:
    f.write("# vtk DataFile Version 3.0\n")
    f.write("Baia de Guanabara - Superficie Superior (Vista de Cima)\n")
    f.write("ASCII\n")
    f.write("DATASET UNSTRUCTURED_GRID\n")
    
    # Pontos
    f.write(f"POINTS {len(nos_superficie)} float\n")
    for no in nos_superficie:
        f.write(f"{no[0]:.2f} {no[1]:.2f} {no[2]:.2f}\n")
    
    # Células (triângulos = tipo 5 no VTK)
    f.write(f"CELLS {num_elem} {num_elem * 4}\n")
    for elem in elementos_superficie:
        f.write(f"3 {elem[0]} {elem[1]} {elem[2]}\n")
    
    # Tipos de célula
    f.write(f"CELL_TYPES {num_elem}\n")
    for _ in range(num_elem):
        f.write("5\n")  # 5 = VTK_TRIANGLE
    
    # Dados dos pontos
    f.write(f"POINT_DATA {len(nos_superficie)}\n")
    f.write("SCALARS Concentracao_Microplasticos float 1\n")
    f.write("LOOKUP_TABLE default\n")
    for c in concentracao:
        f.write(f"{c:.6f}\n")

print(f"\n✅ SUCESSO! Arquivo salvo em: {OUTPUT_PATH}")
print(f"   Tamanho: {OUTPUT_PATH.stat().st_size / 1024:.1f} KB")
print("\n🎬 Abra no ParaView: File -> Open -> baia_guanabara_superficie.vtk")
print("   Representation: Surface")
print("   Coloring: Concentracao_Microplasticos")
print("   Pressione 'R' para Reset Camera")
