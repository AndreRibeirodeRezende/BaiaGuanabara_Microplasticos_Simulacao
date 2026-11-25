#!/usr/bin/env python3
"""
Simulação Enriquecida: Evento Extremo Pós-Chuva + Ressurgência de Cabo Frio
Baseado em:
- Rodrigues et al. (FluHidros 2026): Fontes reais e 3 classes de flutuabilidade
- Rosman et al. (2024): ESEI/ESIca, hotspots, coeficiente de absorção
- Carvalho et al. (2003): ITR, ventos NE, TSM 18-20°C, isoterma 19°C
"""
import matplotlib
matplotlib.use('Agg')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.tri import Triangulation
from scipy.spatial import Delaunay
from pathlib import Path
import matplotlib.animation as animation
from matplotlib.colors import LinearSegmentedColormap

# ==========================================
# 1. CONFIGURAÇÕES
# ==========================================
BASE_DIR = Path("/mnt/c/Users/Maria Engracia/Desktop/Andre/IA/Microplastico/EHD8L_BaiaGuanabara")
CSV_DIR = BASE_DIR / "02_Malha_e_Geometria/Nos_e_Elementos"
OUT_GIF = Path("/mnt/c/Users/Maria Engracia/Desktop/evento_extremo_enriquecido.gif")
OUT_PNG = Path("/mnt/c/Users/Maria Engracia/Desktop/evento_extremo_enriquecido_resumo.png")

print("="*70)
print("SIMULAÇÃO ENRIQUECIDA: PÓS-CHUVA + RESSURGÊNCIA CABO FRIO")
print("Base: Rodrigues et al. (2026), Rosman et al. (2024), Carvalho et al. (2003)")
print("="*70)

# ==========================================
# 2. CARREGAR MALHA SISBAHIA
# ==========================================
print("\n[1/6] Carregando malha SisBaHiA...")
df_nos = pd.read_csv(CSV_DIR / "no.csv")
X = df_nos['NOCOORDENADAX'].values
Y = df_nos['NOCOORDENADAY'].values
N = len(X)

tri = Delaunay(np.column_stack((X, Y)))
triang = Triangulation(X, Y, tri.simplices)
print(f"  OK {N} nós, {len(tri.simplices)} triângulos")

# ==========================================
# 3. FONTES REAIS DE MICROPLÁSTICOS
# ==========================================
print("\n[2/6] Configurando fontes reais (Rodrigues et al., 2026)...")

# Coordenadas UTM aproximadas das fontes
fontes = {
    # Rios afluentes (fundo da baía) - 12 rios
    'Rio Guandu':       (678000, 7482000, 1.0),
    'Rio Sarapuí':      (679000, 7484000, 0.8),
    'Rio Iguaçu':       (680000, 7486000, 0.9),
    'Rio Estrela':      (681000, 7487000, 0.7),
    'Rio São João':     (682000, 7488000, 0.6),
    'Rio Suruí':        (683000, 7489000, 0.5),
    'Rio Magé':         (684000, 7490000, 0.7),
    'Rio Inhomirim':    (685000, 7491000, 0.6),
    'Rio Raiz da Serra':(686000, 7490000, 0.5),
    'Rio Iriri':        (687000, 7489000, 0.4),
    'Rio Alcântara':    (688000, 7488000, 0.5),
    'Rio Macacu':       (689000, 7487000, 0.6),
    
    # Emissários submarinos (Rosman et al., 2024)
    'ESEI (Ipanema)':   (668000, 7462000, 4.75),  # 4.75 mg/L
    'ESIca (Icaraí)':   (687000, 7470000, 1.50),  # 1.5 mg/L (após tratamento 70%)
    'ESBarra (Barra)':  (665000, 7458000, 3.00),
    
    # Canais urbanos costeiros
    'Jardim de Alah':   (667000, 7461000, 0.8),
    'Visc. Albuquerque':(666000, 7460000, 0.7),
    'Rocinha/S.Conrado':(664000, 7459000, 0.9),
    'Joatinga':         (662000, 7458000, 0.5),
    'Sernambetiba':     (663000, 7457000, 0.6),
}

