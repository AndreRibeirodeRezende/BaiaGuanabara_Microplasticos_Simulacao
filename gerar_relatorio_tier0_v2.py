#!/usr/bin/env python3
"""
Gera o Relatorio Tier 0 atualizado com batimetria real do Westerdok.
Substitui a premissa de 2,5 m pelo valor medido de 2,77 m (NAP).
Saida: TXT formatado pronto para converter em PDF ou colar no cartao.
"""
import matplotlib
matplotlib.use('Agg')
from pathlib import Path
from datetime import datetime

OUT_DIR = Path("/mnt/c/Users/Maria Engracia/Desktop")

print("="*70)
print("GERANDO RELATORIO TIER 0 v2 - COM BATIMETRIA REAL")
print("="*70)

# Parametros reais
H_real = 2.77
H_old = 2.50
P_comp = 10.0
L_cortina = 60.0
eta_max = 0.86
Q50_old = 400.0
Q50_real = Q50_old * (H_real/H_old)**0.5
Qcrit_real = 800.0 * (H_real/H_old)**0.5
rho = 1025.0
g = 9.81
P_hid = rho * g * H_real / 1000.0
fator_pressao = (rho * g * H_old / 1000.0) / P_hid
Q_min = 13.0 * fator_pressao
Q_max = 20.0 * fator_pressao
tarifa = 0.20
captura = 1000.0
horas = 8760.0
consumo = P_comp * horas
custo_EUR = consumo * tarifa
custo_kg_EUR = custo_EUR / captura
custo_kg_BRL = custo_kg_EUR * 5.50
TCO_kg_EUR = 76.45
pct_energia = (custo_kg_EUR / TCO_kg_EUR) * 100

# Economias
econ_10 = custo_EUR * (1 - (0.9)**1.5)
econ_15 = custo_EUR * (1 - (0.85)**1.5)
econ_20 = custo_EUR * (1 - (0.8)**1.5)

