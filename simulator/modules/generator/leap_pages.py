import random
from typing import List

def _gerar_trace_sequencial_com_saltos(num_enderecos: int, max_pagina: int, prob_salto: int) -> List[str]:
    """
    Algoritmo 2: Localidade Espacial (Sequencial com Saltos).
    
    Simula um programa que acessa endereços de forma sequencial
    (ex: p, p+1, p+2) com uma probabilidade de "salto" para um
    endereço completamente novo (simulando uma chamada de função ou
    acesso a dados distantes).
    """
    trace = []
    if num_enderecos == 0:
        return trace
        
    pagina_atual = random.randint(0, max_pagina)
    trace.append(str(pagina_atual))

    for _ in range(num_enderecos - 1):
        # Gera um número de 0 a 100
        chance = random.randint(0, 100)
        
        if chance < prob_salto:
            # "Salto" para um novo endereço aleatório
            pagina_atual = random.randint(0, max_pagina)
        else:
            # "Passo" sequencial (localidade espacial)
            pagina_atual = (pagina_atual + 1) % (max_pagina + 1)
            
        trace.append(str(pagina_atual))
    return trace