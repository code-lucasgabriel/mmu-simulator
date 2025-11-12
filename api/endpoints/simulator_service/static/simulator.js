// Get references to all our DOM elements
const simForm = document.getElementById('sim-form');
const runButton = document.getElementById('run-button');
const loadingIndicator = document.getElementById('loading-indicator');

const logOutput = document.getElementById('log-output');
const statTlbHits = document.getElementById('stat-tlb-hits');
const statTlbMisses = document.getElementById('stat-tlb-misses');
const statPageFaults = document.getElementById('stat-page-faults');

const testFileSelect = document.getElementById('test_file');
const addressesTextarea = document.getElementById('addresses');

// --- RE-IMPLEMENT: Get all form inputs to disable them ---
const tlbEntriesInput = document.getElementById('tlb_entries');
const numFramesInput = document.getElementById('num_frames');
const repPolicySelect = document.getElementById('rep_policy');

// List of all inputs in the SIMULATOR form
const formInputs = [
    runButton,
    tlbEntriesInput,
    numFramesInput,
    repPolicySelect,
    testFileSelect,
    addressesTextarea
];

// --- RE-IMPLEMENT: Interval IDs for polling and animation ---
let statsInterval = null;
let loadingInterval = null;

// --- RE-IMPLEMENT: Function to toggle all inputs ---
function setInputsDisabled(disabled) {
    formInputs.forEach(input => {
        if (input) { // Add a check in case an element isn't found
            input.disabled = disabled;
        }
    });
}

// --- RE-IMPLEMENT: Function to start the log animation ---
function startLogAnimation() {
    let dots = 0;
    logOutput.textContent = 'Running simulation';
    loadingInterval = setInterval(() => {
        dots = (dots + 1) % 4;
        logOutput.textContent = `Running simulation${'.'.repeat(dots)}`;
    }, 500);
}

// --- RE-IMPLEMENT: Function to stop the log animation ---
function stopLogAnimation() {
    if (loadingInterval) {
        clearInterval(loadingInterval);
        loadingInterval = null;
    }
}

// --- RE-IMPLEMENT: Function to poll for live stats ---
async function pollStats() {
    try {
        const response = await fetch('/current-stats');
        if (!response.ok) return; // Silently fail if server is busy
        
        const stats = await response.json();
        
        // Update stats UI
        statTlbHits.textContent = stats.tlb_hits.toLocaleString();
        statTlbMisses.textContent = stats.tlb_misses.toLocaleString();
        statPageFaults.textContent = stats.page_faults.toLocaleString();

    } catch (error) {
        // Silently ignore errors, as the main fetch will handle the final one
        console.warn("Stats poll failed:", error);
    }
}


// --- FUNCTION: Load test files into dropdown ---
async function loadTestFiles() {
    try {
        // --- FIX: Removed /simulator/ prefix as requested ---
        const response = await fetch('/list-tests');
        if (!response.ok) {
            throw new Error('Failed to load test list');
        }
        const data = await response.json();
        
        if (data.tests && data.tests.length > 0) {
            data.tests.forEach(filename => {
                const option = new Option(filename, filename);
                testFileSelect.add(option);
            });
        } else {
            // No tests found, disable the selector
            testFileSelect.disabled = true;
            const option = new Option("No test files found", "");
            option.disabled = true;
            testFileSelect.add(option);
        }
    } catch (error) {
        console.error('Error loading test files:', error);
        testFileSelect.disabled = true;
        const option = new Option("Error loading tests", "");
        option.disabled = true;
        testFileSelect.add(option);
    }
}

// --- LISTENER: Handle test file selection ---
testFileSelect.addEventListener('change', async () => {
    const selectedFile = testFileSelect.value;
    
    if (selectedFile) {
        // A file is selected.
        // --- DO NOT FETCH CONTENT ---
        // Just disable the textarea and show a message.
        addressesTextarea.value = `Test file selected:\n${selectedFile}\n\n(Manual input is disabled)`;
        addressesTextarea.disabled = true; // Disable textarea
    } else {
        // "-- Manual Input --" is selected
        addressesTextarea.disabled = false; // Re-enable textarea
        addressesTextarea.value = ''; // Clear it
        addressesTextarea.placeholder = '100\n101\n100\n102\n...';
    }
});