# Hotspots de acúmulo (Rosman et al., 2024)
hotspots = {
    'Marina da Glória':     (683000, 7468000),
    'Enseada de Botafogo':  (684000, 7467000),
    'Canal do Mangue':      (682000, 7472000),
    'Canal do Cunha':       (681000, 7475000),
    'Praia do Diabo/Forte': (670000, 7463000),
}

print(f"  OK {len(fontes)} fontes configuradas")
print(f"  OK {len(hotspots)} hotspots de acúmulo")

# ==========================================
# 4. PARÂMETROS FÍSICOS DO EVENTO
# ==========================================
print("\n[3/6] Configurando parâmetros físicos...")

# Condições extremas (pós-chuva + ressurgência)
# Fundo da baía: água doce quente (pós-chuva)
T_fundo_baia = 30.0   # °C
S_fundo_baia = 15.0   # psu

# Boca da baía: Água Central do Atlântico Sul (ACAS) - ressurgência
# Carvalho et al. (2003): isoterma 19°C, TSM até 10°C mais fria
T_boca_baia = 18.0    # °C (ACAS)
S_boca_baia = 36.0    # psu

# Polos geográficos
X_boca, Y_boca = 685000, 7455000      # Sul (Cabo Frio)
X_fundo, Y_fundo = 680000, 7485000    # Norte (rios)

# Gradiente espacial W: 0=boca, 1=fundo
dist_boca = np.sqrt((X - X_boca)**2 + (Y - Y_boca)**2)
dist_fundo = np.sqrt((X - X_fundo)**2 + (Y - Y_fundo)**2)
W = dist_boca / (dist_boca + dist_fundo)

# Período de maré e tempo
T_mare = 12.42  # horas
tempo_total = 2 * T_mare  # 2 ciclos = 24.84h
N_FRAMES = 72  # 3 frames por hora
tempos = np.linspace(0, tempo_total, N_FRAMES)

# Ventos de quadrante NE (Carvalho et al., 2003)
# Componente paralela (u) correlacionada com ITR
# Ventos NE: u > 0 (leste), v < 0 (sul) - forçam ressurgência
vento_u_base = 6.7   # m/s (componente paralela, leste)
vento_v_base = -2.0  # m/s (componente longitudinal, sul)

print(f"  OK T fundo: {T_fundo_baia}°C, S: {S_fundo_baia} psu")
print(f"  OK T boca: {T_boca_baia}°C (ACAS), S: {S_boca_baia} psu")
print(f"  OK Ventos NE: u={vento_u_base} m/s, v={vento_v_base} m/s")

# ==========================================
# 5. CAMPO INICIAL DE MICROPLÁSTICOS
# ==========================================
print("\n[4/6] Calculando campos iniciais de MP...")

# Campo base de MP (soma das contribuições das fontes)
MP_base = np.zeros(N)
for nome, (xf, yf, conc) in fontes.items():
    dist_fonte = np.sqrt((X - xf)**2 + (Y - yf)**2)
    sigma = 3000  # dispersão inicial ~3km
    MP_base += conc * np.exp(-0.5 * (dist_fonte / sigma)**2)

# Normalizar para [0, 1]
MP_base = MP_base / MP_base.max()

# 3 classes de flutuabilidade (Rodrigues et al., 2026)
# Leves: superfície, maior dispersão, influenciados por vento
# Neutros: coluna d'água, dispersão intermediária
# Densos: fundo, baixa mobilidade, retenção próxima às fontes
MP_leves = MP_base.copy()
MP_neutros = MP_base.copy()
MP_densos = MP_base.copy()

print(f"  OK MP base: max={MP_base.max():.3f}")

# ==========================================
# 6. FUNÇÃO DE ANIMAÇÃO
# ==========================================
print("\n[5/6] Renderizando animação (2-3 minutos)...")

fig, axes = plt.subplots(2, 2, figsize=(20, 16))
fig.suptitle('', fontsize=16, fontweight='bold', y=0.98)

# Configurar eixos
for ax in axes.flat:
    ax.set_xlim(X.min() - 3000, X.max() + 3000)
    ax.set_ylim(Y.min() - 3000, Y.max() + 3000)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3, linestyle='--')

