from typing import List, Tuple, Dict, Optional
from .interface import BaseRepPolicy
from collections import deque

class LRU(BaseRepPolicy):
    def __init__(self, is_tlb: int = False):
        self.frequency_list = deque()
        # set is_tlb to the correct value, so update_table receives the correct parameters and perform the correct behavior. Very neat, as the superclass is the one who defines which update_table to use
        super().__init__(is_tlb)
        self._memory_full = False

    def __str__(self) -> str:
        return "LRU"
    
    def update_state(self, page_number: int, frame_number: int):
        """
        Method to update the frequency list counter.

        Used when a page is added to the TLB or used.
        """
        try:
            self.frequency_list.remove((page_number, frame_number))
        except:
            # page not in the list, can skip and append it to the data structure.
            pass
        self.frequency_list.append((page_number, frame_number))

    def _update_tlb(self, tlb: List[Tuple[int, int]], num_tlb_entries: int, page_number: int, frame_number: int) -> Optional[int]:
        if len(tlb) < num_tlb_entries:
            # tlb is not full yet
            tlb.append((page_number, frame_number))
            self.update_state(page_number, frame_number)
            return
        
        page_map = self.frequency_list.popleft() # least frequent element in the data structure

        # swap the previous most unvisited page_map with the new
        idx = tlb.index(page_map)
        tlb[idx] = (page_number, frame_number)
        self.update_state(page_number, frame_number)

    def _update_memory(self, frames: List[Optional[int]], page_table: Dict[int, int], page_number: int) -> int:
        if not self._memory_full:
            idx = self._search_empty_frame(frames)
            if idx is not None:
                frames[idx] = page_number
                page_table[page_number] = idx
                self.update_state(page_number, idx)
                return idx

        # if memory is full, the replacement policy has to choose which pages to substitute. Notice lu page stands for "least used"
        (lu_page, frame_number) = self.frequency_list.popleft()
        frames[frame_number] = page_number
        self.update_state(page_number, frame_number)
        return frame_number

    def _search_empty_frame(self, frames: List[Optional[int]]) -> Optional[int]:
        try:
            idx = frames.index(None)
        except:
            idx = None
            pass
        if idx is None:
            self._memory_full = True
        return idx
        