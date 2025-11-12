import random
from typing import List
from .random_pages import _gerar_trace_aleatorio

def _gerar_trace_working_set(num_enderecos: int, max_pagina: int, tamanho_set: int, prob_no_set: int) -> List[str]:
    """
    Algoritmo 3: Localidade Temporal (Working Set).
    
    Simula um programa com um "working set" de páginas "quentes"
    (frequentemente acessadas). A maioria dos acessos (definido
    por prob_no_set) será a uma página dentro desse set.
    Ocasionalmente, uma página "fria" é acessada, e ela substitui
    uma página aleatória no working set.
    """
    trace = []
    if num_enderecos == 0:
        return trace

    # Garante que o tamanho do set não seja maior que o número de páginas
    tamanho_set = min(tamanho_set, max_pagina + 1)
    
    # Inicializa o working set com páginas aleatórias
    working_set = [random.randint(0, max_pagina) for _ in range(tamanho_set)]
    
    if not working_set:
         # Caso extremo: tamanho_set = 0, apenas gera aleatório
         return _gerar_trace_aleatorio(num_enderecos, max_pagina)

    for _ in range(num_enderecos):
        chance = random.randint(0, 100)
        
        pagina_escolhida = 0
        
        if chance < prob_no_set:
            # Acesso "quente" (localidade temporal)
            # Escolhe uma página aleatória DE DENTRO do working set
            pagina_escolhida = random.choice(working_set)
        else:
            # Acesso "frio" (page fault ou transição de contexto)
            # Escolhe uma página aleatória de TODO o espaço de endereçamento
            pagina_escolhida = random.randint(0, max_pagina)
            
            # A nova página "fria" agora se torna "quente"
            # Ela substitui uma página antiga no working set
            indice_para_substituir = random.randint(0, tamanho_set - 1)
            working_set[indice_para_substituir] = pagina_escolhida
            
        trace.append(str(pagina_escolhida))
    return trace