#!/usr/bin/env python3
"""
Gera visualização 3D da Baía de Guanabara com:
- Batimetria real (profundidade dos nós SisBaHiA)
- Contorno nítido via triangulação Delaunay
- Transporte de microplásticos em ciclo de maré (12h25min)
- Múltiplos time steps para animação no ParaView
"""
import pandas as pd
import numpy as np
from scipy.spatial import Delaunay
from pathlib import Path
import time

# CAMINHO REAL (encontrado pelo find)
BASE_DIR = Path("/mnt/c/Users/Maria Engracia/Desktop/Andre/IA/Microplastico/EHD8L_BaiaGuanabara")
CSV_DIR = BASE_DIR / "02_Malha_e_Geometria/Nos_e_Elementos"
OUTPUT_DIR = BASE_DIR / "04_OpenFOAM_Case/visualizacao_3d_mare"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("="*70)
print("GERANDO VISUALIZAÇÃO 3D - BAÍA DE GUANABARA COM CICLO DE MARÉ")
print("="*70)

# ==============================================================================
# 1. CARREGAR DADOS REAIS DO SISBAHIA
# ==============================================================================
print("\n[1/6] Carregando malha SisBaHiA...")
df_nos = pd.read_csv(CSV_DIR / "no.csv")
df_elem = pd.read_csv(CSV_DIR / "elemento.csv")
print(f"  ✓ {len(df_nos)} nós, {len(df_elem)} elementos")

# Extrair coordenadas (X, Y, Z) - Z é a batimetria (profundidade negativa)
nos = df_nos.iloc[:, 1:4].values
elementos = df_elem.iloc[:, 1:4].values - 1  # Base 0

# Normalizar coordenadas para evitar problemas numéricos
x_min, y_min = nos[:, 0].min(), nos[:, 1].min()
nos_norm = nos.copy()
nos_norm[:, 0] -= x_min
nos_norm[:, 1] -= y_min

print(f"  ✓ Coordenadas normalizadas: X[{nos_norm[:,0].min():.0f}, {nos_norm[:,0].max():.0f}]")
print(f"  ✓ Profundidade: Z[{nos[:,2].min():.1f}, {nos[:,2].max():.1f}] m")

# ==============================================================================
# 2. TRIANGULAÇÃO DELAUNAY (Contorno Nítido)
# ==============================================================================
print("\n[2/6] Triangulação Delaunay...")
points_2d = nos_norm[:, :2]
tri = Delaunay(points_2d)
triangulos = tri.simplices
print(f"  ✓ {len(triangulos)} triângulos gerados")

# ==============================================================================
# 3. SIMULAR CAMPO DE CORRENTES DE MARÉ
# ==============================================================================
print("\n[3/6] Simulando campo de correntes de maré...")

# Período de maré semi-diurna: 12h25min = 44700 segundos
PERIODO_MARE = 12.42 * 3600  # segundos
DURACAO_SIM = PERIODO_MARE  # 1 ciclo completo
NUM_STEPS = 24  # 24 passos (a cada ~31 minutos)
DT = DURACAO_SIM / NUM_STEPS

# Centro da baía (para calcular direção das correntes)
centro_x = np.mean(nos_norm[:, 0])
centro_y = np.mean(nos_norm[:, 1])

# Calcular vetor radial de cada nó ao centro
dx = nos_norm[:, 0] - centro_x
dy = nos_norm[:, 1] - centro_y
r = np.sqrt(dx**2 + dy**2)
r_max = np.max(r)

# Vetor tangencial (corrente rotacional de maré)
# vx = -dy/r, vy = dx/r (rotação anti-horária)
vx_base = -dy / (r + 1e-6)
vy_base = dx / (r + 1e-6)

print(f"  ✓ Período de maré: {PERIODO_MARE/3600:.2f} horas")
print(f"  ✓ {NUM_STEPS} passos de tempo ({DT/60:.1f} min cada)")

# ==============================================================================
# 4. SIMULAR TRANSPORTE DE MICROPLÁSTICOS
# ==============================================================================
print("\n[4/6] Simulando transporte de microplásticos...")

# Concentração inicial: maior no centro urbano (Rio de Janeiro)
# Centro urbano aproximado: região sudoeste da baía
centro_urbano_x = centro_x - 5000  # Deslocado para sudoeste
centro_urbano_y = centro_y - 10000

dist_urbano = np.sqrt((nos_norm[:, 0] - centro_urbano_x)**2 + 
                      (nos_norm[:, 1] - centro_urbano_y)**2)
max_dist = np.max(dist_urbano)

# Concentração inicial (distribuição gaussiana)
C0 = np.exp(-2.0 * (dist_urbano / max_dist)**2)

# Simular advecção ao longo do tempo
C_t = C0.copy()

# ==============================================================================
# 5. EXPORTAR VTK MULTI-STEP
# ==============================================================================
print("\n[5/6] Exportando VTK multi-step...")

