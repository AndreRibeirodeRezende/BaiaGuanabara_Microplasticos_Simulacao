#!/usr/bin/env python3
"""
SIMULAÇÃO FINAL ENRIQUECIDA: PÓS-CHUVA + RESSURGÊNCIA DE CABO FRIO
Integra: Rodrigues et al. (2026), Rosman et al. (2024), Carvalho et al. (2003)
Resolve o contorno da Baía de Guanabara usando máscara de polígono.
"""
import matplotlib
matplotlib.use('Agg')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.path import Path as MplPath
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# ==========================================
# 1. CONFIGURAÇÕES E CAMINHOS
# ==========================================
BASE_DIR = Path("/mnt/c/Users/Maria Engracia/Desktop/Andre/IA/Microplastico/EHD8L_BaiaGuanabara")
CSV_DIR = BASE_DIR / "02_Malha_e_Geometria/Nos_e_Elementos"
OUT_PNG = Path("/mnt/c/Users/Maria Engracia/Desktop/simulacao_final_baia.png")

print("="*70)
print("GERANDO SIMULAÇÃO FINAL COM CONTORNO REAL DA BAÍA")
print("="*70)

# ==========================================
# 2. CARREGAR E PROCESSAR DADOS
# ==========================================
print("\n[1/4] Carregando dados e definindo contorno...")
df_nos = pd.read_csv(CSV_DIR / "no.csv")
X = df_nos['NOCOORDENADAX'].values
Y = df_nos['NOCOORDENADAY'].values

# Carregar contorno robustamente
try:
    df_cont = pd.read_csv(CSV_DIR / "contorno.csv", header=None, skiprows=1)
    df_cont = df_cont.iloc[:, :2].apply(pd.to_numeric, errors='coerce').dropna()
    contour_X = df_cont.iloc[:, 0].values
    contour_Y = df_cont.iloc[:, 1].values
    contour_pts = np.column_stack([contour_X, contour_Y])
    
    # Criar polígono e mascarar pontos fora da baía
    poly = MplPath(contour_pts)
    all_pts = np.column_stack([X, Y])
    mask = poly.contains_points(all_pts)
    
    X_in = X[mask]
    Y_in = Y[mask]
    print(f"  OK {len(X_in)} nós dentro do contorno da baía")
except Exception as e:
    print(f"  AVISO: Erro no contorno, usando todos os pontos. {e}")
    X_in, Y_in = X, Y
    contour_X, contour_Y = np.array([]), np.array([])

# ==========================================
# 3. PARÂMETROS FÍSICOS (Baseado nas Referências)
# ==========================================
print("\n[2/4] Configurando física do evento extremo...")
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

# ==========================================
# 4. MICROPLÁSTICOS E HOTSPOTS (Rodrigues & Rosman)
# ==========================================
print("\n[3/4] Calculando campos de Microplásticos...")
fontes = {
    'Rio Guandu': (678000, 7482000, 1.0), 'Rio Sarapuí': (679000, 7484000, 0.8),
    'Rio Iguaçu': (680000, 7486000, 0.9), 'Rio Estrela': (681000, 7487000, 0.7),
    'Rio São João': (682000, 7488000, 0.6), 'Rio Suruí': (683000, 7489000, 0.5),
    'Rio Magé': (684000, 7490000, 0.7), 'Rio Inhomirim': (685000, 7491000, 0.6),
    'Rio Raiz da Serra': (686000, 7490000, 0.5), 'Rio Iriri': (687000, 7489000, 0.4),
    'Rio Alcântara': (688000, 7488000, 0.5), 'Rio Macacu': (689000, 7487000, 0.6),
    'ESEI (Ipanema)': (668000, 7462000, 4.75), 'ESIca (Icaraí)': (687000, 7470000, 1.50),
    'ESBarra (Barra)': (665000, 7458000, 3.00),
    'Jd. Alah': (667000, 7461000, 0.8), 'V. Albuquerque': (666000, 7460000, 0.7),
    'Rocinha/S.Conrado': (664000, 7459000, 0.9), 'Joatinga': (662000, 7458000, 0.5),
    'Sernambetiba': (663000, 7457000, 0.6)
}

hotspots = {
    'Marina da Glória': (683000, 7468000), 'Enseada de Botafogo': (684000, 7467000),
    'Canal do Mangue': (682000, 7472000), 'Canal do Cunha': (681000, 7475000),
    'Praia do Diabo/Forte': (670000, 7463000)
}

