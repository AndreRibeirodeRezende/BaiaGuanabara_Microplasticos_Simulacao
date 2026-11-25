#!/usr/bin/env python3
# ANIMACAO 2 CICLOS DE MARE - EVENTO EXTREMO BAIA DE GUANABARA
# Referencias: Rodrigues et al. (2026), Rosman et al. (2024), Carvalho et al. (2003)
import matplotlib
matplotlib.use('Agg')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from scipy.spatial import Delaunay
from pathlib import Path as FP
import warnings
warnings.filterwarnings('ignore')

BASE = FP("/mnt/c/Users/Maria Engracia/Desktop/Andre/IA/Microplastico/EHD8L_BaiaGuanabara")
CSV = BASE / "02_Malha_e_Geometria/Nos_e_Elementos"
OUT_GIF = FP("/mnt/c/Users/Maria Engracia/Desktop/animacao_2ciclos_mare.gif")

print("Carregando malha SisBaHiA...")
df = pd.read_csv(CSV / "no.csv")
X = df['NOCOORDENADAX'].values
Y = df['NOCOORDENADAY'].values
N = len(X)
print(f"  {N} nos")

print("Triangulando e identificando contorno...")
pts = np.column_stack([X, Y])
tri = Delaunay(pts)
edges = {}
for s in tri.simplices:
    for i in range(3):
        e = tuple(sorted([s[i], s[(i+1)%3]]))
        edges[e] = edges.get(e, 0) + 1
border = sorted(set([n for e,c in edges.items() if c==1 for n in e]))
bX, bY = X[border], Y[border]
cx0, cy0 = np.mean(bX), np.mean(bY)
ang = np.arctan2(bY-cy0, bX-cx0)
o = np.argsort(ang)
bXs, bYs = bX[o], bY[o]
bXc = np.append(bXs, bXs[0])
bYc = np.append(bYs, bYs[0])
print(f"  {len(border)} nos no contorno")

print("Configurando fisica do evento extremo...")
Xb, Yb = 685000, 7455000
Xf, Yf = 680000, 7485000
db = np.sqrt((X-Xb)**2 + (Y-Yb)**2)
df_ = np.sqrt((X-Xf)**2 + (Y-Yf)**2)
W = db / (db + df_)

# Fontes reais (Rodrigues et al. 2026 + Rosman et al. 2024)
# ESEI=4.75 mg/L, ESIca=1.5 mg/L (tratamento 70%), rios=1.0
fontes = [
    (678000,7482000,1.0),(679000,7484000,0.8),(680000,7486000,0.9),
    (681000,7487000,0.7),(682000,7488000,0.6),(683000,7489000,0.5),
    (684000,7490000,0.7),(685000,7491000,0.6),(686000,7490000,0.5),
    (687000,7489000,0.4),(688000,7488000,0.5),(689000,7487000,0.6),
    (668000,7462000,4.75),(687000,7470000,1.5),(665000,7458000,3.0),
    (667000,7461000,0.8),(666000,7460000,0.7),(664000,7459000,0.9),
    (662000,7458000,0.5),(663000,7457000,0.6)
]
hotspots = [(683000,7468000),(684000,7467000),(682000,7472000),
            (681000,7475000),(670000,7463000)]

# Campo base de MP (soma gaussiana das fontes)
MP_base = np.zeros(N)
for xf,yf,c in fontes:
    d = np.sqrt((X-xf)**2 + (Y-yf)**2)
    MP_base += c * np.exp(-0.5*(d/3000)**2)
MP_base = MP_base / MP_base.max()

# Correntes de maré (rotacional, sentido leste segundo Rodrigues et al.)
dx = X - cx0
dy = Y - cy0
r = np.sqrt(dx**2 + dy**2) + 1e-6
vx = -dy/r
vy = dx/r

# Ventos NE (Carvalho et al. 2003): u=+6.7 m/s, v=-2.0 m/s
vento_u = 6.7
vento_v = -2.0

# Perodo de mare semi-diurna: 12h25min
T_MARE = 12.42
N_FRAMES = 60  # 30 frames por ciclo = 2 ciclos completos
tempos = np.linspace(0, 2*T_MARE, N_FRAMES)
print(f"  {N_FRAMES} frames em {2*T_MARE:.2f} horas")

# Coeficiente de absorcao em praias (Rosman et al. 2024): cA=0.05
cA = 0.05

print("Gerando animacao...")
fig, axes = plt.subplots(2, 2, figsize=(16, 14))
fig.suptitle('', fontsize=15, fontweight='bold')

