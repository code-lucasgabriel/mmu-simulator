import collections
from modules.rep_policy import BaseRepPolicy
from typing import List, Tuple, Optional
from core import Statistics, MMU

class MemorySimulator:
    def __init__(self, mmu: MMU, page_size: int, num_tlb_entries: int, num_frames: int, rep_policy: BaseRepPolicy):
        self.mmu = mmu
        self.page_size = page_size
        self.num_tlb_entries = num_tlb_entries
        self.num_frames = num_frames    
        self.rep_policy = rep_policy

        if str(rep_policy) not in ['LRU', 'SecondChance']:
            raise ValueError("Política de substituição inválida. Use 'LRU' ou 'SecondChance'.")

        # initializes the MMU
        self.mmu.initialize(num_tlb_entries=self.num_tlb_entries, num_frames=num_frames)

    def access_memory(self, virtual_address: int):
        """
        Simula o acesso a um endereço virtual.
        Deve atualizar os contadores e aplicar a política de substituição se necessário.
        """
        page_number = virtual_address # naming convention
        if self.mmu.search_tlb(page_number):
            Statistics.tlb_hits += 1
            return
        
        # if the vpn wasn't found in the tlb, then it is a tlb_miss
        Statistics.tlb_misses+=1

        frame_number = self.mmu.get_frame_number(page_number)

        if frame_number is None:
            # if the vpn wasn't found in the memory, then it's a page_fault
            Statistics.page_faults += 1
            # stores the new page_number in the memory and return the associated frame
            frame_number = self.mmu.store_page_frame(self.rep_policy, self.num_frames, page_number)
            
        # after retrieving the frame_number, add (page_number, frame_number) to the tlb
        self.mmu.store_page_tlb(self.num_tlb_entries, page_number, frame_number)
        

    def print_statistics(self):
        print("=" * 60)
        print("SIMULADOR DE MEMÓRIA - Estatísticas de Acesso")
        print("=" * 60)
        print(f"Política de Substituição:   {self.rep_policy}")
        print(f"Tamanho da Página:          {self.page_size} bytes")
        print(f"Entradas na TLB:            {self.num_tlb_entries}")
        print(f"Número de Frames:           {self.num_frames}")
        print("-" * 60)
        print(f"TLB Hits:                   {Statistics.tlb_hits:,}")
        print(f"TLB Misses:                 {Statistics.tlb_misses:,}")
        print(f"Page Faults:                {Statistics.page_faults:,}")
        print("=" * 60)


    #* Custom implemented methods
    def set_rep_policy(self, new_rep_policy: BaseRepPolicy):
        """
        Method for changing the Replacement Policy of the MemorySimulator object (allows for changes during runtime, due to the 'Strategy Pattern' design chosen for the policy algorithms implementation).
        """
        if new_rep_policy not in ['LRU', 'SecondChance']:
            raise ValueError("Política de substituição inválida. Use 'LRU' ou 'SecondChance'.")
        self.rep_policy = new_rep_policy
        print(f"Replacement policy changed to {self.rep_policy}")


