#!/usr/bin/env python3
"""
Gerador de Malha Gmsh 2.2 com ordem correta de nós para prismas.
Gera uma malha simples de canal retangular para teste inicial.
"""
import numpy as np
from pathlib import Path

# Configurações da malha
OUTPUT_DIR = Path("/home/engracia/EHD8L_BaiaGuanabara/04_OpenFOAM_Case")
OUTPUT_MSH = OUTPUT_DIR / "malha_guanabara.msh"

# Dimensões do domínio (metros) - canal retangular simples
LX = 1000.0  # Comprimento X
LY = 500.0   # Largura Y
LZ = 10.0    # Profundidade Z

# Resolução da malha
NX = 20  # Células em X
NY = 10  # Células em Y
NZ = 5   # Células em Z (profundidade)

print("="*70)
print("GERANDO MALHA GMESH 2.2 - ORDEM CORRETA DE NÓS")
print("="*70)
print(f"Domínio: {LX}m x {LY}m x {LZ}m")
print(f"Resolução: {NX} x {NY} x {NZ} = {NX*NY*NZ} células")

def gerar_malha():
    with open(OUTPUT_MSH, 'w') as f:
        # Cabeçalho Gmsh 2.2
        f.write("$MeshFormat\n")
        f.write("2.2 0 8\n")
        f.write("$EndMeshFormat\n")
        
        # Gerar nós (grid estruturado)
        num_nos_x = NX + 1
        num_nos_y = NY + 1
        num_nos_z = NZ + 1
        total_nos = num_nos_x * num_nos_y * num_nos_z
        
        f.write(f"$Nodes\n")
        f.write(f"{total_nos}\n")
        
        no_id = 1
        nos = {}  # Dicionário para mapear (i,j,k) -> no_id
        
        for k in range(num_nos_z):
            for j in range(num_nos_y):
                for i in range(num_nos_x):
                    x = i * LX / NX
                    y = j * LY / NY
                    z = k * LZ / NZ
                    f.write(f"{no_id} {x:.6f} {y:.6f} {z:.6f}\n")
                    nos[(i, j, k)] = no_id
                    no_id += 1
        
        f.write("$EndNodes\n")
        
        # Gerar elementos (hexaedros tipo 5 no Gmsh)
        # Hexaedro: 8 nós, ordem: base inferior (anti-horário) + base superior (anti-horário)
        # Ordem correta: n1 n2 n3 n4 (base inf) n5 n6 n7 n8 (base sup)
        # onde n5 está acima de n1, n6 acima de n2, etc.
        
        num_hex = NX * NY * NZ
        num_elem_total = num_hex  # Apenas hexaedros de volume
        
        f.write(f"$Elements\n")
        f.write(f"{num_elem_total}\n")
        
        elem_id = 1
        for k in range(NZ):
            for j in range(NY):
                for i in range(NX):
                    # 8 nós do hexaedro
                    n1 = nos[(i, j, k)]
                    n2 = nos[(i+1, j, k)]
                    n3 = nos[(i+1, j+1, k)]
                    n4 = nos[(i, j+1, k)]
                    n5 = nos[(i, j, k+1)]
                    n6 = nos[(i+1, j, k+1)]
                    n7 = nos[(i+1, j+1, k+1)]
                    n8 = nos[(i, j+1, k+1)]
                    
                    # Tipo 5 = Hexaedro, Physical ID 10 = Volume
                    f.write(f"{elem_id} 5 2 10 0 {n1} {n2} {n3} {n4} {n5} {n6} {n7} {n8}\n")
                    elem_id += 1
        
        f.write("$EndElements\n")
    
    print(f"\n✓ Malha gerada: {OUTPUT_MSH}")
    print(f"  Tamanho: {OUTPUT_MSH.stat().st_size / 1024:.1f} KB")
    print(f"  Total de nós: {total_nos}")
    print(f"  Total de elementos: {num_elem_total}")

if __name__ == "__main__":
    gerar_malha()
    print("="*70)
    print("PRÓXIMO PASSO: gmshToFoam malha_guanabara.msh")
    print("="*70)
