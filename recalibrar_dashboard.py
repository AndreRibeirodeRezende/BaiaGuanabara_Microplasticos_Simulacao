#!/usr/bin/env python3
"""
Recalibra o dashboard Westerdok com batimetria real (2,77 m NAP).
Gera:
  1. Imagens das curvas recalibradas (para o relatorio Tier 0)
  2. JSON com novos parametros (para atualizar o dashboard web)
  3. TXT com os novos numeros para colar no cartao
"""
import matplotlib
matplotlib.use('Agg')
import numpy as np
import matplotlib.pyplot as plt
import json
from pathlib import Path
from datetime import datetime

OUT_DIR = Path("/mnt/c/Users/Maria Engracia/Desktop")

print("="*70)
print("RECALIBRANDO DASHBOARD WESTERDOK - BATIMETRIA REAL")
print("="*70)

# ============================================================
# PARAMETROS ANTERIORES (PREMISSA)
# ============================================================
H_old = 2.50          # m (premissa)
P_comp = 10.0         # kW
L_cortina = 60.0      # m
eta_max = 0.86        # eficiencia maxima reportada
Q50_old = 400.0       # m3/h/m (prior do modelo de Hill)
Qcrit_old = 800.0     # m3/h/m
T_boca = 18.0         # C (ACAS)
T_fundo = 30.0        # C (pos-chuva)
S_boca = 36.0         # psu
S_fundo = 15.0        # psu
tarifa = 0.20         # EUR/kWh
captura_anual = 1000.0  # kg/ano
horas_ano = 8760.0

# ============================================================
# PARAMETROS REAIS (PDOK / AMSTERDAM OPEN GEODATA)
# ============================================================
H_real = 2.77         # m NAP (medido)
rho = 1025.0          # kg/m3 (agua do mar)
g = 9.81              # m/s2

# Pressao hidrostatica na profundidade da cortina
P_hid_old = rho * g * H_old / 1000.0    # kPa
P_hid_real = rho * g * H_real / 1000.0  # kPa

print(f"\n[1/5] Parametros fisicos:")
print(f"  Profundidade: {H_old} m -> {H_real} m (NAP)")
print(f"  Pressao hidrostatica: {P_hid_old:.2f} kPa -> {P_hid_real:.2f} kPa")

# ============================================================
# ENGENHARIA REVERSA DA VAZAO DE AR
# ============================================================
# Para soprador de deslocamento positivo: P * Q ~ constante para mesma potencia
# Potencia hidraulica = P_hid * Q
# Q_real = Q_old * (P_hid_old / P_hid_real)
fator_pressao = P_hid_old / P_hid_real  # ~0.90

Q_estimado_old_min = 13.0   # m3/h/m (limite inferior)
Q_estimado_old_max = 20.0   # m3/h/m (limite superior)
Q_estimado_real_min = Q_estimado_old_min * fator_pressao
Q_estimado_real_max = Q_estimado_old_max * fator_pressao

print(f"\n[2/5] Vazao de ar estimada (10 kW / 60 m):")
print(f"  Antes: {Q_estimado_old_min:.0f}-{Q_estimado_old_max:.0f} m3/h/m")
print(f"  Agora: {Q_estimado_real_min:.0f}-{Q_estimado_real_max:.0f} m3/h/m")
print(f"  Q50 do modelo: {Q50_old} m3/h/m")
print(f"  Razao operacional: {Q_estimado_real_min/Q50_old:.4f} a {Q_estimado_real_max/Q50_old:.4f}")

# ============================================================
# CURVA DE HILL RECALIBRADA
# ============================================================
# eta(Q) = eta_max * Q^n / (Q50^n + Q^n), com n=2 (Hill classico)
Q_range = np.linspace(0, 1000, 500)
n_hill = 2.0

