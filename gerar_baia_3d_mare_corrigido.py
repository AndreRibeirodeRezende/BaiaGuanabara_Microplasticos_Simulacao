#!/usr/bin/env python3
"""
Gera visualização 3D da Baía de Guanabara com ciclo de maré.
Versão corrigida: advecção simplificada para malha não-estruturada.
"""
import pandas as pd
import numpy as np
from scipy.spatial import Delaunay
from pathlib import Path

# CAMINHO REAL (encontrado pelo find)
BASE_DIR = Path("/mnt/c/Users/Maria Engracia/Desktop/Andre/IA/Microplastico/EHD8L_BaiaGuanabara")
CSV_DIR = BASE_DIR / "02_Malha_e_Geometria/Nos_e_Elementos"
OUTPUT_DIR = BASE_DIR / "04_OpenFOAM_Case/visualizacao_3d_mare"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("="*70)
print("GERANDO VISUALIZAÇÃO 3D - BAÍA DE GUANABARA COM CICLO DE MARÉ")
print("="*70)

# 1. Carregar dados
print("\n[1/6] Carregando malha SisBaHiA...")
df_nos = pd.read_csv(CSV_DIR / "no.csv")
df_elem = pd.read_csv(CSV_DIR / "elemento.csv")
print(f"  OK {len(df_nos)} nos, {len(df_elem)} elementos")

nos = df_nos.iloc[:, 1:4].values
elementos = df_elem.iloc[:, 1:4].values - 1

# Normalizar coordenadas
x_min, y_min = nos[:, 0].min(), nos[:, 1].min()
nos_norm = nos.copy()
nos_norm[:, 0] -= x_min
nos_norm[:, 1] -= y_min

print(f"  OK Coordenadas normalizadas")

# 2. Triangulação Delaunay
print("\n[2/6] Triangulação Delaunay...")
points_2d = nos_norm[:, :2]
tri = Delaunay(points_2d)
triangulos = tri.simplices
print(f"  OK {len(triangulos)} triangulos gerados")

# 3. Simular campo de correntes de maré
print("\n[3/6] Simulando campo de correntes de mare...")
PERIODO_MARE = 12.42 * 3600
DURACAO_SIM = PERIODO_MARE
NUM_STEPS = 24
DT = DURACAO_SIM / NUM_STEPS

centro_x = np.mean(nos_norm[:, 0])
centro_y = np.mean(nos_norm[:, 1])

dx = nos_norm[:, 0] - centro_x
dy = nos_norm[:, 1] - centro_y
r = np.sqrt(dx**2 + dy**2)
r_max = np.max(r)

# Vetor tangencial (corrente rotacional)
vx_base = -dy / (r + 1e-6)
vy_base = dx / (r + 1e-6)

print(f"  OK Periodo de mare: {PERIODO_MARE/3600:.2f} horas")
print(f"  OK {NUM_STEPS} passos de tempo")

# 4. Simular transporte de microplásticos
print("\n[4/6] Simulando transporte de microplasticos...")

# Concentração inicial: maior no centro urbano
centro_urbano_x = centro_x - 5000
centro_urbano_y = centro_y - 10000

dist_urbano = np.sqrt((nos_norm[:, 0] - centro_urbano_x)**2 + 
                      (nos_norm[:, 1] - centro_urbano_y)**2)
max_dist = np.max(dist_urbano)

C0 = np.exp(-2.0 * (dist_urbano / max_dist)**2)

# 5. Exportar VTK multi-step
print("\n[5/6] Exportando VTK multi-step...")

vtk_path = OUTPUT_DIR / "baia_guanabara_mare.vtk"

# Armazenar concentrações para cada step
concentracoes = []

