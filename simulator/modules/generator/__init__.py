from typing import List, Dict, Any
from .random_pages import _gerar_trace_aleatorio
from .hot_pages import _gerar_trace_working_set
from .leap_pages import _gerar_trace_sequencial_com_saltos

def generate_trace(config: Dict[str, Any]) -> List[str]:
    """
    Função principal que seleciona o algoritmo correto
    com base na configuração.
    """
    algoritmo = config.get("algoritmo")
    num_enderecos = config.get("num_enderecos", 1000)
    max_pagina = config.get("max_pagina", 1023)
    
    try:
        if algoritmo == "aleatorio":
            return _gerar_trace_aleatorio(
                num_enderecos,
                max_pagina
            )
        elif algoritmo == "sequencial_com_saltos":
            return _gerar_trace_sequencial_com_saltos(
                num_enderecos,
                max_pagina,
                config.get("prob_salto", 10)
            )
        elif algoritmo == "working_set":
            return _gerar_trace_working_set(
                num_enderecos,
                max_pagina,
                config.get("tamanho_set", 50),
                config.get("prob_no_set", 90)
            )
        else:
            raise ValueError(f"Algoritmo desconhecido: {algoritmo}")
    except Exception as e:
        return [f"Erro ao gerar trace: {e}"]