eta_old = eta_max * (Q_range**n_hill) / (Q50_old**n_hill + Q_range**n_hill)
# Para Westerdok real, o Q50 efetivo pode ser diferente (escala menor)
# Estimativa: Q50_real ~ Q50_old * (H_real/H_old)^0.5 (escalamento com profundidade)
Q50_real = Q50_old * np.sqrt(H_real / H_old)
Qcrit_real = Qcrit_old * np.sqrt(H_real / H_old)

eta_real = eta_max * (Q_range**n_hill) / (Q50_real**n_hill + Q_range**n_hill)

print(f"\n[3/5] Curva de Hill recalibrada:")
print(f"  Q50: {Q50_old} -> {Q50_real:.0f} m3/h/m")
print(f"  Qcrit: {Qcrit_old} -> {Qcrit_real:.0f} m3/h/m")

# ============================================================
# POTENCIAL DE ECONOMIA RECALCULADO
# ============================================================
consumo_anual = P_comp * horas_ano  # kWh/ano
custo_anual_EUR = consumo_anual * tarifa
custo_anual_BRL = custo_anual_EUR * 5.50  # CORRECAO: definir ANTES de usar
custo_especifico_EUR = custo_anual_EUR / captura_anual
custo_especifico_BRL = custo_especifico_EUR * 5.50

# Economia com reducao de vazao (lei de afinidade: P ~ Q^1.5 para sopradores)
# Reducao de 10-20% na vazao -> reducao de ~8-15% na potencia
economias = {}
for red in [0.10, 0.15, 0.20]:
    red_pot = 1.0 - (1.0 - red)**1.5
    econ_EUR = custo_anual_EUR * red_pot
    econ_BRL = econ_EUR * 5.50
    economias[red] = {'EUR': econ_EUR, 'BRL': econ_BRL, 'red_pot': red_pot}

print(f"\n[4/5] Linha de base energetica:")
print(f"  Consumo anual: {consumo_anual:.0f} kWh/ano")
print(f"  Custo anual: EUR {custo_anual_EUR:,.0f} (R$ {custo_anual_BRL:,.0f})")
print(f"  Custo especifico: EUR {custo_especifico_EUR:.2f}/kg (R$ {custo_especifico_BRL:.2f}/kg)")
print(f"\n  Potencial de economia:")
for red, v in economias.items():
    print(f"    -{int(red*100)}% vazao: EUR {v['EUR']:,.0f}/ano (R$ {v['BRL']:,.0f}/ano)")

# ============================================================
# GERAR IMAGENS DO DASHBOARD RECALIBRADO
# ============================================================
print(f"\n[5/5] Gerando imagens do dashboard recalibrado...")

# Figura 1: Curva de eficiencia vs vazao (antes vs depois)
fig1, ax1 = plt.subplots(figsize=(12, 7))
ax1.plot(Q_range, eta_old * 100, 'b--', linewidth=2, label=f'Modelo original (Q50={Q50_old:.0f})')
ax1.plot(Q_range, eta_real * 100, 'r-', linewidth=2.5, label=f'Recalibrado (Q50={Q50_real:.0f}, H={H_real} m)')
ax1.axvline(Q_estimado_real_min, color='green', linestyle=':', linewidth=1.5, label=f'Vazao estimada min ({Q_estimado_real_min:.0f})')
ax1.axvline(Q_estimado_real_max, color='orange', linestyle=':', linewidth=1.5, label=f'Vazao estimada max ({Q_estimado_real_max:.0f})')
ax1.axhline(eta_max * 100, color='gray', linestyle='-', linewidth=1, alpha=0.5)
ax1.set_xlabel('Vazao de ar especifica Qa (m3/h/m)', fontsize=12)
ax1.set_ylabel('Eficiencia de captura (%)', fontsize=12)
ax1.set_title('Curva de Eficiencia vs Vazao - Westerdok Recalibrado\nBatimetria real: 2,77 m NAP (PDOK/Amsterdam Open Geodata)', fontsize=13, fontweight='bold')
ax1.set_xlim(0, 1000)
ax1.set_ylim(0, 100)
ax1.legend(fontsize=10, loc='lower right')
ax1.grid(True, alpha=0.3)
plt.tight_layout()
out_fig1 = OUT_DIR / "dashboard_curva_eficiencia_recalibrada.png"
plt.savefig(out_fig1, dpi=150, bbox_inches='tight')
plt.close()
print(f"  OK {out_fig1.name}")

