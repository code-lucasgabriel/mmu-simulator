import random
from typing import List

def _gerar_trace_aleatorio(num_enderecos: int, max_pagina: int) -> List[str]:
    """
    Algoritmo 1: Geração Completamente Aleatória.
    
    Gera uma lista de endereços (páginas) puramente aleatórios
    dentro do intervalo [0, max_pagina].
    """
    trace = []
    for _ in range(num_enderecos):
        pagina = random.randint(0, max_pagina)
        trace.append(str(pagina))
    return trace