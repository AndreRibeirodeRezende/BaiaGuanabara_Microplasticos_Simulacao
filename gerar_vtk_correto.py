#!/usr/bin/env python3
"""
Gera arquivo VTK XML (.vtu) usando a biblioteca VTK oficial do Python.
Garante 100% de compatibilidade com ParaView 6.
"""
import vtk
import pandas as pd
import numpy as np
from pathlib import Path

# CAMINHO REAL (encontrado pelo find)
BASE_DIR = Path("/mnt/c/Users/Maria Engracia/Desktop/Andre/IA/Microplastico/EHD8L_BaiaGuanabara")
CSV_DIR = BASE_DIR / "02_Malha_e_Geometria/Nos_e_Elementos"
OUTPUT_PATH = Path("/mnt/c/Users/Maria Engracia/Desktop/baia_guanabara_correta.vtu")

print("="*70)
print("GERANDO VTK COM BIBLIOTECA VTK OFICIAL")
print("="*70)

# 1. Carregar dados
print("\n[1/5] Carregando malha SisBaHiA...")
df_nos = pd.read_csv(CSV_DIR / "no.csv")
df_elem = pd.read_csv(CSV_DIR / "elemento.csv")
print(f"  ✓ {len(df_nos)} nós, {len(df_elem)} elementos")

nos_2d = df_nos.iloc[:, 1:4].values
elementos_2d = df_elem.iloc[:, 1:4].values - 1

# 2. Extrudar para 3D
print("\n[2/5] Extrudando para 3D...")
PROFUNDIDADE = 10.0
NIVEIS_Z = 3

nos_3d = []
for no in nos_2d:
    x, y = no[0], no[1]
    for k in range(NIVEIS_Z):
        # TROCA DE EIXOS: X mantém, Y vira Z (altura visual), Z vira Y (profundidade)
        z_visual = (y - 7450000) / 100.0
        y_profundidade = -k * PROFUNDIDADE / (NIVEIS_Z - 1)
        nos_3d.append([x, y_profundidade, z_visual])

nos_3d = np.array(nos_3d)
print(f"  ✓ {len(nos_3d)} nós 3D")

# 3. Criar elementos (prismas)
print("\n[3/5] Criando prismas...")
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
print(f"  ✓ {len(elementos_3d)} prismas")

# 4. Campo de concentração
print("\n[4/5] Calculando concentração...")
centro_x = np.mean(nos_3d[:, 0])
centro_z = np.mean(nos_3d[:, 2])
dist = np.sqrt((nos_3d[:, 0] - centro_x)**2 + (nos_3d[:, 2] - centro_z)**2)
max_dist = np.max(dist)
concentracao = np.exp(-2.0 * (dist / max_dist)**2)

for i, no in enumerate(nos_3d):
    y_prof = no[1]
    concentracao[i] *= (1.0 - 0.5 * (abs(y_prof) / PROFUNDIDADE))

# 5. Criar arquivo VTK usando biblioteca oficial
print("\n[5/5] Gerando arquivo VTK com biblioteca oficial...")

# Criar pontos
points = vtk.vtkPoints()
for no in nos_3d:
    points.InsertNextPoint(no[0], no[1], no[2])

# Criar malha não estruturada
ugrid = vtk.vtkUnstructuredGrid()
ugrid.SetPoints(points)

# Adicionar prismas (VTK_WEDGE = 13)
for elem in elementos_3d:
    wedge = vtk.vtkWedge()
    for i, node_id in enumerate(elem):
        wedge.GetPointIds().SetId(i, node_id)
    ugrid.InsertNextCell(wedge.GetCellType(), wedge.GetPointIds())

# Adicionar campo de concentração
concentration_array = vtk.vtkFloatArray()
concentration_array.SetName("Concentracao_Microplasticos")
concentration_array.SetNumberOfComponents(1)
for c in concentracao:
    concentration_array.InsertNextValue(c)

ugrid.GetPointData().AddArray(concentration_array)

# Escrever arquivo
writer = vtk.vtkXMLUnstructuredGridWriter()
writer.SetFileName(str(OUTPUT_PATH))
writer.SetInputData(ugrid)
writer.Write()

print(f"\n✅ SUCESSO! Arquivo salvo em: {OUTPUT_PATH}")
print(f"   Tamanho: {OUTPUT_PATH.stat().st_size / 1024:.1f} KB")
print("\n🎬 Abra no ParaView: File -> Open -> baia_guanabara_correta.vtu")
print("   Representation: Surface")
print("   Coloring: Concentracao_Microplasticos")
