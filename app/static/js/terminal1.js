// Create a new Terminal instance with optimized settings
const term = new Terminal({
    cursorBlink: true,
    theme: {
        background: '#000000',
        foreground: '#FFFFFF'
    },
    rightClickSelectsWord: true,
    allowProposedApi: true,
    rendererType: 'canvas',
    allowTransparency: true
});

// Create and configure the FitAddon
const fitAddon = new FitAddon.FitAddon();
term.loadAddon(fitAddon);

// Initialize terminal with optimized canvas settings
function initializeTerminal() {
    const terminalContainer = document.getElementById('terminal-container');
    
    // Set canvas willReadFrequently attribute
    const canvas = terminalContainer.querySelector('canvas');
    if (canvas) {
        canvas.getContext('2d', { willReadFrequently: true });
    }
    
    // Attach the terminal to the container
    term.open(terminalContainer);
    fitAddon.fit();
    
    // Handle terminal resize
    window.addEventListener('resize', () => {
        fitAddon.fit();
    });

    // Initialize with clean state
    term.reset();
    term.write('\x1b[2J\x1b[H'); // Clear screen and move cursor to top-left
    term.write('Welcome to AWS CLI Learning Platform\r\n');
    term.write('$ ');
}

// Global variables for challenge management
let inputBuffer = '';
let commandHistory = [];
let historyIndex = -1;
let activeChallengeId = null;

// Updated challenge start function to work with existing architecture
window.startChallenge = function(challengeId) {
    console.log(`Starting challenge: ${challengeId}`);
    activeChallengeId = challengeId;

    // Clear the terminal and show challenge started message
    term.clear();
    term.write(`Challenge ${challengeId} started: Enter your command below.\r\n$ `);
};

// Improved terminal input handling
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

function validateCommand(command) {
    fetch('/validate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            command: command,
            challenge_id: activeChallengeId
        })
    })
    .then(response => response.json())
    .then(data => {
        term.write(data.message.replace(/\n/g, '\r\n') + '\r\n$ ');
        
        // Handle badges if they were earned
        if (data.cloud_warrior) {
            showCloudWarriorPopup();
        }
        if (data.cloud_sorcerer) {
            showCloudSorcererPopup();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        term.write(`\r\nError: ${error.message}\r\n$ `);
    });
}

// Initialize terminal after DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeTerminal();
});
