#!/usr/bin/env python3
"""
Gera VTK de alta resolução usando a malha REAL do SisBaHiA
CAMINHO CORRIGIDO: /mnt/c/Users/Maria Engracia/Desktop/Andre/IA/Microplastico/EHD8L_BaiaGuanabara/
"""
import pandas as pd
import numpy as np
from pathlib import Path

# ============================================================
# CAMINHO REAL (encontrado pelo find)
# ============================================================
BASE_DIR = Path("/mnt/c/Users/Maria Engracia/Desktop/Andre/IA/Microplastico/EHD8L_BaiaGuanabara")
CSV_DIR = BASE_DIR / "02_Malha_e_Geometria/Nos_e_Elementos"
OUTPUT_DIR = BASE_DIR / "04_OpenFOAM_Case/high_res_vtk"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("="*70)
print("GERANDO VTK REALISTA - BAÍA DE GUANABARA (MALHA SISBAHIA)")
print("="*70)
print(f"\n📂 Lendo CSVs de: {CSV_DIR}")

# Verificar se os arquivos existem
if not CSV_DIR.exists():
    print(f"\n❌ ERRO: Pasta não encontrada: {CSV_DIR}")
    exit(1)

# ==============================================================================
# 1. CARREGAR MALHA REAL DO SISBAHIA
# ==============================================================================
print("\n[1/5] Carregando malha real do SisBaHiA...")

df_nos = pd.read_csv(CSV_DIR / "no.csv")
df_elem = pd.read_csv(CSV_DIR / "elemento.csv")

print(f"  ✓ {len(df_nos)} nós carregados")
print(f"  ✓ {len(df_elem)} elementos carregados")

# Mostrar as primeiras linhas para debug
print(f"\n  📋 Colunas do no.csv: {list(df_nos.columns)}")
print(f"  📋 Colunas do elemento.csv: {list(df_elem.columns)}")
print(f"  📋 Primeiras linhas do no.csv:")
print(df_nos.head())

# Extrair coordenadas - ajustar conforme as colunas reais
# Assumindo que as colunas são posicionais: ID, X, Y, Z
nos_2d = df_nos.iloc[:, 1:4].values  # X, Y, Z
elementos_2d = df_elem.iloc[:, 1:4].values - 1  # Índices base 0

print(f"\n  ✓ Coordenadas extraídas: X=[{nos_2d[:,0].min():.0f}, {nos_2d[:,0].max():.0f}]")
print(f"  ✓ Coordenadas extraídas: Y=[{nos_2d[:,1].min():.0f}, {nos_2d[:,1].max():.0f}]")

# ==============================================================================
# 2. EXTRUDAR PARA 3D
# ==============================================================================
print("\n[2/5] Extrudando malha 2D para 3D...")

PROFUNDIDADE = 10.0
NIVEIS_Z = 5

nos_3d = []
for no in nos_2d:
    x, y = no[0], no[1]
    for k in range(NIVEIS_Z):
        z = k * PROFUNDIDADE / (NIVEIS_Z - 1)
        nos_3d.append([x, y, z])

nos_3d = np.array(nos_3d)
print(f"  ✓ {len(nos_3d)} nós 3D gerados")

# ==============================================================================
# 3. CRIAR ELEMENTOS 3D (Prismas)
# ==============================================================================
print("\n[3/5] Criando elementos 3D...")

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
print(f"  ✓ {len(elementos_3d)} prismas gerados")

# ==============================================================================
# 4. GERAR CAMPO DE CONCENTRAÇÃO
# ==============================================================================
print("\n[4/5] Gerando campo de concentração...")

centro_x = np.mean(nos_3d[:, 0])
centro_y = np.mean(nos_3d[:, 1])
dist = np.sqrt((nos_3d[:, 0] - centro_x)**2 + (nos_3d[:, 1] - centro_y)**2)
max_dist = np.max(dist)
concentracao = np.exp(-2.0 * (dist / max_dist)**2)

for i, no in enumerate(nos_3d):
    z = no[2]
    fator_vertical = 1.0 - 0.5 * (z / PROFUNDIDADE)
    concentracao[i] *= fator_vertical

print(f"  ✓ Concentração: min={concentracao.min():.3f}, max={concentracao.max():.3f}")

# ==============================================================================
# 5. EXPORTAR PARA VTK
# ==============================================================================
print("\n[5/5] Exportando para VTK...")

vtk_path = OUTPUT_DIR / "baia_guanabara_realista.vtk"

with open(vtk_path, 'w') as f:
    f.write("# vtk DataFile Version 3.0\n")
    f.write("Baia de Guanabara - Malha Real SisBaHiA Extrudada\n")
    f.write("ASCII\n")
    f.write("DATASET UNSTRUCTURED_GRID\n")
    
    f.write(f"POINTS {len(nos_3d)} float\n")
    for no in nos_3d:
        f.write(f"{no[0]:.2f} {no[1]:.2f} {no[2]:.2f}\n")
    
    num_elem = len(elementos_3d)
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

print(f"  ✓ Arquivo VTK gerado: {vtk_path}")
print(f"  ✓ Tamanho: {vtk_path.stat().st_size / 1024:.1f} KB")

print("\n" + "="*70)
print("✅ VTK REALISTA GERADO COM SUCESSO!")
print("="*70)
