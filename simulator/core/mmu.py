from typing import List, Tuple, Optional, Dict
from simulator.modules.rep_policy import BaseRepPolicy, LRU

"""
Clas that represents the MMU and holds it's state variables.
"""

class MMU:
    def __init__(self):
        self.tlb: List[Tuple[int, int]] = [] # maps vpn to ppn
        self.page_table: Dict[int, int] = {} # maps vpn to ppn
        self.frames: List[Optional[int]] = []
        self.num_tlb_entries = 0
        self.tlb_rep_policy = LRU(is_tlb=True) # tlb replacement policy is necessarily LRU

    def initialize(self, num_tlb_entries: int , num_frames: int):
        """this method reset/initialize the MMU."""
        self.tlb = []
        self.page_table = {}
        self.frames = [None] * num_frames
        self.num_tlb_entries = num_tlb_entries
    
    def get_frame_number(self, page_number: int) -> Optional[int]:
        return self.page_table.get(page_number, None) # if none, the page isn't in memory
    
    def search_tlb(self, page_number: int) -> Optional[int]:
        for (vpn, ppn) in self.tlb:
            if vpn == page_number:
                self.tlb_rep_policy.update_state(vpn, ppn)
                return ppn
            
        return None

    def store_page_tlb(self, page_number: int, frame_number: int) -> None:
        """
        Updates the tlb with (page_number, frame_number) using the default TLU replacement policy.
        """
        self.tlb_rep_policy.update_table(self, page_number, frame_number)

    def store_page_frame(self, rep_policy: BaseRepPolicy, page_number: int) -> int:
        """
        stores a new frame into memory, using rep_policy if needed to substitute an existing frame.
        """
        frame_number = rep_policy.update_table(self, page_number)
        return frame_number