# Figura 2: Pressao hidraulica e potencia
fig2, ax2 = plt.subplots(figsize=(10, 6))
categorias = ['Premissa\n(2,50 m)', 'Real\n(2,77 m NAP)']
pressoes = [P_hid_old, P_hid_real]
cores = ['#888888', '#d62728']
bars = ax2.bar(categorias, pressoes, color=cores, edgecolor='black', linewidth=1.5)
for bar, val in zip(bars, pressoes):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
             f'{val:.2f} kPa', ha='center', va='bottom', fontsize=12, fontweight='bold')
ax2.set_ylabel('Pressao hidrostatica (kPa)', fontsize=12)
ax2.set_title('Pressao na Profundidade da Cortina\nImpacto na vazao de ar para mesma potencia', fontsize=13, fontweight='bold')
ax2.set_ylim(0, 35)
ax2.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
out_fig2 = OUT_DIR / "dashboard_pressao_hidrostatica.png"
plt.savefig(out_fig2, dpi=150, bbox_inches='tight')
plt.close()
print(f"  OK {out_fig2.name}")

# Figura 3: Economia potencial
fig3, ax3 = plt.subplots(figsize=(10, 6))
reducoes = list(economias.keys())
labels = [f'-{int(r*100)}% vazao' for r in reducoes]
valores_EUR = [economias[r]['EUR'] for r in reducoes]
valores_BRL = [economias[r]['BRL'] for r in reducoes]
x = np.arange(len(labels))
largura = 0.35
bars1 = ax3.bar(x - largura/2, valores_EUR, largura, label='EUR', color='#1f77b4')
bars2 = ax3.bar(x + largura/2, valores_BRL, largura, label='BRL (x5.50)', color='#ff7f0e')
for bar in bars1:
    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
             f'EUR {bar.get_height():,.0f}', ha='center', fontsize=9)
for bar in bars2:
    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
             f'R$ {bar.get_height():,.0f}', ha='center', fontsize=9)
ax3.set_ylabel('Economia anual', fontsize=12)
ax3.set_title('Potencial de Economia com Reducao de Vazao\nLei de afinidade para sopradores (P ~ Q^1.5)', fontsize=13, fontweight='bold')
ax3.set_xticks(x)
ax3.set_xticklabels(labels)
ax3.legend()
ax3.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
out_fig3 = OUT_DIR / "dashboard_economia_potencial.png"
plt.savefig(out_fig3, dpi=150, bbox_inches='tight')
plt.close()
print(f"  OK {out_fig3.name}")

# ============================================================
# JSON COM PARAMETROS ATUALIZADOS (para o dashboard web)
# ============================================================
params_json = {
    'versao': '2.0 - com batimetria real',
    'data_atualizacao': datetime.now().isoformat(),
    'fonte_batimetria': 'PDOK / Amsterdam Open Geodata (fallback publico)',
    'parametros_fisicos': {
        'profundidade_m_NAP': H_real,
        'profundidade_anterior_m': H_old,
        'pressao_hidrostatica_kPa': round(P_hid_real, 2),
        'comprimento_cortina_m': L_cortina,
        'potencia_compressor_kW': P_comp,
        'eficiencia_maxima': eta_max,
        'captura_anual_kg': captura_anual,
        'tarifa_EUR_kWh': tarifa
    },
    'curva_hill_recalibrada': {
        'Q50_m3_h_m': round(Q50_real, 0),
        'Qcrit_m3_h_m': round(Qcrit_real, 0),
        'expoente_n': n_hill,
        'Q50_anterior': Q50_old,
        'fator_escalamento': round(np.sqrt(H_real/H_old), 3)
    },
    'vazao_ar_estimada': {
        'min_m3_h_m': round(Q_estimado_real_min, 1),
        'max_m3_h_m': round(Q_estimado_real_max, 1),
        'fator_correcao_pressao': round(fator_pressao, 3),
        'razao_com_Q50': f"{Q_estimado_real_min/Q50_real:.4f} a {Q_estimado_real_max/Q50_real:.4f}"
    },
    'linha_base_energetica': {
        'consumo_anual_kWh': round(consumo_anual, 0),
        'custo_anual_EUR': round(custo_anual_EUR, 0),
        'custo_anual_BRL': round(custo_anual_BRL, 0),
        'custo_especifico_EUR_kg': round(custo_especifico_EUR, 2),
        'custo_especifico_BRL_kg': round(custo_especifico_BRL, 2)
    },
    'economia_potencial_EUR_ano': {
        'reducao_10pct': round(economias[0.10]['EUR'], 0),
        'reducao_15pct': round(economias[0.15]['EUR'], 0),
        'reducao_20pct': round(economias[0.20]['EUR'], 0)
    }
}