// --- Call the function to load tests when the page loads ---
// document.addEventListener('DOMContentLoaded', loadTestFiles);
// This is moved to the main DOMContentLoaded listener at the end


// --- RE-IMPLEMENTED: Listen for the main form submission ---
simForm.addEventListener('submit', async (event) => {
    event.preventDefault(); // Stop the form from reloading the page

    // --- FIX: ---
    // We MUST get the form data *before* we disable the inputs,
    // otherwise formData.get() will return null for everything.

    // --- 1. Get form data FIRST ---
    const formData = new FormData(simForm);
    const selectedTestFile = formData.get('test_file');

    // --- 2. Build the config object ---
    const tlb_entries = parseInt(formData.get('tlb_entries'), 10) || 16;
    const num_frames = parseInt(formData.get('num_frames'), 10) || 64;
    const rep_policy = formData.get('rep_policy') || 'LRU';

    const config = {
        tlb_entries: tlb_entries,
        num_frames: num_frames,
        rep_policy: rep_policy,
        addresses: null,
        test_file: null
    };

    if (selectedTestFile) {
        config.test_file = selectedTestFile;
    } else {
        // This will now correctly be an empty string "" if left blank
        config.addresses = formData.get('addresses'); 
    }

    // --- 3. Log the (now correct) config object ---
    console.log("Sending this JSON to /run-simulation:", JSON.stringify(config, null, 2));


    // --- 4. NOW, disable inputs and start loading ---
    setInputsDisabled(true); // This now disables ALL inputs
    runButton.textContent = 'Running...'; // Text content is fine, button is disabled
    loadingIndicator.classList.remove('hidden');
    startLogAnimation();

    // --- 5. Clear previous results ---
    statTlbHits.textContent = '0';
    statTlbMisses.textContent = '0';
    statPageFaults.textContent = '0';

    // --- 6. Start live polling ---
    statsInterval = setInterval(pollStats, 1000); // Poll every 1 second

    
    let results; // To store final results

    try {
        // --- 7. Make the (long) API call ---
        const response = await fetch('/run-simulation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(config),
        });

        // --- UPDATED ERROR HANDLING ---
        if (!response.ok) {
            const errorData = await response.json();
            
            let errorMessage = 'Simulation failed'; // Default message
            if (errorData.detail) {
                if (typeof errorData.detail === 'string') {
                    // It's a simple string, great!
                    errorMessage = errorData.detail;
                } else if (Array.isArray(errorData.detail) && errorData.detail.length > 0) {
                    // It's a Pydantic validation array, take the first message
                    errorMessage = errorData.detail[0].msg || JSON.stringify(errorData.detail);
                } else if (typeof errorData.detail === 'object') {
                    // It's some other object, stringify it so we can see it
                    errorMessage = JSON.stringify(errorData.detail);
                }
            }
            // Throw the new, clean error message
            throw new Error(errorMessage);
        }
        // --- END UPDATED BLOCK ---

        // Get the JSON results
        results = await response.json();

        // --- 6. (MOVED) Populate final data inside the try block ---
        // This runs AFTER the simulation is complete
        if (results) {
            // Populate logs from the final result
            if (results.logs) {
                logOutput.textContent = results.logs.join('\n');
            } else {
                logOutput.textContent = "Simulation complete. Logs were not returned to prevent browser freezing.";
            }

            // Populate final statistics from the final result
            statTlbHits.textContent = results.statistics.tlb_hits.toLocaleString();
            statTlbMisses.textContent = results.statistics.tlb_misses.toLocaleString();
            statPageFaults.textContent = results.statistics.page_faults.toLocaleString();
        }

    } catch (error) {
        console.error('Simulation Error:', error);
        logOutput.textContent = `An error occurred: ${error.message}`;
    } finally {
        // --- 5. Clean up everything ---
        
        // --- RE-IMPLEMENT: Stop all intervals ---
        stopLogAnimation();
        if (statsInterval) {
            clearInterval(statsInterval);
            statsInterval = null;
        }

        // Re-enable inputs
        setInputsDisabled(false);
        runButton.textContent = 'Run Simulation';
        loadingIndicator.classList.add('hidden');
        
        // A file was selected, so we need to re-disable the textarea
        // (the setInputsDisabled(false) re-enabled it)
        if (testFileSelect.value) {
            addressesTextarea.disabled = true;
        }

        // --- 6. (MOVED) Data is now populated in the 'try' block ---
        // We also do one final poll, just in case.
        await pollStats();
    }
});


