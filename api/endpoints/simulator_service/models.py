from pydantic import BaseModel, Field
from typing import List, Optional

class SimulationConfig(BaseModel):
    """Defines the configuration sent from the frontend."""
    tlb_entries: int
    num_frames: int
    rep_policy: str
    addresses: Optional[str] = None
    test_file: Optional[str] = None

class SimulationStats(BaseModel):
    """Defines the statistics returned to the frontend."""
    tlb_hits: int
    tlb_misses: int
    page_faults: int

class SimulationResult(BaseModel):
    """Defines the full simulation result payload."""
    logs: List[str]
    statistics: SimulationStats

class TraceGenerationConfig(BaseModel):
    """Define a configuração para o novo gerador de trace."""
    
    algoritmo: str
    nome_arquivo: str = Field(..., pattern=r"^[a-zA-Z0-9_\-]+\.(in|txt)$")
    num_enderecos: int = Field(..., gt=0) # should be > 0
    max_pagina: int = Field(..., ge=0) # should be >= 0
    
    prob_salto: Optional[int] = Field(None, ge=0, le=100) # %
    tamanho_set: Optional[int] = Field(None, ge=0)
    prob_no_set: Optional[int] = Field(None, ge=0, le=100) # %