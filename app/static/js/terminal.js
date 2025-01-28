// Create a new Terminal instance with optimized settings
let term = null;
let fitAddon = null;
let inputBuffer = '';
let commandHistory = [];
let historyIndex = -1;
let activeChallengeId = null;

function createTerminal() {
    term = new Terminal({
        cursorBlink: true,
        theme: {
            background: '#000000',
            foreground: '#FFFFFF'
        },
        rightClickSelectsWord: true,
        allowProposedApi: true,
        rendererType: 'canvas',
        allowTransparency: true,
        rows: 24,
        cols: 80
    });

    fitAddon = new FitAddon.FitAddon();
    term.loadAddon(fitAddon);
    return term;
}

// Initialize terminal with error handling
function initializeTerminal() {
    try {
        const terminalContainer = document.getElementById('terminal-container');
        if (!terminalContainer) {
            console.error('Terminal container not found');
            return;
        }

        term = createTerminal();
        term.open(terminalContainer);

        setTimeout(() => {
            try {
                fitAddon.fit();
            } catch (e) {
                console.error('Error fitting terminal:', e);
            }
        }, 100);

        // Handle terminal resize with debouncing
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                try {
                    fitAddon.fit();
                } catch (e) {
                    console.error('Error during resize:', e);
                }
            }, 100);
        });

        // Initialize with clean state
        term.reset();
        term.write('\x1b[2J\x1b[H');
        term.write('Welcome to AWS CLI Learning Platform\r\n');
        term.write('$ ');

        // Set up input handling
        term.onData(data => {
            switch (data) {
                case '\r': // Enter
                    handleEnterKey();
                    break;
                case '\u007F': // Backspace
                    handleBackspace();
                    break;
                case '\u001b[A': // Up arrow
                    handleUpArrow();
                    break;
                case '\u001b[B': // Down arrow
                    handleDownArrow();
                    break;
                default:
                    if (data >= String.fromCharCode(0x20) && data <= String.fromCharCode(0x7E)) {
                        inputBuffer += data;
                        term.write(data);
                    }
            }
        });

    } catch (e) {
        console.error('Error initializing terminal:', e);
    }
}

function handleEnterKey() {
    term.write('\r\n');

    if (inputBuffer.trim() === 'clear') {
        term.clear();
        term.write('$ ');
        inputBuffer = '';
        return;
    }

    if (activeChallengeId) {
        validateCommand(inputBuffer.trim());
    } else {
        term.write('No active challenge. Please start a challenge first.\r\n$ ');
    }

    commandHistory.push(inputBuffer.trim());
    historyIndex = -1;
    inputBuffer = '';
}

function handleBackspace() {
    if (inputBuffer.length > 0) {
        inputBuffer = inputBuffer.slice(0, -1);
        term.write('\b \b');
    }
}

function handleUpArrow() {
    if (commandHistory.length > 0) {
        if (historyIndex === -1) {
            historyIndex = commandHistory.length;
        }
        if (historyIndex > 0) {
            historyIndex--;
            showHistoryCommand();
        }
    }
}

function handleDownArrow() {
    if (historyIndex !== -1) {
        historyIndex++;
        if (historyIndex < commandHistory.length) {
            showHistoryCommand();
        } else {
            inputBuffer = '';
            historyIndex = -1;
            term.write('\r\x1b[K$ ');
        }
    }
}

function showHistoryCommand() {
    inputBuffer = commandHistory[historyIndex];
    term.write('\r\x1b[K$ ' + inputBuffer);
}

async function validateCommand(command) {
    try {
        const response = await fetch('/validate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                command: command,
                challenge_id: activeChallengeId
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        if (term && term.write) {
            term.write(data.message.replace(/\n/g, '\r\n') + '\r\n$ ');
            
            if (data.cloud_warrior) {
                showCloudWarriorPopup();
            }
            if (data.cloud_sorcerer) {
                showCloudSorcererPopup();
            }
        }
    } catch (error) {
        console.error('Validation error:', error);
        if (term && term.write) {
            term.write(`\r\nError: ${error.message}\r\n$ `);
        }
    }
}

// Start challenge function
window.startChallenge = function(challengeId) {
    console.log(`Starting challenge: ${challengeId}`);
    activeChallengeId = challengeId;
    
    if (term) {
        term.clear();
        term.write(`Challenge ${challengeId} started: Enter your command below.\r\n$ `);
    }
};

// Initialize terminal after DOM is loaded
document.addEventListener('DOMContentLoaded', initializeTerminal);
