#!/usr/bin/env python3
"""
Gera CSV simples para importar no ParaView via Table To Points.
Usa colunas reais do SisBaHiA com normalização e exagero vertical.
"""
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path("/mnt/c/Users/Maria Engracia/Desktop/Andre/IA/Microplastico/EHD8L_BaiaGuanabara")
CSV = BASE / "02_Malha_e_Geometria/Nos_e_Elementos"
OUT_CSV = Path("/mnt/c/Users/Maria Engracia/Desktop/baia_guanabara.csv")

print("="*70)
print("GERANDO CSV PARA PARAVIEW (TABLE TO POINTS)")
print("="*70)

# 1. Carregar dados
print("\n[1/4] Carregando dados SisBaHiA...")
df_nos = pd.read_csv(CSV / "no.csv")
print(f"  ✓ {len(df_nos)} nós carregados")

# 2. Extrair coordenadas reais
print("\n[2/4] Extraindo coordenadas...")
nos_x = df_nos['NOCOORDENADAX'].values
nos_y = df_nos['NOCOORDENADAY'].values
nos_z = df_nos['NOCOORDENADAZ'].values

# Normalizar X e Y
x_min = nos_x.min()
y_min = nos_y.min()
nos_x_norm = nos_x - x_min
nos_y_norm = nos_y - y_min

# Exagero vertical (Z * 100 para visualização)
EXAGERO = 100
nos_z_exag = nos_z * EXAGERO

print(f"  ✓ X: [{nos_x_norm.min():.0f}, {nos_x_norm.max():.0f}]")
print(f"  ✓ Y: [{nos_y_norm.min():.0f}, {nos_y_norm.max():.0f}]")
print(f"  ✓ Z (exagerado x{EXAGERO}): [{nos_z_exag.min():.1f}, {nos_z_exag.max():.1f}]")

# 3. Calcular concentração de microplásticos
print("\n[3/4] Calculando concentração...")
cx = np.mean(nos_x_norm)
cy = np.mean(nos_y_norm)
ux = cx - 8000
uy = cy - 12000
dist = np.sqrt((nos_x_norm - ux)**2 + (nos_y_norm - uy)**2)
C0 = np.exp(-2.0 * (dist / dist.max())**2)

# 4. Criar DataFrame e salvar CSV
print("\n[4/4] Salvando CSV...")
df_out = pd.DataFrame({
    'X': nos_x_norm,
    'Y': nos_y_norm,
    'Z': nos_z_exag,
    'Concentracao_MP': C0,
    'Batimetria': nos_z
})

df_out.to_csv(OUT_CSV, index=False, float_format='%.6f')

print(f"\n  ✓ CSV salvo: {OUT_CSV}")
print(f"  ✓ Tamanho: {OUT_CSV.stat().st_size / 1024:.1f} KB")
print(f"  ✓ Linhas: {len(df_out)}")

print("\n" + "="*70)
print("SUCESSO! CSV gerado no Desktop!")
print("="*70)
print("\nNo ParaView:")
print("  1. File -> Open -> baia_guanabara.csv")
print("  2. Em 'File Type', selecione 'CSV Files'")
print("  3. Apply")
print("  4. Filters -> Alphabetical -> Table To Points")
print("  5. X Column: X, Y Column: Y, Z Column: Z")
print("  6. Apply")
print("  7. Representation: Surface")
print("  8. Coloring: Concentracao_MP")
print("  9. Clique no botão -Z (vista de cima)")
print("="*70)