// ===============================================
// === TRACE GENERATOR LOGIC ===
// ===============================================

const traceGenForm = document.getElementById('trace-gen-form');
const traceGenButton = document.getElementById('trace-gen-button');
const traceGenStatus = document.getElementById('trace-gen-status');
const genAlgoritmoSelect = document.getElementById('gen-algoritmo');

// References to conditional parameter panels
const paramsSequencial = document.getElementById('params-sequencial');
const paramsWorkingSet = document.getElementById('params-working-set');

// NEW: Get all form inputs for the GENERATOR form
const traceGenInputs = [
    document.getElementById('gen-algoritmo'),
    document.getElementById('gen-nome-arquivo'),
    document.getElementById('gen-num-enderecos'),
    document.getElementById('gen-max-pagina'),
    document.getElementById('gen-prob-salto'),
    document.getElementById('gen-tamanho-set'),
    document.getElementById('gen-prob-no-set'),
    document.getElementById('trace-gen-button')
].filter(el => el); // Filter out nulls

// NEW: Function to toggle all GENERATOR inputs
function setTraceGenInputsDisabled(disabled) {
    traceGenInputs.forEach(input => {
        if (input) input.disabled = disabled;
    });
}

// Function to show/hide conditional parameter fields
// LANGUAGE FIX: Renamed function
function updateGeneratorFields() {
    // LANGUAGE FIX: Renamed variable
    const algorithm = genAlgoritmoSelect.value;
    
    // Hide all first
    paramsSequencial.classList.add('hidden');
    paramsWorkingSet.classList.add('hidden');
    
    // Show the relevant one
    if (algorithm === 'sequencial_com_saltos') {
        paramsSequencial.classList.remove('hidden');
    } else if (algorithm === 'working_set') {
        paramsWorkingSet.classList.remove('hidden');
    }
    // 'aleatorio' (Random) has no extra fields
}

