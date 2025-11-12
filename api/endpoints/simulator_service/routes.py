from fastapi import APIRouter, Body, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from typing import List, Iterable, Optional

from simulator.core import Statistics, MMU
from simulator.modules.rep_policy import LRU
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
    return FileResponse(STATIC_DIR / "simulator.html")

# --- NEW ENDPOINT ---
@simulator_router.get("/list-tests")
def list_test_files():
    """
    Lists the available test files from the /simulator/tests/ directory.
    """
    if not TESTS_DIR.is_dir():
        return {"tests": []} # Return empty if dir doesn't exist
    
    try:
        # Get all files, filter for .in or .txt
        test_files = [
            f for f in os.listdir(TESTS_DIR) 
            if os.path.isfile(TESTS_DIR / f) and (f.endswith('.in') or f.endswith('.txt'))
        ]
        return {"tests": test_files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading test directory: {e}")

# --- NEW ENDPOINT ---
@simulator_router.get("/get-test/{test_name}")
def get_test_file_content(test_name: str):
    """
    Returns the content of a specific test file.
    Includes security check to prevent directory traversal.
    """
    try:
        # --- Security Check ---
        # 1. Resolve the real path
        file_path = (TESTS_DIR / test_name).resolve()
        
        # 2. Verify it's still inside the TESTS_DIR
        if not file_path.is_file() or not str(file_path).startswith(str(TESTS_DIR.resolve())):
            raise HTTPException(status_code=404, detail="File not found or access denied.")
        
        # 3. Return as plain text
        return FileResponse(file_path, media_type="text/plain")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- RE-IMPLEMENTED: Endpoint for Live Stats ---
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
    # 1. Reset statistics and logs for this run
    Statistics.reset()

    # 2. Select the replacement policy
    if config.rep_policy == "LRU":
        policy = LRU(is_tlb=False)
    # elif config.rep_policy == "SecondChance":
    #     policy = SecondChance(is_tlb=False)
    else:
        # Default to LRU if invalid policy is somehow sent
        policy = LRU(is_tlb=False)
        Statistics.log(f"Warning: Invalid policy '{config.rep_policy}' received. Defaulting to LRU.")

    # 3. Initialize the simulator
    mmu = MMU()
    # --- Store hardcoded page_size for later ---
    page_size = 4096 
    mem_simulator = MemorySimulator(
        mmu=mmu,
        page_size=page_size, # Use the variable
        num_tlb_entries=config.tlb_entries,
        num_frames=config.num_frames,
        rep_policy=policy
    )

    # --- 4. ROBUST: Determine address source ---
    address_iterator: Iterable[str]

    if config.test_file:
        # --- A. Use Test File (Stream from disk) ---
        Statistics.log(f"Loading from test file: {config.test_file}")
        
        # Security check (copied from /get-test/ endpoint)
        file_path = (TESTS_DIR / config.test_file).resolve()
        
        if not file_path.is_file() or not str(file_path).startswith(str(TESTS_DIR.resolve())):
            Statistics.log(f"Error: Invalid or non-existent test file '{config.test_file}'.")
            raise HTTPException(status_code=400, detail="Invalid test file selected.")
        
        # Create a generator function to stream the file line by line
        # This does NOT load the whole file into memory
        def file_streamer(path: Path) -> Iterable[str]:
            with open(path, 'r') as f:
                for line in f:
                    yield line
        
        address_iterator = file_streamer(file_path)

    elif config.addresses is not None:
        # --- B. Use Manual Input String ---
        # This block now correctly handles `addresses: ""` (empty string)
        # which Pydantic does NOT convert to None.
        Statistics.log("Loading from manual address trace.")
        address_iterator = config.addresses.strip().split('\n')
    
    else:
        # --- C. No Input ---
        # This is the error you were seeing. It happens when BOTH
        # test_file AND addresses are 'None' in the JSON.
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

    # 6. Return the results
    final_stats = Statistics.get_stats()
    
    # --- MODIFIED: Handle large logs ---
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

# --- RE-IMPLEMENTED: simulation endpoint is async ---
@simulator_router.post("/run-simulation", response_model=SimulationResult)
async def run_simulation(config: SimulationConfig):
    """
    Runs the memory simulation based on the provided config.
    It runs the synchronous (blocking) simulation in a separate thread
    using 'asyncio.to_thread' so it doesn't block the main server.
    This allows the '/current-stats' endpoint to remain responsive.
    """
    try:
        # Run the blocking function in a thread pool
        result = await asyncio.to_thread(_run_simulation_logic, config)
        return result
    except Exception as e:
        # Handle exceptions that might occur during the sim
        # This will now correctly pass the 400 error message if it happens
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
        # 1. Resolve o caminho de saída e faz a verificação de segurança
        file_path = (TESTS_DIR / config.nome_arquivo).resolve()
        
        if not str(file_path).startswith(str(TESTS_DIR.resolve())):
            raise HTTPException(status_code=400, detail="Nome de arquivo ou caminho inválido.")
            
        if file_path.exists():
            raise HTTPException(status_code=400, detail=f"O arquivo '{config.nome_arquivo}' já existe.")
            
        # 2. Converte o modelo Pydantic em um dicionário para a função
        config_dict = config.model_dump()
        
        # 3. Gera o trace (é uma operação síncrona, rodamos em thread)
        trace_list = await asyncio.to_thread(generate_trace, config_dict)
        
        # 4. Formata o conteúdo do arquivo
        trace_content = "\n".join(trace_list)
        
        # 5. Salva o arquivo (também em thread para não bloquear)
        def save_file():
            try:
                # Cria o diretório de testes se não existir
                TESTS_DIR.mkdir(parents=True, exist_ok=True)
                with open(file_path, 'w') as f:
                    f.write(trace_content)
            except Exception as e:
                # Esta exceção será capturada pelo bloco try/except externo
                raise IOError(f"Falha ao salvar o arquivo: {e}")

        await asyncio.to_thread(save_file)

        return JSONResponse(
            status_code=201, # 201 Created
            content={"message": f"Arquivo '{config.nome_arquivo}' gerado com sucesso!", "filename": config.nome_arquivo}
        )

    except HTTPException as e:
        # Re-levanta exceções HTTP (como "Arquivo já existe")
        raise e
    except Exception as e:
        # Captura outros erros (ex: falha de permissão de escrita)
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {str(e)}")
