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

const tlbEntriesInput = document.getElementById('tlb_entries');
const numFramesInput = document.getElementById('num_frames');
const repPolicySelect = document.getElementById('rep_policy');

const formInputs = [
    runButton,
    tlbEntriesInput,
    numFramesInput,
    repPolicySelect,
    testFileSelect,
    addressesTextarea
];

let statsInterval = null;
let loadingInterval = null;

function setInputsDisabled(disabled) {
    formInputs.forEach(input => {
        if (input) { // Add a check in case an element isn't found
            input.disabled = disabled;
        }
    });
}

function startLogAnimation() {
    let dots = 0;
    logOutput.textContent = 'Running simulation';
    loadingInterval = setInterval(() => {
        dots = (dots + 1) % 4;
        logOutput.textContent = `Running simulation${'.'.repeat(dots)}`;
    }, 500);
}

function stopLogAnimation() {
    if (loadingInterval) {
        clearInterval(loadingInterval);
        loadingInterval = null;
    }
}

async function pollStats() {
    try {
        const response = await fetch('/current-stats');
        if (!response.ok) return; // Silently fail if server is busy
        
        const stats = await response.json();
        
        // update stats UI
        statTlbHits.textContent = stats.tlb_hits.toLocaleString();
        statTlbMisses.textContent = stats.tlb_misses.toLocaleString();
        statPageFaults.textContent = stats.page_faults.toLocaleString();

    } catch (error) {
        console.warn("Stats poll failed:", error);
    }
}


async function loadTestFiles() {
    try {
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

testFileSelect.addEventListener('change', async () => {
    const selectedFile = testFileSelect.value;
    
    if (selectedFile) {
        // A file is selected.
        // it doesn't fetch text content, just disable the textarea and show a message.
        addressesTextarea.value = `Test file selected:\n${selectedFile}\n\n(Manual input is disabled)`;
        addressesTextarea.disabled = true; // Disable textarea
    } else {
        // manual input is selected
        addressesTextarea.disabled = false; // Re-enable textarea
        addressesTextarea.value = ''; // Clear it
        addressesTextarea.placeholder = '100\n101\n100\n102\n...';
    }
});

simForm.addEventListener('submit', async (event) => {
    event.preventDefault(); 

    const formData = new FormData(simForm);
    const selectedTestFile = formData.get('test_file');

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
        config.addresses = formData.get('addresses'); 
    }

    console.log("Sending this JSON to /run-simulation:", JSON.stringify(config, null, 2));


    setInputsDisabled(true); // This now disables ALL inputs
    runButton.textContent = 'Running...'; // Text content is fine, button is disabled
    loadingIndicator.classList.remove('hidden');
    startLogAnimation();

    statTlbHits.textContent = '0';
    statTlbMisses.textContent = '0';
    statPageFaults.textContent = '0';

    statsInterval = setInterval(pollStats, 1000); // Poll every 1 second

    
    let results; // To store final results

    try {
        const response = await fetch('/run-simulation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(config),
        });

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

        results = await response.json();

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
        stopLogAnimation();
        if (statsInterval) {
            clearInterval(statsInterval);
            statsInterval = null;
        }

        setInputsDisabled(false);
        runButton.textContent = 'Run Simulation';
        loadingIndicator.classList.add('hidden');
        
        if (testFileSelect.value) {
            addressesTextarea.disabled = true;
        }

        await pollStats();
    }
});


const traceGenForm = document.getElementById('trace-gen-form');
const traceGenButton = document.getElementById('trace-gen-button');
const traceGenStatus = document.getElementById('trace-gen-status');
const genAlgoritmoSelect = document.getElementById('gen-algoritmo');

const paramsSequencial = document.getElementById('params-sequencial');
const paramsWorkingSet = document.getElementById('params-working-set');

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

function setTraceGenInputsDisabled(disabled) {
    traceGenInputs.forEach(input => {
        if (input) input.disabled = disabled;
    });
}