out_json = OUT_DIR / "dashboard_parametros_recalibrados.json"
with open(out_json, 'w', encoding='utf-8') as f:
    json.dump(params_json, f, indent=2, ensure_ascii=False)
print(f"  OK {out_json.name}")

# ============================================================
# TXT PARA COLAR NO RELATORIO
# ============================================================
txt = f"""
DASHBOARD WESTERDOK - PARAMETROS RECALIBRADOS
==============================================
Data: {datetime.now().strftime('%Y-%m-%d %H:%M')}

BATIMETRIA REAL:
  Profundidade: {H_real} m NAP (antes: {H_old} m premissa)
  Fonte: PDOK / Amsterdam Open Geodata
  Pressao hidrostatica: {P_hid_real:.2f} kPa (antes: {P_hid_old:.2f} kPa)

CURVA DE HILL RECALIBRADA:
  Q50: {Q50_real:.0f} m3/h/m (antes: {Q50_old})
  Qcrit: {Qcrit_real:.0f} m3/h/m (antes: {Qcrit_old})
  Fator de escalamento: sqrt({H_real}/{H_old}) = {np.sqrt(H_real/H_old):.3f}

VAZAO DE AR ESTIMADA (10 kW / 60 m):
  Faixa: {Q_estimado_real_min:.0f} a {Q_estimado_real_max:.0f} m3/h/m
  Razao com Q50 real: {Q_estimado_real_min/Q50_real:.4f} a {Q_estimado_real_max/Q50_real:.4f}
  Conclusao: OPERA EM REGIAO DE BAIXA EFICIENCIA

LINHA DE BASE:
  Consumo: {consumo_anual:.0f} kWh/ano
  Custo: EUR {custo_anual_EUR:,.0f}/ano (R$ {custo_anual_BRL:,.0f})
  Custo especifico: EUR {custo_especifico_EUR:.2f}/kg

ECONOMIA POTENCIAL:
  -10% vazao: EUR {economias[0.10]['EUR']:,.0f}/ano
  -15% vazao: EUR {economias[0.15]['EUR']:,.0f}/ano
  -20% vazao: EUR {economias[0.20]['EUR']:,.0f}/ano

IMAGENS GERADAS:
  - {out_fig1.name}
  - {out_fig2.name}
  - {out_fig3.name}
"""
out_txt = OUT_DIR / "dashboard_parametros_recalibrados.txt"
with open(out_txt, 'w', encoding='utf-8') as f:
    f.write(txt)
print(f"  OK {out_txt.name}")

print("\n" + "="*70)
print("DASHBOARD RECALIBRADO COM SUCESSO!")
print("="*70)
print(f"\nArquivos no Desktop:")
print(f"  1. {out_fig1.name}")
print(f"  2. {out_fig2.name}")
print(f"  3. {out_fig3.name}")
print(f"  4. {out_json.name} (para atualizar o site)")
print(f"  5. {out_txt.name} (para colar no relatorio)")
print("="*70)