relatorio = f"""
================================================================================
DIAGNOSTICO RELAMPAGO v2 - BUBBLE BARRIER WESTERDOK
Tier 0: Dados Publicos + Batimetria Real (PDOK/Amsterdam Open Geodata)
================================================================================

Autor: Andre Ribeiro de Rezende
Instituicao: Pesquisador Independente
Data: {datetime.now().strftime('%d/%m/%Y')}
Versao: 2.0 (com batimetria medida)

================================================================================
RESUMO EXECUTIVO
================================================================================

A barreira de bolhas de Westerdok opera com um compressor de ~10 kW continuos,
consumindo aproximadamente {consumo:.0f} kWh/ano. Com captura anual de ~1.000 kg
de plastico, o consumo especifico e de {custo_kg_EUR:.1f} kWh/kg.

NOVIDADE DESTA VERSAO: A profundidade do canal foi medida via dados publicos
do PDOK (Publieke Dienstverlening Op de Kaart) e Amsterdam Open Geodata:

  Profundidade real: {H_real} m NAP (Normaal Amsterdams Peil)
  (Anteriormente estimada como {H_old} m - faixa tipica)

Isso elimina a lacuna metodologica declarada no Tier 0 original e ancora o
diagnostico em dado auditavel do governo holandes.

================================================================================
1. DADOS PUBLICOS UTILIZADOS
================================================================================

| Parametro              | Valor          | Fonte                              |
|------------------------|----------------|------------------------------------|
| Potencia compressor    | ~10 kW cont.   | WUR/edepot                         |
| Captura anual          | ~1.000 kg/ano  | Waternet/Tauw (2023); TGBB (2024)  |
| Eficiencia captura     | 86%            | TGBB; Holland Circular Hotspot     |
| Comprimento cortina    | 60 m           | Greentek Solutions                 |
| PROFUNDIDADE REAL      | {H_real} m NAP | PDOK / Amsterdam Open Geodata      |
| Pressao hidrostatica   | {P_hid:.2f} kPa| Calculado (rho=1025, g=9.81)       |
| Tarifa energia         | EUR 0,20/kWh   | HarmoniQ (H1 2025)                 |

================================================================================
2. LINHA DE BASE ENERGETICA
================================================================================

| Metrica                        | Valor                  |
|--------------------------------|------------------------|
| Consumo anual                  | {consumo:.0f} kWh/ano         |
| Custo anual eletricidade       | EUR {custo_EUR:,.0f}/ano        |
| Custo especifico energia       | EUR {custo_kg_EUR:.2f}/kg         |
| Custo especifico (BRL)         | R$ {custo_kg_BRL:.2f}/kg          |
| TCO reportado (Waternet/Tauw)  | EUR {TCO_kg_EUR:.2f}/kg           |
| Parcela energia no TCO         | {pct_energia:.1f}%                |

Nota: O custo de EUR {custo_kg_EUR:.2f}/kg refere-se APENAS a eletricidade.
O TCO completo (CAPEX + OPEX + manutencao em 10 anos) e EUR {TCO_kg_EUR:.2f}/kg.

================================================================================
3. DESCOBERTA: INCOMPATIBILIDADE DE ESCALA (REFORCADA)
================================================================================

O modelo parametrico do dashboard foi calibrado com barreiras de grande porte,
cuja vazao de ar tipica e da ordem de centenas de m3/h por metro de cortina
(Q50 = {Q50_old} m3/h/m no modelo original).

Com a batimetria real de {H_real} m, a pressao hidrostatica na cortina e de
{P_hid:.2f} kPa (11% maior que a premissa de {H_old} m). Aplicando engenharia
reversa a potencia de 10 kW:

  Vazao estimada: {Q_min:.0f} a {Q_max:.0f} m3/h/m
  Q50 recalibrado: {Q50_real:.0f} m3/h/m
  Razao operacional: {Q_min/Q50_real:.4f} a {Q_max/Q50_real:.4f}

>>> A vazao real esta UMA ORDEM DE GRANDEZA abaixo do Q50.

Isso NAO significa que a barreira e ineficiente. Significa que o modelo publico
NAO foi feito para a escala de Westerdok - e que a curva real de eficiencia
vs. vazao da instalacao e um dado que so a TGBB possui.

COM A BATIMETRIA REAL, a discrepancia e MAIOR do que estimada antes, o que
REFORCA o potencial de otimizacao.

================================================================================
4. POTENCIAL DE ECONOMIA (RECALCULADO)
================================================================================

Cenario        | Reducao vazao | Reducao potencia | Economia EUR/ano | Economia BRL/ano
---------------|---------------|------------------|------------------|------------------
Conservador    | -10%          | ~8%              | EUR {econ_10:,.0f}        | R$ {econ_10*5.5:,.0f}
Moderado       | -15%          | ~12%             | EUR {econ_15:,.0f}        | R$ {econ_15*5.5:,.0f}
Otimista       | -20%          | ~15%             | EUR {econ_20:,.0f}        | R$ {econ_20*5.5:,.0f}

Faixas pressupoem que a reducao de vazao NAO comprometa a eficiencia de
captura - o que so pode ser confirmado com a curva real de eficiencia vs. Qa.

================================================================================
5. TRES PERGUNTAS QUE SO A TGBB PODE RESPONDER
================================================================================

1. Qual e a vazao de ar real (Qa) por metro de cortina em Westerdok?
   (medida ou de projeto)

2. A curva potencia x vazao do compressor coincide com a de placa?
   (ou ha desvio por desgaste, contrapressao ou entupimento de difusores?)

3. A profundidade local varia com a mare?
   (e em quanto isso desloca o ponto otimo?)

Se qualquer uma dessas respostas surpreender, ha economia a capturar sem
perda de eficiencia de captura.

================================================================================
6. PROPOSTA: CAMPANHA DE MEDICAO LEVE (TIER 1)
================================================================================

Com 1 semana de medicao leve (potencia, vazao, pressao), e possivel transformar
estas estimativas em numeros verificaveis, com incerteza declarada e
conformidade com ISO 50015 / IPMVP Opcao B.

Sem instrumentacao permanente, sem NDA para esta etapa, sem compromisso de
continuidade.

================================================================================
7. REFERENCIAS
================================================================================

- Rodrigues, M. F.; Rosman, P. C. C.; Silva, R. A. G. (2026). Avaliacao do
  Transporte e da Dispersao de Microplasticos... III FluHidros e X VII ENES.

- Rosman, A. A. C.; Rosman, P. C. C.; Carreira, R. (2024). Deriva de
  Microplasticos Leves Oriundos dos Emissarios de Ipanema e Icarai...

- Carvalho, G. A.; Cabral, A. P.; Fernandez, M. A. S. (2003). Correlacao entre
  o campo de vento medio e um indice que define a intensidade da ressurgencia
  na regiao do Cabo Frio. Anais XI SBSR, p. 1509-1514.

- PDOK - Publieke Dienstverlening Op de Kaart (Kadaster, Holanda).
  https://www.pdok.nl/

- Amsterdam Open Geodata. https://maps.amsterdam.nl/open_geodata/

- Waternet/Tauw (2023). Relatorio de monitoramento Westerdok.

- TGBB (2024). Dados operacionais da barreira Westerdok.

- HarmoniQ (2025). Tarifa industrial de energia, H1 2025.

================================================================================
FIM DO RELATORIO
================================================================================
"""

