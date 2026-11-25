#!/usr/bin/env python3
"""
Gera VTK XML (.vtu) com ordem CORRETA de nós para prismas VTK_WEDGE.
Usa coordenadas normalizadas para evitar problemas de precisão.
"""
import pandas as pd
import numpy as np
from pathlib import Path

# CAMINHO REAL
BASE_DIR = Path("/mnt/c/Users/Maria Engracia/Desktop/Andre/IA/Microplastico/EHD8L_BaiaGuanabara")
CSV_DIR = BASE_DIR / "02_Malha_e_Geometria/Nos_e_Elementos"
OUTPUT_PATH = Path("/mnt/c/Users/Maria Engracia/Desktop/baia_guanabara_final.vtu")

print("="*70)
print("GERANDO VTK FINAL - ORDEM CORRETA DE NÓS")
print("="*70)

# Carregar dados
print("\n[1/5] Carregando malha...")
df_nos = pd.read_csv(CSV_DIR / "no.csv")
df_elem = pd.read_csv(CSV_DIR / "elemento.csv")
print(f"  ✓ {len(df_nos)} nós, {len(df_elem)} elementos")

nos_2d = df_nos.iloc[:, 1:4].values
elementos_2d = df_elem.iloc[:, 1:4].values - 1

# NORMALIZAR coordenadas para evitar problemas de precisão no ParaView
# Subtrair o mínimo para ter coordenadas começando em 0
x_min = nos_2d[:, 0].min()
y_min = nos_2d[:, 1].min()

print(f"\n[2/5] Normalizando coordenadas...")
print(f"  ✓ X: [{x_min:.0f}, {nos_2d[:, 0].max():.0f}] -> [0, {nos_2d[:, 0].max() - x_min:.0f}]")
print(f"  ✓ Y: [{y_min:.0f}, {nos_2d[:, 1].max():.0f}] -> [0, {nos_2d[:, 1].max() - y_min:.0f}]")

# Extrudar para 3D
PROFUNDIDADE = 10.0
NIVEIS_Z = 3

nos_3d = []
for no in nos_2d:
    x_norm = no[0] - x_min  # Normalizado
    y_norm = no[1] - y_min  # Normalizado
    for k in range(NIVEIS_Z):
        z = k * PROFUNDIDADE / (NIVEIS_Z - 1)
        nos_3d.append([x_norm, y_norm, z])

nos_3d = np.array(nos_3d)
print(f"  ✓ {len(nos_3d)} nós 3D gerados")

# Criar prismas com ORDEM CORRETA
print("\n[3/5] Criando prismas (ordem VTK_WEDGE correta)...")
elementos_3d = []
num_nos_2d = len(nos_2d)

for elem in elementos_2d:
    n1, n2, n3 = elem
    for k in range(NIVEIS_Z - 1):
        # Base inferior (triângulo)
        n1_inf = n1 + k * num_nos_2d
        n2_inf = n2 + k * num_nos_2d
        n3_inf = n3 + k * num_nos_2d
        # Base superior (triângulo correspondente)
        n1_sup = n1 + (k + 1) * num_nos_2d
        n2_sup = n2 + (k + 1) * num_nos_2d
        n3_sup = n3 + (k + 1) * num_nos_2d
        
        # ORDEM VTK_WEDGE: [n1_inf, n2_inf, n3_inf, n1_sup, n2_sup, n3_sup]
        # Os 3 primeiros são a base, os 3 últimos são o topo
        elementos_3d.append([n1_inf, n2_inf, n3_inf, n1_sup, n2_sup, n3_sup])

elementos_3d = np.array(elementos_3d)
print(f"  ✓ {len(elementos_3d)} prismas gerados")

# Campo de concentração
print("\n[4/5] Calculando concentração...")
centro_x = np.mean(nos_3d[:, 0])
centro_y = np.mean(nos_3d[:, 1])
dist = np.sqrt((nos_3d[:, 0] - centro_x)**2 + (nos_3d[:, 1] - centro_y)**2)
max_dist = np.max(dist)
concentracao = np.exp(-2.0 * (dist / max_dist)**2)

for i, no in enumerate(nos_3d):
    z = no[2]
    concentracao[i] *= (1.0 - 0.5 * (z / PROFUNDIDADE))

# Exportar VTK XML
print("\n[5/5] Exportando .vtu...")
num_elem = len(elementos_3d)

with open(OUTPUT_PATH, 'w') as f:
    f.write('<?xml version="1.0"?>\n')
    f.write('<VTKFile type="UnstructuredGrid" version="0.1" byte_order="LittleEndian">\n')
    f.write('  <UnstructuredGrid>\n')
    f.write(f'    <Piece NumberOfPoints="{len(nos_3d)}" NumberOfCells="{num_elem}">\n')
    
    # Pontos
    f.write('      <Points>\n')
    f.write('        <DataArray type="Float32" NumberOfComponents="3" format="ascii">\n')
    for no in nos_3d:
        f.write(f'          {no[0]:.2f} {no[1]:.2f} {no[2]:.2f}\n')
    f.write('        </DataArray>\n')
    f.write('      </Points>\n')
    
    # Células
    f.write('      <Cells>\n')
    f.write('        <DataArray type="Int32" Name="connectivity" format="ascii">\n')
    for elem in elementos_3d:
        f.write(f'          {elem[0]} {elem[1]} {elem[2]} {elem[3]} {elem[4]} {elem[5]}\n')
    f.write('        </DataArray>\n')
    
    f.write('        <DataArray type="Int32" Name="offsets" format="ascii">\n')
    for i in range(1, num_elem + 1):
        f.write(f'          {i * 6}\n')
    f.write('        </DataArray>\n')
    
    f.write('        <DataArray type="UInt8" Name="types" format="ascii">\n')
    for _ in range(num_elem):
        f.write('          13\n')
    f.write('        </DataArray>\n')
    f.write('      </Cells>\n')
    
    # Dados
    f.write('      <PointData>\n')
    f.write('        <DataArray type="Float32" Name="Concentracao_Microplasticos" format="ascii">\n')
    for c in concentracao:
        f.write(f'          {c:.6f}\n')
    f.write('        </DataArray>\n')
    f.write('      </PointData>\n')
    
    f.write('    </Piece>\n')
    f.write('  </UnstructuredGrid>\n')
    f.write('</VTKFile>\n')

print(f"\n✅ SUCESSO! Arquivo salvo em: {OUTPUT_PATH}")
print(f"   Tamanho: {OUTPUT_PATH.stat().st_size / 1024:.1f} KB")
print("\n🎬 Abra no ParaView: File -> Open -> baia_guanabara_final.vtu")
print("   Depois: View -> Reset Camera (ou pressione 'R')")
