#!/usr/bin/env python3
"""
Usa os elementos REAIS do arquivo elemento.csv do SisBaHiA
Sem triangulação Delaunay - preserva a geometria real da baía
"""
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path("/mnt/c/Users/Maria Engracia/Desktop/Andre/IA/Microplastico/EHD8L_BaiaGuanabara")
CSV = BASE / "02_Malha_e_Geometria/Nos_e_Elementos"
OUT = Path("/mnt/c/Users/Maria Engracia/Desktop/baia_elementos_reais.vtk")

print("="*70)
print("GERANDO VTK COM ELEMENTOS REAIS DO SISBAHIA")
print("="*70)

# Carregar dados
print("\n[1/5] Carregando dados...")
df_nos = pd.read_csv(CSV / "no.csv")
df_elem = pd.read_csv(CSV / "elemento.csv")

print(f"  Colunas no.csv: {list(df_nos.columns)}")
print(f"  Colunas elemento.csv: {list(df_elem.columns)}")
print(f"  Primeiras linhas elemento.csv:")
print(df_elem.head())

# Extrair coordenadas
X = df_nos['NOCOORDENADAX'].values
Y = df_nos['NOCOORDENADAY'].values
Z = df_nos['NOCOORDENADAZ'].values

# Normalizar
X_min, Y_min = X.min(), Y.min()
X_norm = X - X_min
Y_norm = Y - Y_min
Z_vis = Z * 50

print(f"\n[2/5] Coordenadas:")
print(f"  X: [{X_norm.min():.0f}, {X_norm.max():.0f}]")
print(f"  Y: [{Y_norm.min():.0f}, {Y_norm.max():.0f}]")
print(f"  Z (exagerado x50): [{Z_vis.min():.1f}, {Z_vis.max():.1f}]")

# Usar elementos REAIS do CSV
print("\n[3/5] Usando elementos reais do elemento.csv...")
# Assumindo que as colunas são: MALID, NONUMERO, NOVERTICE1, NOVERTICE2, NOVERTICE3
# Os índices dos vértices estão nas últimas 3 colunas
elem_cols = df_elem.columns[-3:]  # Últimas 3 colunas
elementos = df_elem[elem_cols].values - 1  # Converter para base 0

print(f"  OK {len(elementos)} elementos reais")
print(f"  Primeiro elemento: {elementos[0]}")

# Concentração de microplásticos
print("\n[4/5] Calculando concentração...")
cx, cy = np.mean(X_norm), np.mean(Y_norm)
ux, uy = cx - 8000, cy - 12000
dist = np.sqrt((X_norm - ux)**2 + (Y_norm - uy)**2)
C = np.exp(-2.0 * (dist / dist.max())**2)

# Gerar VTK
print("\n[5/5] Gerando VTK...")
with open(OUT, 'wb') as f:
    f.write(b"# vtk DataFile Version 3.0\n")
    f.write(b"Baia de Guanabara - Elementos Reais do SisBaHiA\n")
    f.write(b"ASCII\n")
    f.write(b"DATASET UNSTRUCTURED_GRID\n")
    
    # Nós
    f.write(f"POINTS {len(X)} float\n".encode('ascii'))
    for i in range(len(X)):
        f.write(f"{X_norm[i]:.2f} {Y_norm[i]:.2f} {Z_vis[i]:.2f}\n".encode('ascii'))
    
    # Elementos REAIS
    n_elem = len(elementos)
    f.write(f"CELLS {n_elem} {n_elem * 4}\n".encode('ascii'))
    for elem in elementos:
        f.write(f"3 {elem[0]} {elem[1]} {elem[2]}\n".encode('ascii'))
    
    # Tipos
    f.write(f"CELL_TYPES {n_elem}\n".encode('ascii'))
    for _ in range(n_elem):
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

print("\n" + "="*70)
print("SUCESSO! VTK com elementos reais gerado!")
print("="*70)
print("\nNo ParaView:")
print("  1. File -> Open -> baia_elementos_reais.vtk")
print("  2. Apply")
print("  3. Representation: Surface")
print("  4. Coloring: Concentracao_MP")
print("  5. Clique no botão -Z (vista de cima)")
print("  6. Pressione R (Reset Camera)")
print("\nA geometria real da baía será preservada!")
