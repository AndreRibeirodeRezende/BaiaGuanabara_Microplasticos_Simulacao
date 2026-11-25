#!/usr/bin/env python3
"""
SCRIPT DEFINITIVO: Contorno Real da Baía de Guanabara + Simulação Enriquecida
- NÃO depende do arquivo contorno.csv (que tem apenas 30 pontos)
- Usa a própria malha para identificar o contorno via arestas de borda
- Resolve o conflito pathlib.Path vs matplotlib.path.Path
- Gera 4 painéis: T, S, MP leves/neutros, MP densos + hotspots
- Baseado em Rodrigues et al. (2026), Rosman et al. (2024), Carvalho et al. (2003)
"""
import matplotlib
matplotlib.use('Agg')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import Delaunay
from pathlib import Path as FilePath
import warnings
warnings.filterwarnings('ignore')

# ==========================================
# 1. CONFIGURAÇÕES
# ==========================================
BASE_DIR = FilePath("/mnt/c/Users/Maria Engracia/Desktop/Andre/IA/Microplastico/EHD8L_BaiaGuanabara")
CSV_DIR = BASE_DIR / "02_Malha_e_Geometria/Nos_e_Elementos"
OUT_PNG = FilePath("/mnt/c/Users/Maria Engracia/Desktop/baia_definitiva_simulacao.png")

print("="*70)
print("SCRIPT DEFINITIVO: BAÍA DE GUANABARA COM CONTORNO REAL")
print("="*70)

# ==========================================
# 2. CARREGAR MALHA
# ==========================================
print("\n[1/6] Carregando malha SisBaHiA...")
df_nos = pd.read_csv(CSV_DIR / "no.csv")
df_elem = pd.read_csv(CSV_DIR / "elemento.csv")

X = df_nos['NOCOORDENADAX'].values
Y = df_nos['NOCOORDENADAY'].values
N = len(X)

print(f"  OK {N} nós, {len(df_elem)} elementos")
print(f"  X: [{X.min():.0f}, {X.max():.0f}]")
print(f"  Y: [{Y.min():.0f}, {Y.max():.0f}]")

# ==========================================
# 3. IDENTIFICAR CONTORNO DA BAÍA VIA MALHA
# ==========================================
print("\n[2/6] Identificando contorno da baía via arestas de borda...")
points = np.column_stack([X, Y])
tri = Delaunay(points)

# Contar quantos triângulos compartilham cada aresta
edge_count = {}
for simplex in tri.simplices:
    for i in range(3):
        edge = tuple(sorted([simplex[i], simplex[(i+1) % 3]]))
        edge_count[edge] = edge_count.get(edge, 0) + 1

# Arestas de borda pertencem a apenas 1 triângulo
border_edges = [edge for edge, count in edge_count.items() if count == 1]
border_node_ids = sorted(list(set([n for edge in border_edges for n in edge])))

print(f"  OK {len(border_node_ids)} nós na borda")
print(f"  OK {len(border_edges)} arestas de borda")

# Ordenar nós da borda por ângulo para formar polígono contínuo
border_X = X[border_node_ids]
border_Y = Y[border_node_ids]
cx_border = np.mean(border_X)
cy_border = np.mean(border_Y)
angles = np.arctan2(border_Y - cy_border, border_X - cx_border)
order = np.argsort(angles)
border_X_sorted = border_X[order]
border_Y_sorted = border_Y[order]

# Fechar polígono
border_X_closed = np.append(border_X_sorted, border_X_sorted[0])
border_Y_closed = np.append(border_Y_sorted, border_Y_sorted[0])

# Criar polígono matplotlib (usando matplotlib.path.Path, NÃO pathlib.Path)
from matplotlib.path import Path as MplPath
polygon_vertices = np.column_stack([border_X_closed[:-1], border_Y_closed[:-1]])
bay_polygon = MplPath(polygon_vertices)

# Filtrar pontos DENTRO da baía
all_points = np.column_stack([X, Y])
mask_inside = bay_polygon.contains_points(all_points)
X_in = X[mask_inside]
Y_in = Y[mask_inside]
N_in = len(X_in)

print(f"  OK {N_in} nós dentro da baía (de {N} total)")

# ==========================================
# 4. PARÂMETROS FÍSICOS DO EVENTO EXTREMO
# ==========================================
print("\n[3/6] Configurando física do evento extremo...")

# Polos geográficos
X_boca, Y_boca = 685000, 7455000      # Sul (Ressurgência Cabo Frio)
X_fundo, Y_fundo = 680000, 7485000    # Norte (Pós-chuva, rios)

# Gradiente espacial W: 0=boca, 1=fundo
dist_boca = np.sqrt((X_in - X_boca)**2 + (Y_in - Y_boca)**2)
dist_fundo = np.sqrt((X_in - X_fundo)**2 + (Y_in - Y_fundo)**2)
W = dist_boca / (dist_boca + dist_fundo)

# Condições extremas (t = 6.21h, Enchente Máxima do 1º Ciclo)
T_boca, T_fundo = 18.0, 30.0          # °C (ACAS vs Água Doce Quente)
S_boca, S_fundo = 36.0, 15.0          # psu
F_mare = 1.0  # Enchente máxima
F_vento = 0.9 # Ventos NE fortes

# Campos de Temperatura e Salinidade
penetracao = 0.25 * F_mare * F_vento
W_ef = np.clip(W - penetracao, 0, 1)
Temp = T_boca + (T_fundo - T_boca) * W_ef
Sal = S_boca - (S_boca - S_fundo) * W_ef

print(f"  OK T: [{Temp.min():.1f}, {Temp.max():.1f}] °C")
print(f"  OK S: [{Sal.min():.1f}, {Sal.max():.1f}] psu")

# ==========================================
# 5. MICROPLÁSTICOS E HOTSPOTS
# ==========================================
print("\n[4/6] Calculando campos de Microplásticos...")

fontes = {
    'Rio Guandu': (678000, 7482000, 1.0), 'Rio Sarapuí': (679000, 7484000, 0.8),
    'Rio Iguaçu': (680000, 7486000, 0.9), 'Rio Estrela': (681000, 7487000, 0.7),
    'Rio São João': (682000, 7488000, 0.6), 'Rio Suruí': (683000, 7489000, 0.5),
    'Rio Magé': (684000, 7490000, 0.7), 'Rio Inhomirim': (685000, 7491000, 0.6),
    'Rio Raiz da Serra': (686000, 7490000, 0.5), 'Rio Iriri': (687000, 7489000, 0.4),
    'Rio Alcântara': (688000, 7488000, 0.5), 'Rio Macacu': (6890