# Salvar TXT
out_txt = OUT_DIR / "relatorio_tier0_v2.txt"
with open(out_txt, 'w', encoding='utf-8') as f:
    f.write(relatorio)
print(f"\nOK Relatorio salvo: {out_txt}")
print(f"   Tamanho: {out_txt.stat().st_size/1024:.1f} KB")

# Salvar versao curta (cartao de 1 pagina)
cartao = f"""
+--------------------------------------------------------------------------+
|  DIAGNOSTICO RELAMPAGO v2 - Bubble Barrier Westerdok                     |
|  O que os dados publicos (AGORA com batimetria real) dizem               |
+--------------------------------------------------------------------------+

TRES NUMEROS

  ~{consumo:.0f} kWh/ano      Consumo do compressor (~10 kW x 8.760 h)
  ~{custo_kg_EUR:.1f} kWh/kg        Energia por kg de plastico (~1 t/ano)
  ~EUR {custo_kg_EUR:.2f}/kg        Custo de eletricidade ({pct_energia:.0f}% do TCO de EUR {TCO_kg_EUR}/kg)

NOVIDADE: Batimetria real = {H_real} m NAP (PDOK/Amsterdam Open Geodata)
          (Antes: {H_old} m premissa - lacuna metodologica eliminada)

UMA DESCOBERTA (REFORCADA)

  O modelo do dashboard foi calibrado para barreiras de grande porte
  (Q50 = {Q50_old} m3/h/m). Com H = {H_real} m, a engenharia reversa da
  potencia de 10 kW estima vazao de ~{Q_min:.0f}-{Q_max:.0f} m3/h/m -
  UMA ORDEM DE GRANDEZA abaixo do Q50.

  >>> A discrepancia e MAIOR do que estimada antes.
  >>> O potencial de otimizacao e REAL.

TRES PERGUNTAS

  1. Qual e a vazao de ar real (Qa) por metro de cortina?
  2. A curva potencia x vazao coincide com a de placa?
  3. A profundidade local varia com a mare?

SE FAZER SENTIDO

  1 semana de medicao leve (potencia, vazao, pressao) transforma estas
  estimativas em numeros verificaveis (ISO 50015 / IPMVP Opcao B).

  Sem instrumentacao permanente, sem NDA, sem compromisso.

Referencias: WUR/edepot, Waternet/Tauw (2023), TGBB (2024), HarmoniQ (2025),
             PDOK, Amsterdam Open Geodata, Rodrigues et al. (2026),
             Rosman et al. (2024), Carvalho et al. (2003).

Contato: Andre Ribeiro de Rezende | Pesquisador Independente | 2026
+--------------------------------------------------------------------------+
"""

out_cartao = OUT_DIR / "cartao_tier0_v2.txt"
with open(out_cartao, 'w', encoding='utf-8') as f:
    f.write(cartao)
print(f"OK Cartao (1 pagina) salvo: {out_cartao}")

print("\n" + "="*70)
print("RELATORIO TIER 0 v2 GERADO COM SUCESSO!")
print("="*70)
print(f"\nArquivos no Desktop:")
print(f"  1. {out_txt.name} (relatorio completo)")
print(f"  2. {out_cartao.name} (cartao de 1 pagina para enviar)")
print("\nPrincipais mudancas em relacao ao Tier 0 original:")
print(f"  - Profundidade: {H_old} m (premissa) -> {H_real} m (NAP, medido)")
print(f"  - Pressao: {rho*g*H_old/1000:.2f} kPa -> {P_hid:.2f} kPa (+11%)")
print(f"  - Vazao estimada: 13-20 -> {Q_min:.0f}-{Q_max:.0f} m3/h/m (-11%)")
print(f"  - Discrepancia com Q50: REFORCADA (maior do que antes)")
print("="*70)
