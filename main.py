from mem_sim import MemorySimulator
from modules.rep_policy import LRU, SecondChance
from core import MMU

policy = LRU()
mmu = MMU()

mem_simulator = MemorySimulator(mmu=mmu, page_size=4096, num_tlb_entries=16, num_frames=64, rep_policy=policy)


arq_test = open("tests/trace.in", "r")
# arq_test = open("in", "r")

for addr in arq_test:
    mem_simulator.access_memory(int(addr))
mem_simulator.print_statistics()
