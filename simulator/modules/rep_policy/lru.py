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

    def _update_tlb(self, mmu, page_number: int, frame_number: int) -> Optional[int]:
        if len(mmu.tlb) < mmu.num_tlb_entries:
            # tlb is not full yet
            mmu.tlb.append((page_number, frame_number))
            self.update_state(page_number, frame_number)
            return
        
        page_map = self.frequency_list.popleft() # least frequent element in the data structure

        # swap the previous most unvisited page_map with the new
        idx = mmu.tlb.index(page_map)
        mmu.tlb[idx] = (page_number, frame_number)
        self.update_state(page_number, frame_number)

    # def _update_memory(self, frames: List[Optional[int]], tlb: List[Tuple[int, int]], page_table: Dict[int, int], page_number: int) -> int:
    def _update_memory(self, mmu, page_number: int) -> Optional[int]:
        idx = self._search_empty_frame(mmu.frames)
        if idx is not None:
            mmu.frames[idx] = page_number
            mmu.page_table[page_number] = idx
            self.update_state(page_number, idx)
            return idx

        # if memory is full, the replacement policy has to choose which pages to substitute. Notice lu page stands for "least used"
        (lu_page, frame_number) = self.frequency_list.popleft()

        # remove from the page_table and add new mapping
        if lu_page in mmu.page_table:
            del mmu.page_table[lu_page]
        mmu.page_table[page_number] = frame_number

        mmu.frames[frame_number] = page_number
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
        