function updateGeneratorFields() {
    const algorithm = genAlgoritmoSelect.value;
    
    paramsSequencial.classList.add('hidden');
    paramsWorkingSet.classList.add('hidden');
    
    if (algorithm === 'sequencial_com_saltos') {
        paramsSequencial.classList.remove('hidden');
    } else if (algorithm === 'working_set') {
        paramsWorkingSet.classList.remove('hidden');
    }
}

if (traceGenForm) {
    traceGenForm.addEventListener('submit', async (event) => {
        event.preventDefault(); // Prevents page reload
        
        const formData = new FormData(traceGenForm);

        setTraceGenInputsDisabled(true);
        traceGenButton.textContent = 'Generating...';
        traceGenStatus.textContent = 'Starting trace generation...';
        traceGenStatus.className = 'text-sm mt-2 text-blue-600';

        const config = {
            algoritmo: formData.get('algoritmo'),
            nome_arquivo: formData.get('nome_arquivo'),
            num_enderecos: parseInt(formData.get('num_enderecos'), 10),
            max_pagina: parseInt(formData.get('max_pagina'), 10),
            ...(formData.get('prob_salto') && { prob_salto: parseInt(formData.get('prob_salto'), 10) }),
            ...(formData.get('tamanho_set') && { tamanho_set: parseInt(formData.get('tamanho_set'), 10) }),
            ...(formData.get('prob_no_set') && { prob_no_set: parseInt(formData.get('prob_no_set'), 10) }),
        };

        config.nome_arquivo += '.in'
        try {
            const response = await fetch('/gerar-trace', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config),
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || 'Failed to generate file.');
            }

            traceGenStatus.textContent = `Success! File '${result.filename}' generated. Reloading test list...`;
            traceGenStatus.className = 'text-sm mt-2 text-green-600';
            
            while (testFileSelect.options.length > 1) {
                testFileSelect.remove(1);
            }
            await loadTestFiles(); // Re-use the existing function
            
            testFileSelect.value = result.filename;
            testFileSelect.dispatchEvent(new Event('change'));

        } catch (error) {
            console.error("Error generating trace:", error);
            traceGenStatus.textContent = `Error: Filename already existent or not filled.`;
            traceGenStatus.className = 'text-sm mt-2 text-red-600';
        } finally {
            setTraceGenInputsDisabled(false);
            traceGenButton.textContent = 'Generate Trace';
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const navBtnSimulator = document.getElementById('nav-btn-simulator');
    const navBtnGenerator = document.getElementById('nav-btn-generator');

    const pageSimulator = document.getElementById('page-simulator');
    const pageGenerator = document.getElementById('page-generator');

    const activeClasses = ['bg-blue-600', 'text-white'];
    const inactiveClasses = ['bg-transparent', 'text-gray-500', 'hover:bg-gray-100'];

    function showSimulatorPage() {
        pageSimulator.classList.remove('hidden');
        pageGenerator.classList.add('hidden');

        navBtnSimulator.classList.add(...activeClasses);
        navBtnSimulator.classList.remove(...inactiveClasses);
        
        navBtnGenerator.classList.add(...inactiveClasses);
        navBtnGenerator.classList.remove(...activeClasses);
    }

    function showGeneratorPage() {
        pageGenerator.classList.remove('hidden');
        pageSimulator.classList.add('hidden');

        navBtnGenerator.classList.add(...activeClasses);
        navBtnGenerator.classList.remove(...inactiveClasses);

        navBtnSimulator.classList.add(...inactiveClasses);
        navBtnSimulator.classList.remove(...activeClasses);
    }

    if (navBtnSimulator && navBtnGenerator && pageSimulator && pageGenerator) {
        navBtnSimulator.addEventListener('click', showSimulatorPage);
        navBtnGenerator.addEventListener('click', showGeneratorPage);
    }
    if (typeof genAlgoritmoSelect !== 'undefined' && genAlgoritmoSelect) {
        genAlgoritmoSelect.addEventListener('change', updateGeneratorFields);
        updateGeneratorFields();
    }

    loadTestFiles();
});