# Criar arquivo VTK com múltiplos time steps
vtk_path = OUTPUT_DIR / "baia_guanabara_mare.vtk"

with open(vtk_path, 'w') as f:
    f.write("# vtk DataFile Version 3.0\n")
    f.write("Baia de Guanabara - Ciclo de Mare Completo (12h25min)\n")
    f.write("ASCII\n")
    f.write("DATASET UNSTRUCTURED_GRID\n")
    
    # Escrever nós (uma única vez)
    f.write(f"POINTS {len(nos_norm)} float\n")
    for no in nos_norm:
        # X, Y normalizados, Z = batimetria real (profundidade)
        f.write(f"{no[0]:.2f} {no[1]:.2f} {no[2]:.2f}\n")
    
    # Escrever elementos (triângulos)
    num_tri = len(triangulos)
    f.write(f"CELLS {num_tri} {num_tri * 4}\n")
    for tri in triangulos:
        f.write(f"3 {tri[0]} {tri[1]} {tri[2]}\n")
    
    # Tipos de célula
    f.write(f"CELL_TYPES {num_tri}\n")
    for _ in range(num_tri):
        f.write("5\n")  # 5 = VTK_TRIANGLE
    
    # Dados dos pontos para cada time step
    f.write(f"POINT_DATA {len(nos_norm)}\n")
    
    for step in range(NUM_STEPS):
        t = step * DT
        hora = t / 3600
        
        # Fator de maré (senoidal)
        fator_mare = np.sin(2 * np.pi * t / PERIODO_MARE)
        
        # Campo de velocidade de maré (varia com o tempo)
        vx = vx_base * fator_mare * 0.5  # m/s (amplitude 0.5 m/s)
        vy = vy_base * fator_mare * 0.5
        
        # Advecção simples: deslocar concentração na direção da corrente
        # C(x,t+dt) = C(x - v*dt, t)
        # Aproximação: usar gradiente de concentração
        grad_C_x = np.gradient(C_t, nos_norm[:, 0])
        grad_C_y = np.gradient(C_t, nos_norm[:, 1])
        
        # Atualizar concentração (advecção + difusão)
        difusao = 0.01  # Coeficiente de difusão
        laplaciano = np.gradient(grad_C_x, nos_norm[:, 0]) + np.gradient(grad_C_y, nos_norm[:, 1])
        
        C_t = C_t - (vx * grad_C_x + vy * grad_C_y) * DT + difusao * laplaciano * DT
        C_t = np.clip(C_t, 0, 1)  # Limitar entre 0 e 1
        
        # Escrever campo de concentração
        f.write(f"SCALARS Concentracao_MP_t{step:02d} float 1\n")
        f.write("LOOKUP_TABLE default\n")
        for c in C_t:
            f.write(f"{c:.6f}\n")
        
        # Escrever campo de velocidade (magnitude)
        vel_mag = np.sqrt(vx**2 + vy**2)
        f.write(f"SCALARS Velocidade_Mare_t{step:02d} float 1\n")
        f.write("LOOKUP_TABLE default\n")
        for v in vel_mag:
            f.write(f"{v:.6f}\n")
        
        print(f"  ✓ Step {step:02d}: t={hora:.2f}h, fator_maré={fator_mare:.3f}, C_max={C_t.max():.3f}")

print(f"\n  ✓ Arquivo VTK salvo: {vtk_path}")
print(f"  ✓ Tamanho: {vtk_path.stat().st_size / 1024:.1f} KB")

# ==============================================================================
# 6. RESUMO E INSTRUÇÕES
# ==============================================================================
print("\n" + "="*70)
print("✅ VISUALIZAÇÃO 3D GERADA COM SUCESSO!")
print("="*70)
print(f"\n📂 Arquivo: {vtk_path}")
print(f"📊 Estatísticas:")
print(f"   • Nós: {len(nos_norm):,}")
print(f"   • Triângulos: {num_tri:,}")
print(f"   • Time steps: {NUM_STEPS}")
print(f"   • Duração: {DURACAO_SIM/3600:.2f} horas (1 ciclo de maré)")
print(f"\n🎬 Como abrir no ParaView:")
print(f"   1. Copie para o Windows:")
print(f"      cp {vtk_path} /mnt/c/Users/'Maria Engracia'/Desktop/")
print(f"   2. Abra o ParaView")
print(f"   3. File → Open → baia_guanabara_mare.vtk")
print(f"   4. Apply")
print(f"   5. Representation: Surface")
print(f"   6. Coloring: Concentracao_MP_t00 (ou outro time step)")
print(f"   7. Use o slider de tempo para animar o ciclo de maré!")
print(f"\n🔍 O que você verá:")
print(f"   • Contorno nítido da Baía de Guanabara")
print(f"   • Batimetria real (profundidade nos eixos Z)")
print(f"   • Microplásticos se movendo com as correntes de maré")
print(f"   • Concentração variando ao longo das 12h25min")
print("="*70)