# Calcular MP Leves/Neutros (superfície/coluna - maior dispersão)
MP_LN = np.zeros(len(X_in))
for nome, (xf, yf, conc) in fontes.items():
    dist_f = np.sqrt((X_in - xf)**2 + (Y_in - yf)**2)
    MP_LN += conc * np.exp(-0.5 * (dist_f / 4000)**2)
MP_LN = MP_LN / MP_LN.max()

# Calcular MP Densos (fundo - baixa mobilidade, retenção)
MP_D = np.zeros(len(X_in))
for nome, (xf, yf, conc) in fontes.items():
    dist_f = np.sqrt((X_in - xf)**2 + (Y_in - yf)**2)
    MP_D += conc * np.exp(-0.5 * (dist_f / 1500)**2)
MP_D = MP_D / MP_D.max()

# ==========================================
# 5. GERAR VISUALIZAÇÃO
# ==========================================
print("\n[4/4] Gerando figura final...")
fig, axes = plt.subplots(2, 2, figsize=(22, 18))
fig.suptitle('EVENTO EXTREMO: PÓS-CHUVA + RESSURGÊNCIA DE CABO FRIO\n'
             'Enchente Máxima (t=6.21h) - Baseado em Rodrigues et al. (2026), Rosman et al. (2024), Carvalho et al. (2003)',
             fontsize=16, fontweight='bold', y=0.98)

def plotar_painel(ax, dados, cmap, vmin, vmax, titulo, label_cbar, mostrar_hotspots=False):
    # Scatter plot para garantir contorno nítido
    sc = ax.scatter(X_in, Y_in, c=dados, cmap=cmap, s=2, alpha=0.8, vmin=vmin, vmax=vmax)
    # Desenhar contorno real
    if len(contour_X) > 0:
        ax.plot(contour_X, contour_Y, 'k-', linewidth=2.5, zorder=10)
    
    if mostrar_hotspots:
        for nome_hs, (xh, yh) in hotspots.items():
            ax.plot(xh, yh, 'k*', markersize=14, markeredgecolor='white', markeredgewidth=2, zorder=11)
            ax.annotate(nome_hs, (xh, yh), textcoords="offset points", xytext=(10,10),
                        fontsize=9, color='black', fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.8), zorder=12)
    
    ax.set_title(titulo, fontsize=13, fontweight='bold')
    ax.set_xlabel('Coordenada X (UTM)'); ax.set_ylabel('Coordenada Y (UTM)')
    ax.set_aspect('equal'); ax.grid(True, alpha=0.3, linestyle='--')
    plt.colorbar(sc, ax=ax, label=label_cbar, fraction=0.046, pad=0.04)

# Painel 1: Temperatura
plotar_painel(axes[0,0], Temp, 'coolwarm', 16, 32, 
              'Temperatura (°C) - Isoterma 19°C (ACAS)', 'Temperatura (°C)')
axes[0,0].contour(X_in.reshape(int(np.sqrt(len(X_in))), -1), 
                  Y_in.reshape(int(np.sqrt(len(X_in))), -1), 
                  Temp.reshape(int(np.sqrt(len(X_in))), -1), 
                  levels=[19], colors='white', linewidths=2)

# Painel 2: Salinidade
plotar_painel(axes[0,1], Sal, 'Blues', 14, 37, 
              'Salinidade (psu) - Cunhas Salinas', 'Salinidade (psu)')

# Painel 3: MP Leves e Neutros
plotar_painel(axes[1,0], MP_LN, 'YlOrRd', 0, 1, 
              'Microplásticos Leves e Neutros (Superfície/Coluna)\nTransporte por Ventos NE e Correntes', 
              'Concentração Normalizada')

# Painel 4: MP Densos e Hotspots
plotar_painel(axes[1,1], MP_D, 'Oranges', 0, 1, 
              'Microplásticos Densos (Fundo) + Hotspots de Acúmulo (★)\nRetenção próxima às fontes', 
              'Concentração Normalizada', mostrar_hotspots=True)

plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig(OUT_PNG, dpi=150, bbox_inches='tight')
plt.close()

print(f"\nOK Imagem salva: {OUT_PNG}")
print(f"OK Tamanho: {OUT_PNG.stat().st_size / 1024:.1f} KB")
print("\n" + "="*70)
print("SUCESSO! Abra o arquivo no Desktop do Windows.")
print("="*70)