# Títulos dos painéis
axes[0,0].set_title('Hidrodinâmica: Temperatura (°C)', fontsize=13, fontweight='bold')
axes[0,1].set_title('Hidrodinâmica: Salinidade (psu)', fontsize=13, fontweight='bold')
axes[1,0].set_title('MP Leves + Neutros (superfície/coluna)', fontsize=13, fontweight='bold')
axes[1,1].set_title('MP Densos (fundo) + Hotspots', fontsize=13, fontweight='bold')

# Marcar hotspots
for ax in [axes[1,1]]:
    for nome_hs, (xh, yh) in hotspots.items():
        ax.plot(xh, yh, 'k*', markersize=12, markeredgecolor='white', markeredgewidth=1.5)

# Marcar fontes
for ax in axes.flat:
    for nome_f, (xf, yf, _) in fontes.items():
        if 'Rio' in nome_f:
            ax.plot(xf, yf, 'b^', markersize=6, alpha=0.6)
        elif 'ESEI' in nome_f or 'ESIca' in nome_f or 'ESBarra' in nome_f:
            ax.plot(xf, yf, 'rs', markersize=8, alpha=0.7)
        else:
            ax.plot(xf, yf, 'g^', markersize=5, alpha=0.5)

def animate(i):
    t = tempos[i]
    hora = t
    ciclo = int(t // T_mare) + 1
    fase = (t % T_mare) / T_mare
    
    # Fator de maré: +1 (enchente), -1 (vazante)
    F_mare = np.sin(2 * np.pi * t / T_mare)
    
    # Fator de vento (modulado pela maré - ventos NE intensificam na vazante)
    # Carvalho et al. (2003): correlação 12-24h antes
    F_vento = 0.7 + 0.3 * np.cos(2 * np.pi * (t - 6) / T_mare)
    
    # --- TEMPERATURA ---
    # Enchente empurra ACAS (18°C) para dentro; vazante empurra água quente (30°C) para fora
    penetracao_fria = 0.25 * max(0, F_mare) * F_vento
    W_ef_T = np.clip(W - penetracao_fria, 0, 1)
    Temp = T_boca_baia + (T_fundo_baia - T_boca_baia) * W_ef_T
    
    # --- SALINIDADE ---
    penetracao_sal = 0.30 * max(0, F_mare) * F_vento
    W_ef_S = np.clip(W - penetracao_sal, 0, 1)
    Sal = S_boca_baia - (S_boca_baia - S_fundo_baia) * W_ef_S
    
    # --- MICROPLÁSTICOS LEVES (superfície) ---
    # Fortemente influenciados por vento NE (Rosman et al., 2024)
    # Deslocamento para leste (u>0) e sul (v<0)
    desloc_x_leves = (vento_u_base * F_vento * 8000) + (F_mare * 3000)
    desloc_y_leves = (vento_v_base * F_vento * 4000) - (F_mare * 2000)
    
    X_leves = X + desloc_x_leves
    Y_leves = Y + desloc_y_leves
    
    MP_leves_t = np.zeros(N)
    for nome, (xf, yf, conc) in fontes.items():
        dist_f = np.sqrt((X_leves - xf)**2 + (Y_leves - yf)**2)
        sigma = 4000  # maior dispersão
        MP_leves_t += conc * np.exp(-0.5 * (dist_f / sigma)**2)
    MP_leves_t = MP_leves_t / MP_leves_t.max()
    
    # --- MICROPLÁSTICOS NEUTROS (coluna d'água) ---
    # Dispersão intermediária, menos influenciados por vento
    desloc_x_neutros = F_mare * 4000
    desloc_y_neutros = -F_mare * 3000
    
    X_neutros = X + desloc_x_neutros
    Y_neutros = Y + desloc_y_neutros
    
    MP_neutros_t = np.zeros(N)
    for nome, (xf, yf, conc) in fontes.items():
        dist_f = np.sqrt((X_neutros - xf)**2 + (Y_neutros - yf)**2)
        sigma = 3000
        MP_neutros_t += conc * np.exp(-0.5 * (dist_f / sigma)**2)
    MP_neutros_t = MP_neutros_t / MP_neutros_t.max()
    
    # --- MICROPLÁSTICOS DENSOS (fundo) ---
    # Baixa mobilidade, retenção próxima às fontes (Rodrigues et al., 2026)
    desloc_x_densos = F_mare * 1000  # deslocamento mínimo
    desloc_y_densos = -F_mare * 800
    
    X_densos = X + desloc_x_densos
    Y_densos = Y + desloc_y_densos
    
    MP_densos_t = np.zeros(N)
    for nome, (xf, yf, conc) in fontes.items():
        dist_f = np.sqrt((X_densos - xf)**2 + (Y_densos - yf)**2)
        sigma = 1500  # menor dispersão
        MP_densos_t += conc * np.exp(-0.5 * (dist_f / sigma)**2)
    MP_densos_t = MP_densos_t / MP_densos_t.max()
    
    # Coeficiente de absorção em praias (Rosman et al., 2024): cA = 0.05
    # Reduz MP leves perto da costa durante vazante
    dist_costa = np.sqrt((X - 670000)**2 + (Y - 7460000)**2)
    fator_praia = 1.0 - 0.05 * np.exp(-0.5 * (dist_costa / 5000)**2) * max(0, -F_mare)
    MP_leves_t *= fator_praia
    
    # --- PLOTAR ---
    for ax in axes.flat:
        ax.clear()
        ax.set_xlim(X.min() - 3000, X.max() + 3000)
        ax.set_ylim(Y.min() - 3000, Y.max() + 3000)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3, linestyle='--')
    
    # Painel 1: Temperatura
    ax1 = axes[0,0]
    temp_plot = ax1.tripcolor(triang, Temp, cmap='coolwarm', shading='gouraud', vmin=16, vmax=32)
    # Isoterma 19°C (Carvalho et al., 2003) - limite da ACAS
    iso19 = ax1.tricontour(triang, Temp, levels=[19], colors='white', linewidths=2.5)
    ax1.clabel(iso19, inline=True, fontsize=9, fmt='%.0f°C (ACAS)')
    ax1.set_title('Temperatura (°C) - Isoterma 19°C = ACAS', fontsize=12, fontweight='bold')
    ax1.set_xlabel('X (UTM)'); ax1.set_ylabel('Y (UTM)')
    
    # Painel 2: Salinidade
    ax2 = axes[0,1]
    sal_plot = ax2.tripcolor(triang, Sal, cmap='Blues', shading='gouraud', vmin=14, vmax=37)
    iso25 = ax2.tricontour(triang, Sal, levels=[20, 25, 30, 35], colors='red', linewidths=1.5, alpha=0.7)
    ax2.clabel(iso25, inline=True, fontsize=8, fmt='%.0f psu')
    ax2.set_title('Salinidade (psu) - Cunhas salinas', fontsize=12, fontweight='bold')
    ax2.set_xlabel('X (UTM)'); ax2.set_ylabel('Y (UTM)')
    
    # Painel 3: MP Leves + Neutros
    ax3 = axes[1,0]
    mp_ln = (MP_leves_t + MP_neutros_t) / 2
    mp_ln_plot = ax3.tripcolor(triang, mp_ln, cmap='YlOrRd', shading='gouraud', vmin=0, vmax=1)
    ax3.set_title('MP Leves (superfície) + Neutros (coluna)', fontsize=12, fontweight='bold')
    ax3.set_xlabel('X (UTM)'); ax3.set_ylabel('Y (UTM)')
    
    # Painel 4: MP Densos + Hotspots
    ax4 = axes[1,1]
    mp_d_plot = ax4.tripcolor(triang, MP_densos_t, cmap='Oranges', shading='gouraud', vmin=0, vmax=1)
    for nome_hs, (xh, yh) in hotspots.items():
        ax4.plot(xh, yh, 'k*', markersize=14, markeredgecolor='white', markeredgewidth=2)
        ax4.annotate(nome_hs, (xh, yh), textcoords="offset points", xytext=(8,8),
                    fontsize=7, color='black', fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='yellow', alpha=0.7))
    ax4.set_title('MP Densos (fundo) + Hotspots (★)', fontsize=12, fontweight='bold')
    ax4.set_xlabel('X (UTM)'); ax4.set_ylabel('Y (UTM)')
    
    # Título principal
    estado_mare = "ENCHENTE" if F_mare > 0.1 else ("VAZANTE" if F_mare < -0.1 else "ESTOFO")
    intensidade_vento = "FORTE" if F_vento > 0.8 else ("MODERADO" if F_vento > 0.6 else "FRACO")
    main_title = (f'CICLO {ciclo}/2 | t={hora:.1f}h | Maré: {estado_mare} (F={F_mare:+.2f}) | '
                  f'Vento NE: {intensidade_vento} (F={F_vento:.2f})')
    fig.suptitle(main_title, fontsize=14, fontweight='bold', y=0.98)
    
    # Colorbars (adicionar apenas no primeiro frame)
    if i == 0:
        fig.colorbar(temp_plot, ax=ax1, fraction=0.046, pad=0.04, label='Temperatura (°C)')
        fig.colorbar(sal_plot, ax=ax2, fraction=0.046, pad=0.04, label='Salinidade (psu)')
        fig.colorbar(mp_ln_plot, ax=ax3, fraction=0.046, pad=0.04, label='Concentração MP (norm.)')
        fig.colorbar(mp_d_plot, ax=ax4, fraction=0.046, pad=0.04, label='Concentração MP (norm.)')
    
    return []