for step in range(NUM_STEPS):
    t = step * DT
    hora = t / 3600
    
    # Fator de maré (senoidal)
    fator_mare = np.sin(2 * np.pi * t / PERIODO_MARE)
    
    # Campo de velocidade de maré
    vx = vx_base * fator_mare * 0.5
    vy = vy_base * fator_mare * 0.5
    
    # Advecção simplificada: deslocar concentração na direção da corrente
    # Usar interpolação linear simples
    C_t = C0.copy()
    
    # Deslocar cada nó na direção da corrente
    desloc_x = vx * t
    desloc_y = vy * t
    
    # Nova posição
    x_novo = nos_norm[:, 0] + desloc_x
    y_novo = nos_norm[:, 1] + desloc_y
    
    # Calcular concentração na nova posição (interpolação simples)
    # Usar distância ao centro urbano na posição deslocada
    dist_novo = np.sqrt((x_novo - centro_urbano_x)**2 + (y_novo - centro_urbano_y)**2)
    C_t = np.exp(-2.0 * (dist_novo / max_dist)**2)
    
    # Adicionar difusão simples (suavização)
    if step > 0:
        C_anterior = concentracoes[-1]
        C_t = 0.7 * C_t + 0.3 * C_anterior  # Mistura com estado anterior
    
    C_t = np.clip(C_t, 0, 1)
    concentracoes.append(C_t)
    
    print(f"  OK Step {step:02d}: t={hora:.2f}h, fator_mare={fator_mare:.3f}, C_max={C_t.max():.3f}")

# Escrever arquivo VTK
with open(vtk_path, 'w') as f:
    f.write("# vtk DataFile Version 3.0\n")
    f.write("Baia de Guanabara - Ciclo de Mare Completo (12h25min)\n")
    f.write("ASCII\n")
    f.write("DATASET UNSTRUCTURED_GRID\n")
    
    # Nós
    f.write(f"POINTS {len(nos_norm)} float\n")
    for no in nos_norm:
        f.write(f"{no[0]:.2f} {no[1]:.2f} {no[2]:.2f}\n")
    
    # Elementos (triângulos)
    num_tri = len(triangulos)
    f.write(f"CELLS {num_tri} {num_tri * 4}\n")
    for tri_elem in triangulos:
        f.write(f"3 {tri_elem[0]} {tri_elem[1]} {tri_elem[2]}\n")
    
    # Tipos de célula
    f.write(f"CELL_TYPES {num_tri}\n")
    for _ in range(num_tri):
        f.write("5\n")
    
    # Dados dos pontos para cada time step
    f.write(f"POINT_DATA {len(nos_norm)}\n")
    
    for step, C_t in enumerate(concentracoes):
        f.write(f"SCALARS Concentracao_MP_t{step:02d} float 1\n")
        f.write("LOOKUP_TABLE default\n")
        for c in C_t:
            f.write(f"{c:.6f}\n")

print(f"\n  OK Arquivo VTK salvo: {vtk_path}")
print(f"  OK Tamanho: {vtk_path.stat().st_size / 1024:.1f} KB")

# 6. Resumo
print("\n" + "="*70)
print("OK VISUALIZAÇÃO 3D GERADA COM SUCESSO!")
print("="*70)
print(f"\nArquivo: {vtk_path}")
print(f"Estatísticas:")
print(f"   - Nos: {len(nos_norm):,}")
print(f"   - Triangulos: {num_tri:,}")
print(f"   - Time steps: {NUM_STEPS}")
print(f"   - Duração: {DURACAO_SIM/3600:.2f} horas (1 ciclo de mare)")
print(f"\nComo abrir no ParaView:")
print(f"   1. Copie para o Windows:")
print(f"      cp {vtk_path} /mnt/c/Users/Maria\ Engracia/Desktop/")
print(f"   2. Abra o ParaView")
print(f"   3. File -> Open -> baia_guanabara_mare.vtk")
print(f"   4. Apply")
print(f"   5. Representation: Surface")
print(f"   6. Coloring: Concentracao_MP_t00 (ou outro time step)")
print(f"   7. Use o slider de tempo para animar o ciclo de mare!")
print("="*70)