// Listener for the generator form submission
if (traceGenForm) {
    traceGenForm.addEventListener('submit', async (event) => {
        event.preventDefault(); // Prevents page reload
        
        // Get data *before* disabling
        const formData = new FormData(traceGenForm);

        // --- NEW: Disable all inputs ---
        setTraceGenInputsDisabled(true);
        // LANGUAGE FIX: Translated button text
        traceGenButton.textContent = 'Generating...';
        // LANGUAGE FIX: Translated status text
        traceGenStatus.textContent = 'Starting trace generation...';
        traceGenStatus.className = 'text-sm mt-2 text-blue-600';

        // Build the config object
        const config = {
            algoritmo: formData.get('algoritmo'),
            nome_arquivo: formData.get('nome_arquivo'),
            num_enderecos: parseInt(formData.get('num_enderecos'), 10),
            max_pagina: parseInt(formData.get('max_pagina'), 10),
            // Include specific parameters only if they are not null
            ...(formData.get('prob_salto') && { prob_salto: parseInt(formData.get('prob_salto'), 10) }),
            ...(formData.get('tamanho_set') && { tamanho_set: parseInt(formData.get('tamanho_set'), 10) }),
            ...(formData.get('prob_no_set') && { prob_no_set: parseInt(formData.get('prob_no_set'), 10) }),
        };

        config.nome_arquivo += '.in'
        try {
            // LANGUAGE FIX: Endpoint is /gerar-trace, per user's file.
            // Do not change this unless the backend endpoint changes.
            const response = await fetch('/gerar-trace', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config),
            });

            const result = await response.json();

            if (!response.ok) {
                // Server errors (e.g., 400, 500)
                // LANGUAGE FIX: Translated error
                throw new Error(result.detail || 'Failed to generate file.');
            }

            // Success!
            // LANGUAGE FIX: Translated success message
            traceGenStatus.textContent = `Success! File '${result.filename}' generated. Reloading test list...`;
            traceGenStatus.className = 'text-sm mt-2 text-green-600';
            
            // --- UPDATE TEST DROPDOWN ---
            // Clear old options (except the first, "-- Manual Input --")
            while (testFileSelect.options.length > 1) {
                testFileSelect.remove(1);
            }
            // Reload the list
            await loadTestFiles(); // Re-use the existing function
            
            // Select the newly created file
            testFileSelect.value = result.filename;
            // Dispatch the 'change' event to update the simulation page
            testFileSelect.dispatchEvent(new Event('change'));

        } catch (error) {
            // LANGUAGE FIX: Translated error
            console.error("Error generating trace:", error);
            traceGenStatus.textContent = `Error: Filename already existent or not filled.`;
            traceGenStatus.className = 'text-sm mt-2 text-red-600';
        } finally {
            // --- NEW: Re-enable all inputs ---
            setTraceGenInputsDisabled(false);
            // LANGUAGE FIX: Translated button text
            traceGenButton.textContent = 'Generate Trace';
        }
    });
}

// ===============================================
// === PAGE NAVIGATION LOGIC ===
// ===============================================

document.addEventListener('DOMContentLoaded', () => {
    // References to nav buttons
    const navBtnSimulator = document.getElementById('nav-btn-simulator');
    const navBtnGenerator = document.getElementById('nav-btn-generator');

    // References to "pages"
    const pageSimulator = document.getElementById('page-simulator');
    const pageGenerator = document.getElementById('page-generator');

    const activeClasses = ['bg-blue-600', 'text-white'];
    const inactiveClasses = ['bg-transparent', 'text-gray-500', 'hover:bg-gray-100'];

    // Function to show the Simulator page
    function showSimulatorPage() {
        pageSimulator.classList.remove('hidden');
        pageGenerator.classList.add('hidden');

        // Update button style
        navBtnSimulator.classList.add(...activeClasses);
        navBtnSimulator.classList.remove(...inactiveClasses);
        
        navBtnGenerator.classList.add(...inactiveClasses);
        navBtnGenerator.classList.remove(...activeClasses);
    }

    // Function to show the Generator page
    function showGeneratorPage() {
        pageGenerator.classList.remove('hidden');
        pageSimulator.classList.add('hidden');

        // Update button style
        navBtnGenerator.classList.add(...activeClasses);
        navBtnGenerator.classList.remove(...inactiveClasses);

        navBtnSimulator.classList.add(...inactiveClasses);
        navBtnSimulator.classList.remove(...activeClasses);
    }

    // Add click listeners
    if (navBtnSimulator && navBtnGenerator && pageSimulator && pageGenerator) {
        navBtnSimulator.addEventListener('click', showSimulatorPage);
        navBtnGenerator.addEventListener('click', showGeneratorPage);
    }

    // --- CHANGE: Move generator listener to inside 'DOMContentLoaded' ---
    // This ensures `genAlgoritmoSelect` is not null.
    if (typeof genAlgoritmoSelect !== 'undefined' && genAlgoritmoSelect) {
        // LANGUAGE FIX: Renamed function
        genAlgoritmoSelect.addEventListener('change', updateGeneratorFields);
        // Call once at start to set the correct state
        updateGeneratorFields();
    }

    // --- NEW: Load test files *after* DOM is loaded ---
    loadTestFiles();
});