print("  Renderizando frames...")
anim = animation.FuncAnimation(fig, animate, frames=N_FRAMES, interval=150, blit=False)
anim.save(OUT_GIF, writer='pillow', fps=4, dpi=100)
print(f"  OK GIF salvo: {OUT_GIF.name}")

# ==========================================
# 7. IMAGEM ESTÁTICA DE RESUMO
# ==========================================
print("\n[6/6] Gerando imagem estática de resumo...")

# Instante: Enchente máxima do 1º ciclo (t=6.21h) - máxima penetração de ACAS
t_ex = 6.21
F_mare_ex = np.sin(2 * np.pi * t_ex / T_mare)
F_vento_ex = 0.7 + 0.3 * np.cos(2 * np.pi * (t_ex - 6) / T_mare)

pen_fria = 0.25 * max(0, F_mare_ex) * F_vento_ex
W_ef_T = np.clip(W - pen_fria, 0, 1)
Temp_ex = T_boca_baia + (T_fundo_baia - T_boca_baia) * W_ef_T

pen_sal = 0.30 * max(0, F_mare_ex) * F_vento_ex
W_ef_S = np.clip(W - pen_sal, 0, 1)
Sal_ex = S_boca_baia - (S_boca_baia - S_fundo_baia) * W_ef_S

