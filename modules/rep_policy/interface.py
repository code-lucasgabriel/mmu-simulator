from abc import ABC, abstractmethod
from typing import List, Tuple, Optional

class BaseRepPolicy(ABC):
    def __init__(self, is_tlb):
        self.is_tlb = is_tlb

        if self.is_tlb:
            self.update_table = self._update_tlb
        else:
            self.update_table = self._update_memory

    def update_table(self, *args, **kwargs):
        """
        Public-facing method for all updates.
        
        This method is dynamically assigned in __init__ to point to
        either _update_tlb or _update_memory.
        
        This placeholder definition exists to help IntelliSense and
        to provide a clear error if __init__ fails.
        """

        raise NotImplementedError(
            "update_table was not correctly assigned in __init__. "
            "Ensure super().__init__() is called in the subclass."
        )

    def update_state(self, *args, **kwargs) -> None:
        """
        Optional method to update the state of the program pages

        Used both in LRU and SecondChange

        Returns:
            None
        """
        return

    @abstractmethod
    def _update_tlb(self, *args, **kwargs) -> Optional[int]:
        """
        Updates the TLB with the new page

        Args:
            tlb (List[Tuple[int, int]]): the tlb data structure
            num_tlb_entries (int): the size of the tlb cache
            page_number (int): the virtual address of the page
            frame_number (int): the physical address of the page
        Returns:
            frame_number (int): the frame number the page was allocated to
        """
        pass

    @abstractmethod
    def _update_memory(self, *args, **kwargs) -> int:
        """
        Updates the Frames with the new page

        Args:
            frames (List[int]): the frames data structure
            num_frames (int): the number of frames in the memory
            page_number (int): the virtual address of the page
            frame_number (int): the physical address of the page
        Returns:
            frame_number (int): the frame number the page was allocated to
        """
        pass