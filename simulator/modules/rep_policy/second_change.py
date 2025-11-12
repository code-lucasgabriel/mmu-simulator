from typing import List, Tuple, Dict, Optional
from collections import deque
from .interface import BaseRepPolicy

class SecondChance(BaseRepPolicy):
    """
    Implements the Second Chance (Clock) page replacement policy for memory.

    This policy maintains a circular queue (the 'clock') of pages in memory.
    Each page has a reference bit (R-bit).
    - When a page is loaded, it's added to the clock and its R-bit is set to 1.
    - When a replacement is needed, the policy checks the page at the 'hand'
      of the clock (front of the deque):
        - If R-bit is 1: Clear it to 0 (giving a second chance) and move the
          page to the back of the queue.
        - If R-bit is 0: This page is the victim and gets replaced.
    
    Note: Based on the provided MMU structure, the R-bit is only set to 1
    when a page is first loaded (in update_state). The MMU does not
    provide a hook to set the R-bit on subsequent *hits*.
    """

    def __init__(self, is_tlb: int = False):
        # Per the prompt, this policy is explicitly for memory, not TLB
        super().__init__(is_tlb=False) 
        
        # The 'clock' is a circular buffer of pages in memory
        # It stores tuples of (page_number, frame_number)
        self.clock = deque()
        
        # Stores the reference bit (R-bit) for each page
        self.reference_bits: Dict[int, int] = {} # Maps page_number -> r_bit (0 or 1)
        
        self._memory_full = False

    def __str__(self) -> str:
        return "SecondChance"

    def update_state(self, page_number: int, frame_number: int):
        """
        Adds a new page to the clock structure when it's loaded into memory.
        
        This method is called by _update_memory when a page is 
        placed into a frame. We set its reference bit to 1, as it was 
        just referenced (loaded).
        """
        # We assume this page is not already in the clock,
        # as this is called only when a page is added to a frame.
        self.clock.append((page_number, frame_number))
        self.reference_bits[page_number] = 1 

    def _update_tlb(self, mmu, page_number: int, frame_number: int) -> Optional[int]:
        """
        This policy is not designed for the TLB.
        The BaseRepPolicy will not call this if __init__ sets is_tlb=False.
        """
        raise NotImplementedError("SecondChance policy is not intended for TLB use.")

    def _update_memory(self, mmu, page_number: int) -> Optional[int]:
        """
        Updates the memory (frames) with the new page.
        Uses the Second Chance (Clock) algorithm if memory is full.
        """
        # First, try to find an empty frame
        idx = self._search_empty_frame(mmu.frames)
        if idx is not None:
            # Found an empty frame. Place the page here.
            mmu.frames[idx] = page_number
            mmu.page_table[page_number] = idx
            
            # Add the new page to our clock and set its R-bit
            self.update_state(page_number, idx) 
            return idx

        # If no empty frame, memory is full. Run the Clock algorithm.
        while True:
            # Get the page at the 'hand' of the clock (front of the queue)
            (victim_page, frame_number) = self.clock.popleft()

            # Check its reference bit, default to 0 if not found
            if self.reference_bits.get(victim_page, 0) == 1:
                # R-bit is 1. Give it a "second chance".
                # Clear the bit and move it to the back of the queue.
                self.reference_bits[victim_page] = 0
                self.clock.append((victim_page, frame_number))
            else:
                # R-bit is 0. This is our victim.
                # It has already been removed from the clock (popleft).
                
                # Clean up its R-bit entry
                if victim_page in self.reference_bits:
                    del self.reference_bits[victim_page]
                
                # Evict the victim page:
                
                # 1. Remove its mapping from the page table
                if victim_page in mmu.page_table:
                    del mmu.page_table[victim_page]
                
                # 2. Add mapping for the new page
                mmu.page_table[page_number] = frame_number

                # 3. Update the physical frame itself
                mmu.frames[frame_number] = page_number

                # 4. Add the new page to our clock
                self.update_state(page_number, frame_number)
                
                # Return the frame number that was used
                return frame_number

    def _search_empty_frame(self, frames: List[Optional[int]]) -> Optional[int]:
        """
        Helper function to find the first empty frame (contains None).
        Copied from the provided LRU implementation.
        """
        try:
            # Find the index of the first 'None' in the frames list
            idx = frames.index(None)
        except ValueError: # No 'None' was found
            idx = None
            pass
        
        if idx is None:
            self._memory_full = True
        return idx