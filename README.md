<img width="1869" height="1024" alt="image" src="https://github.com/user-attachments/assets/b77abb16-97b4-4be3-b444-25d4526d6a5a" />
<img width="1873" height="1020" alt="image" src="https://github.com/user-attachments/assets/53fb6f69-6034-4e3d-9055-2f90ebea9e6d" />
<img width="1875" height="1025" alt="image" src="https://github.com/user-attachments/assets/2ea52bf9-141c-4665-977b-3a08a47b5877" />

# MMU Simulator

A web-based application for simulating the operation of a Memory Management Unit (MMU) and Translation Lookaside Buffer (TLB). This tool is designed for students to visualize and understand page replacement algorithms and the performance impact of a TLB.
It also includes a trace file generator to create custom workloads for testing different simulation scenarios.

## Features

### 1. MMU/TLB Simulator

Configurable Environment: Set the number of TLB entries and the total number of frames in main memory.
Page Replacement Algorithms: Choose between two classic replacement policies for main memory:
LRU (Least Recently Used)
Second Chance (Clock)

Input: Run simulations by either pasting an address trace directly (one page number per line) or by loading a pre-generated test file.

Detailed Statistics:
- TLB Hits
- TLB Misses
- Page Faults

Live Polling: For large simulations, the statistics panel updates in real-time by polling the backend.

Simulation Log: Inspect a detailed, step-by-step log of the simulation's events.

### 2. Trace File Generator

Generate new .in trace files to test specific scenarios.

Generation Algorithms:
- Random: Uniformly random page accesses.
- Sequential with Jumps: Simulates a program with high locality that occasionally jumps to new memory locations.
- Working Set: Models temporal locality by focusing most accesses within a "working set" of pages, which slowly shifts over time.

Custom Parameters: Configure algorithm-specific details like jump probability, working set size, and set access probability.

(Generated files are automatically detected and added to the simulator's "Load from Test File" dropdown, no refresh required.)

## Tech Stack

### Frontend:

HTML5
Tailwind CSS (for styling)
Vanilla JavaScript (ES6+) (for all client-side logic and API communication)

### Backend:
Python: The simulation and generation logic is handled on the server.
FastAPI (or Flask): Serves the html and provides the JSON API endpoints.

## How to Run
This project consists of a Python backend (for the simulation logic) and a static frontend (served by the backend).

**Clone the repository:**

git clone [your-repository-url]
cd [project-directory]


**Create a virtual environment:**
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

**Install dependencies:**
pip install -r requirements.txt

**Run the server:**
bash run.sh

**Open your browser and navigate to the URL provided by uvicorn (usually http://127.0.0.1:8000).**

**How to Use**
- Navigate to the Generator tab.
- Configure the parameters (e.g., 'Working Set' with 10,000 addresses) and click Generate Trace.
- Navigate back to the Simulator tab.
- The new file (e.g., new_trace.in) will now be available in the Load from Test File dropdown. Select it.
- Configure your simulation (e.g., 16 TLB Entries, 64 Frames, LRU).
- Click Run Simulation.
- Observe the statistics and log update. The UI will be disabled while the simulation is in progress.