# Contorno em todos os paineis
for ax in axes.flat:
    ax.plot(bXc, bYc, 'k-', linewidth=2.5, zorder=10)
    ax.set_xlim(X.min()-2000, X.max()+2000)
    ax.set_ylim(Y.min()-2000, Y.max()+2000)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xlabel('X (UTM)')
    ax.set_ylabel('Y (UTM)')

# Hotspots no painel 4
for hx,hy in hotspots:
    axes[1,1].plot(hx, hy, 'k*', markersize=16, markeredgecolor='white',
                   markeredgewidth=2, zorder=11)

# Objetos graficos
pT = axes[0,0].scatter(X, Y, c=W, cmap='coolwarm', s=2, vmin=16, vmax=32)
pS = axes[0,1].scatter(X, Y, c=W, cmap='Blues', s=2, vmin=14, vmax=37)
pL = axes[1,0].scatter(X, Y, c=MP_base, cmap='YlOrRd', s=2, vmin=0, vmax=1)
pD = axes[1,1].scatter(X, Y, c=MP_base, cmap='Oranges', s=2, vmin=0, vmax=1)

cb1 = fig.colorbar(pT, ax=axes[0,0], fraction=0.046, pad=0.04, label='T (C)')
cb2 = fig.colorbar(pS, ax=axes[0,1], fraction=0.046, pad=0.04, label='S (psu)')
cb3 = fig.colorbar(pL, ax=axes[1,0], fraction=0.046, pad=0.04, label='MP Leves/Neutros')
cb4 = fig.colorbar(pD, ax=axes[1,1], fraction=0.046, pad=0.04, label='MP Densos')

def update(i):
    t = tempos[i]
    F = np.sin(2*np.pi*t/T_MARE)  # fator de mare
    Fv = 0.7 + 0.3*np.cos(2*np.pi*(t-6)/T_MARE)  # vento NE modulado

    # Penetracao da cunha salina/fria (ACAS) na enchente
    pen = 0.30 * max(0, F) * Fv
    W_ef = np.clip(W - pen, 0, 1)
    Temp = 18.0 + 12.0 * W_ef
    Sal = 36.0 - 21.0 * W_ef

    # MP Leves/Neutros: adveccao por vento + mare
    dx_l = vento_u * Fv * 400 + F * 3000
    dy_l = vento_v * Fv * 200 - F * 2000
    Xl = X + dx_l
    Yl = Y + dy_l
    MPl = np.zeros(N)
    for xf,yf,c in fontes:
        d = np.sqrt((Xl-xf)**2 + (Yl-yf)**2)
        MPl += c * np.exp(-0.5*(d/4000)**2)
    MPl = MPl / MPl.max()
    # Absorcao em praias na vazante
    if F < -0.1:
        MPl = MPl * (1.0 - cA*abs(F))

    # MP Densos: baixa mobilidade (Rodrigues et al. 2026)
    dx_d = F * 800
    dy_d = -F * 600
    Xd = X + dx_d
    Yd = Y + dy_d
    MPd = np.zeros(N)
    for xf,yf,c in fontes:
        d = np.sqrt((Xd-xf)**2 + (Yd-yf)**2)
        MPd += c * np.exp(-0.5*(d/1500)**2)
    MPd = MPd / MPd.max()

    # Atualizar cores
    pT.set_array(Temp)
    pS.set_array(Sal)
    pL.set_array(MPl)
    pD.set_array(MPd)

    ciclo = int(t // T_MARE) + 1
    estado = 'ENCHENTE' if F > 0.1 else ('VAZANTE' if F < -0.1 else 'ESTOFO')
    fig.suptitle(
        f'EVENTO EXTREMO: POS-CHUVA + RESSURGENCIA CABO FRIO | '
        f'CICLO {ciclo}/2 | t={t:.2f}h | Mare: {estado} (F={F:+.2f})',
        fontsize=14, fontweight='bold')
    return [pT, pS, pL, pD]

anim = FuncAnimation(fig, update, frames=N_FRAMES, interval=150, blit=False)
print("Renderizando GIF (aguarde 1-3 minutos)...")
anim.save(OUT_GIF, writer='pillow', fps=6, dpi=90)
plt.close()

print(f"OK Animacao salva: {OUT_GIF}")
print(f"   Tamanho: {OUT_GIF.stat().st_size/1024:.1f} KB")
print(f"   {N_FRAMES} frames em {2*T_MARE:.2f} horas (2 ciclos completos)")
print("\n" + "="*70)
print("ABRA O GIF NO DESKTOP DO WINDOWS!")
print("="*70)
