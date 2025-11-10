from typing import List
"""
as the statistics tracks global values in the program, a singleton class were creted to update those value. Its clean and neat :)
"""

class Statistics:
    tlb_hits = 0
    tlb_misses = 0
    page_faults = 0
    logs: List[str] = []
    
    @classmethod
    def reset(cls):
        cls.tlb_hits = 0
        cls.tlb_misses = 0
        cls.page_faults = 0
    
    @classmethod
    def log(cls, message: str):
        """Adds a log message to the simulation output."""
        cls.logs.append(message)

    @classmethod
    def get_stats(cls):
        """Returns a dictionary of the final statistics."""
        return {
            "tlb_hits": cls.tlb_hits,
            "tlb_misses": cls.tlb_misses,
            "page_faults": cls.page_faults,
        }
    
    @classmethod
    def display(cls):
        print(f"TLB Hits: {cls.tlb_hits}")
        print(f"TLB Misses: {cls.tlb_misses}")
        print(f"Page Faults: {cls.page_faults}")