# MP no instante de enchente máxima
MP_leves_ex = np.zeros(N)
MP_densos_ex = np.zeros(N)
desloc_x = vento_u_base * F_vento_ex * 8000 + F_mare_ex * 3000
desloc_y = vento_v_base * F_vento_ex * 4000 - F_mare_ex * 2000

for nome, (xf, yf, conc) in fontes.items():
    dist_f_l = np.sqrt(((X + desloc_x) - xf)**2 + ((Y + desloc_y) - yf)**2)
    MP_leves_ex += conc * np.exp(-0.5 * (dist_f_l / 4000)**2)
    
    dist_f_d = np.sqrt(((X + F_mare_ex*1000) - xf)**2 + ((Y - F_mare_ex*800) - yf)**2)
    MP_densos_ex += conc * np.exp(-0.5 * (dist_f_d / 1500)**2)

MP_leves_ex = MP_leves_ex / MP_leves_ex.max()
MP_densos_ex = MP_densos_ex / MP_densos_ex.max()

fig_res, axes_res = plt.subplots(2, 2, figsize=(22, 18))
fig_res.suptitle('EVENTO EXTREMO: PÓS-CHUVA + RESSURGÊNCIA DE CABO FRIO\n'
                 'Enchente Máxima do 1º Ciclo (t=6.21h) - Máxima Penetração de ACAS',
                 fontsize=16, fontweight='bold', y=0.98)

