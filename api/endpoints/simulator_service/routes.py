from fastapi import APIRouter, Body, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from typing import List, Iterable, Optional

from simulator.core import Statistics, MMU
from simulator.modules.rep_policy import LRU, SecondChance
from simulator.modules.generator import generate_trace
from simulator.mem_sim import MemorySimulator

from api.endpoints.simulator_service.models import SimulationConfig, SimulationResult, SimulationStats, TraceGenerationConfig
from pathlib import Path
import os
import asyncio

# --- Define Base Directory ---
BASE_DIR = Path(__file__).parent 
STATIC_DIR = BASE_DIR / "static" 
ROOT_DIR = BASE_DIR.parent.parent.parent
TESTS_DIR = ROOT_DIR / "simulator" / "tests"


simulator_router = APIRouter()

@simulator_router.get("/")
def get_simulator_page():
    """
    Serves the main HTML page for the simulator.
    """
    return FileResponse(STATIC_DIR / "index.html")

@simulator_router.get("/list-tests")
def list_test_files():
    """
    Lists the available test files from the /simulator/tests/ directory.
    """
    if not TESTS_DIR.is_dir():
        return {"tests": []} # return empty if dir doesn't exist
    
    try:
        # get all files, filter for .in or .txt
        test_files = [
            f for f in os.listdir(TESTS_DIR) 
            if os.path.isfile(TESTS_DIR / f) and (f.endswith('.in') or f.endswith('.txt'))
        ]
        return {"tests": test_files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading test directory: {e}")

@simulator_router.get("/get-test/{test_name}")
def get_test_file_content(test_name: str):
    """
    Returns the content of a specific test file.
    Includes security check to prevent directory traversal.
    """
    try:
        file_path = (TESTS_DIR / test_name).resolve()
        
        if not file_path.is_file() or not str(file_path).startswith(str(TESTS_DIR.resolve())):
            raise HTTPException(status_code=404, detail="File not found or access denied.")

        return FileResponse(file_path, media_type="text/plain")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@simulator_router.get("/current-stats", response_model=SimulationStats)
def get_current_stats():
    """
    Returns the current statistics from the singleton.
    This allows the frontend to poll for live updates.
    """
    return Statistics.get_stats()


def _run_simulation_logic(config: SimulationConfig) -> SimulationResult:
    """
    This is the actual synchronous, blocking simulation logic.
    It will be run in a separate thread.
    """
    Statistics.reset()

    if config.rep_policy == "LRU":
        policy = LRU(is_tlb=False)
    elif config.rep_policy == "SecondChance":
        policy = SecondChance(is_tlb=False)
    else:
        # default to LRU if invalid policy is (somehow, maybe api call capture) sent
        policy = LRU(is_tlb=False)
        Statistics.log(f"Warning: Invalid policy '{config.rep_policy}' received. Defaulting to LRU.")

    mmu = MMU()
    page_size = 4096 
    mem_simulator = MemorySimulator(
        mmu=mmu,
        page_size=page_size,
        num_tlb_entries=config.tlb_entries,
        num_frames=config.num_frames,
        rep_policy=policy
    )

    address_iterator: Iterable[str]

    if config.test_file:
        Statistics.log(f"Loading from test file: {config.test_file}")
        
        file_path = (TESTS_DIR / config.test_file).resolve()
        
        if not file_path.is_file() or not str(file_path).startswith(str(TESTS_DIR.resolve())):
            Statistics.log(f"Error: Invalid or non-existent test file '{config.test_file}'.")
            raise HTTPException(status_code=400, detail="Invalid test file selected.")
        
        # create a generator function to stream the file line by line
        # this does NOT load the whole file into memory
        def file_streamer(path: Path) -> Iterable[str]:
            with open(path, 'r') as f:
                for line in f:
                    yield line
        
        address_iterator = file_streamer(file_path)

    elif config.addresses is not None:
        Statistics.log("Loading from manual address trace.")
        address_iterator = config.addresses.strip().split('\n')
    
    else:
        Statistics.log("Error: No addresses or test file provided.")
        raise HTTPException(status_code=400, detail="No address source provided (neither 'addresses' nor 'test_file').")
    
    for addr_str in address_iterator:
        addr_str_clean = addr_str.strip()
        if not addr_str_clean: # Skip empty lines
            continue
            
        try:
            addr = int(addr_str_clean)
            mem_simulator.access_memory(addr)
        except ValueError:
            Statistics.log(f"Skipping invalid address: '{addr_str_clean}'")
        except Exception as e:
            Statistics.log(f"Error processing address '{addr_str_clean}': {e}")

    final_stats = Statistics.get_stats()
    
    logs_to_return = [
            "=" * 60,
            "SIMULADOR DE MEMÓRIA - Estatísticas de Acesso",
            "=" * 60,
            f"Política de Substituição:   {config.rep_policy}",
            f"Tamanho da Página:            {page_size} bytes",
            f"Entradas na TLB:              {config.tlb_entries}",
            f"Número de Frames:             {config.num_frames}",
            "-" * 60,
            f"TLB Hits:                     {Statistics.tlb_hits:,}",
            f"TLB Misses:                   {Statistics.tlb_misses:,}",
            f"Page Faults:                  {Statistics.page_faults:,}",
            "=" * 60,
            "",
        ]

    errors = False
    for log_line in Statistics.logs:
        if "Skipping invalid address:" in log_line or "Error processing address" in log_line:
            if not errors:
                logs_to_return.append("--- LINES BELOW WERE NOT PROCESSED DUE TO INVALID ADRESS ---")
                errors = True
            logs_to_return.append(log_line)

    return SimulationResult(
        logs=logs_to_return,
        statistics=SimulationStats(**final_stats)
    )

@simulator_router.post("/run-simulation", response_model=SimulationResult)
async def run_simulation(config: SimulationConfig):
    """
    Runs the memory simulation based on the provided config.
    It runs the synchronous (blocking) simulation in a separate thread
    using 'asyncio.to_thread' so it doesn't block the main server.
    This allows the '/current-stats' endpoint to remain responsive.
    """
    try:
        result = await asyncio.to_thread(_run_simulation_logic, config)
        return result
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"An error occurred during simulation: {str(e)}")
    
@simulator_router.post("/gerar-trace")
async def gerar_trace_file(config: TraceGenerationConfig):
    """
    Gera um novo arquivo de trace com base nos parâmetros
    e o salva no diretório /simulator/tests/
    """
    try:
        file_path = (TESTS_DIR / config.nome_arquivo).resolve()
        
        if not str(file_path).startswith(str(TESTS_DIR.resolve())):
            raise HTTPException(status_code=400, detail="Nome de arquivo ou caminho inválido.")
            
        if file_path.exists():
            raise HTTPException(status_code=400, detail=f"O arquivo '{config.nome_arquivo}' já existe.")
            
        config_dict = config.model_dump()
        
        trace_list = await asyncio.to_thread(generate_trace, config_dict)
        
        trace_content = "\n".join(trace_list)
        
        def save_file():
            try:
                TESTS_DIR.mkdir(parents=True, exist_ok=True)
                with open(file_path, 'w') as f:
                    f.write(trace_content)
            except Exception as e:
                raise IOError(f"Falha ao salvar o arquivo: {e}")

        await asyncio.to_thread(save_file)

        return JSONResponse(
            status_code=201, # 201 Created
            content={"message": f"Arquivo '{config.nome_arquivo}' gerado com sucesso!", "filename": config.nome_arquivo}
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {str(e)}")
