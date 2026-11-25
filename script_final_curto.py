import matplotlib
matplotlib.use('Agg')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import Delaunay
from pathlib import Path as FP

BASE = FP("/mnt/c/Users/Maria Engracia/Desktop/Andre/IA/Microplastico/EHD8L_BaiaGuanabara")
CSV = BASE / "02_Malha_e_Geometria/Nos_e_Elementos"
OUT = FP("/mnt/c/Users/Maria Engracia/Desktop/baia_final.png")

print("Carregando malha...")
df = pd.read_csv(CSV / "no.csv")
X = df['NOCOORDENADAX'].values
Y = df['NOCOORDENADAY'].values
print(f"  {len(X)} nos")

print("Triangulando...")
pts = np.column_stack([X, Y])
tri = Delaunay(pts)

print("Identificando borda...")
edges = {}
for s in tri.simplices:
    for i in range(3):
        e = tuple(sorted([s[i], s[(i+1)%3]]))
        edges[e] = edges.get(e, 0) + 1
border = sorted(set([n for e,c in edges.items() if c==1 for n in e]))
bX = X[border]
bY = Y[border]
cx, cy = np.mean(bX), np.mean(bY)
ang = np.arctan2(bY-cy, bX-cx)
ord_ = np.argsort(ang)
bXs = bX[ord_]
bYs = bY[ord_]
bXc = np.append(bXs, bXs[0])
bYc = np.append(bYs, bYs[0])
print(f"  {len(border)} nos na borda")

print("Calculando campos...")
Xb, Yb = 685000, 7455000
Xf, Yf = 680000, 7485000
db = np.sqrt((X-Xb)**2 + (Y-Yb)**2)
df_ = np.sqrt((X-Xf)**2 + (Y-Yf)**2)
W = db / (db + df_)
T = 18.0 + 12.0 * W
S = 36.0 - 21.0 * W

MP = np.zeros(len(X))
fontes = [
    (678000,7482000,1.0),(679000,7484000,0.8),(680000,7486000,0.9),
    (681000,7487000,0.7),(682000,7488000,0.6),(683000,7489000,0.5),
    (684000,7490000,0.7),(685000,7491000,0.6),(686000,7490000,0.5),
    (687000,7489000,0.4),(688000,7488000,0.5),(689000,7487000,0.6),
    (668000,7462000,4.75),(687000,7470000,1.5),(665000,7458000,3.0),
]
for xf,yf,c in fontes:
    d = np.sqrt((X-xf)**2 + (Y-yf)**2)
    MP += c * np.exp(-0.5*(d/3000)**2)
MP = MP / MP.max()

print("Gerando imagem...")
fig, ax = plt.subplots(2, 2, figsize=(20, 18))
fig.suptitle('Baia de Guanabara - Evento Extremo', fontsize=16, fontweight='bold')

ax[0,0].scatter(X, Y, c=T, cmap='coolwarm', s=2, vmin=16, vmax=32)
ax[0,0].plot(bXc, bYc, 'k-', linewidth=3)
ax[0,0].set_title('Temperatura (C)')
ax[0,0].set_aspect('equal')

ax[0,1].scatter(X, Y, c=S, cmap='Blues', s=2, vmin=14, vmax=37)
ax[0,1].plot(bXc, bYc, 'k-', linewidth=3)
ax[0,1].set_title('Salinidade (psu)')
ax[0,1].set_aspect('equal')

ax[1,0].scatter(X, Y, c=MP, cmap='YlOrRd', s=2, vmin=0, vmax=1)
ax[1,0].plot(bXc, bYc, 'k-', linewidth=3)
ax[1,0].set_title('Microplasticos Leves/Neutros')
ax[1,0].set_aspect('equal')

hotspots = [(683000,7468000),(684000,7467000),(682000,7472000),(681000,7475000),(670000,7463000)]
ax[1,1].scatter(X, Y, c=MP, cmap='Oranges', s=2, vmin=0, vmax=1)
ax[1,1].plot(bXc, bYc, 'k-', linewidth=3)
for hx,hy in hotspots:
    ax[1,1].plot(hx, hy, 'k*', markersize=15, markeredgecolor='white')
ax[1,1].set_title('Microplasticos Densos + Hotspots')
ax[1,1].set_aspect('equal')

plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches='tight')
plt.close()
print(f"OK Salvo: {OUT}")
print(f"Tamanho: {OUT.stat().st_size/1024:.1f} KB")