# Painel 1: Temperatura
ax1 = axes_res[0,0]
ax1.tripcolor(triang, Temp_ex, cmap='coolwarm', shading='gouraud', vmin=16, vmax=32)
iso19 = ax1.tricontour(triang, Temp_ex, levels=[19], colors='white', linewidths=3)
ax1.clabel(iso19, inline=True, fontsize=10, fmt='%.0f°C (ACAS)')
ax1.set_title('Temperatura (°C)\nAzul=ACAS (18°C) | Vermelho=Água Doce Quente (30°C)', 
              fontsize=12, fontweight='bold')
ax1.set_xlabel('X (UTM)'); ax1.set_ylabel('Y (UTM)'); ax1.set_aspect('equal'); ax1.grid(True, alpha=0.3)

# Painel 2: Salinidade
ax2 = axes_res[0,1]
ax2.tripcolor(triang, Sal_ex, cmap='Blues', shading='gouraud', vmin=14, vmax=37)
iso_sal = ax2.tricontour(triang, Sal_ex, levels=[20, 25, 30, 35], colors='red', linewidths=2)
ax2.clabel(iso_sal, inline=True, fontsize=9, fmt='%.0f psu')
ax2.set_title('Salinidade (psu)\nAzul=Marinha (36 psu) | Branco=Doce (15 psu)',
              fontsize=12, fontweight='bold')
ax2.set_xlabel('X (UTM)'); ax2.set_ylabel('Y (UTM)'); ax2.set_aspect('equal'); ax2.grid(True, alpha=0.3)

# Painel 3: MP Leves
ax3 = axes_res[1,0]
mp_l_plot = ax3.tripcolor(triang, MP_leves_ex, cmap='YlOrRd', shading='gouraud', vmin=0, vmax=1)
ax3.set_title('Microplásticos Leves (Superfície)\nTransportados por ventos NE para leste',
              fontsize=12, fontweight='bold')
ax3.set_xlabel('X (UTM)'); ax3.set_ylabel('Y (UTM)'); ax3.set_aspect('equal'); ax3.grid(True, alpha=0.3)
fig_res.colorbar(mp_l_plot, ax=ax3, label='Concentração Normalizada')

# Painel 4: MP Densos + Hotspots
ax4 = axes_res[1,1]
mp_d_plot = ax4.tripcolor(triang, MP_densos_ex, cmap='Oranges', shading='gouraud', vmin=0, vmax=1)
for nome_hs, (xh, yh) in hotspots.items():
    ax4.plot(xh, yh, 'k*', markersize=16, markeredgecolor='white', markeredgewidth=2.5)
    ax4.annotate(nome_hs, (xh, yh), textcoords="offset points", xytext=(10,10),
                fontsize=9, color='black', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.8))
ax4.set_title('Microplásticos Densos (Fundo) + Hotspots de Acúmulo (★)\n'
              'Retenção próxima às fontes (Rodrigues et al., 2026)',
              fontsize=12, fontweight='bold')
ax4.set_xlabel('X (UTM)'); ax4.set_ylabel('Y (UTM)'); ax4.set_aspect('equal'); ax4.grid(True, alpha=0.3)
fig_res.colorbar(mp_d_plot, ax=ax4, label='Concentração Normalizada')

plt.tight_layout()
plt.savefig(OUT_PNG, dpi=200, bbox_inches='tight')
plt.close()
print(f"  OK Imagem de resumo salva: {OUT_PNG.name}")

print("\n" + "="*70)
print("SIMULAÇÃO ENRIQUECIDA CONCLUÍDA!")
print("="*70)
print(f"\nArquivos no Desktop:")
print(f"  1. {OUT_GIF.name}")
print(f"     → Animação de 2 ciclos de maré (24.84h)")
print(f"     → 4 painéis: T, S, MP leves/neutros, MP densos+hotspots")
print(f"  2. {OUT_PNG.name}")
print(f"     → Instantâneo da enchente máxima (t=6.21h)")
print(f"     → Isoterma 19°C (ACAS) destacada")
print(f"\nReferências integradas:")
print(f"  • Rodrigues et al. (FluHidros 2026): 3 classes de flutuabilidade")
print(f"  • Rosman et al. (2024): ESEI/ESIca, hotspots, cA=0.05")
print(f"  • Carvalho et al. (2003): ITR, ventos NE, TSM 18-20°C")
print("="*70)
