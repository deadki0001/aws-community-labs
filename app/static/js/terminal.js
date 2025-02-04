// Create a new Terminal instance
const term = new Terminal({
    cursorBlink: true, // Enable blinking cursor for better UX
    theme: {
        background: '#000000', // Black background
        foreground: '#FFFFFF' // White text
    },
    rightClickSelectsWord: true, // Enable word selection on right-click
    allowProposedApi: true // Allow advanced API usage
});

// Attach the terminal to the container
term.open(document.getElementById('terminal-container'));

// Enable full text selection for copying
term.element.style.userSelect = 'text'; 
term.element.style.webkitUserSelect = 'text';
term.element.style.msUserSelect = 'text';
term.element.style.mozUserSelect = 'text';

// Ensure copy (Ctrl+C / Cmd+C) works
term.attachCustomKeyEventHandler((e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'c') {
        return true; // Allow default copy behavior
    }
    return true;
});

// Handle mouse selection to prevent focus shift
term.element.addEventListener('mouseup', () => {
    if (window.getSelection().toString()) {
        term.blur(); // Prevent unwanted focus shift
    }
});

// Fix the white box by making it black
const textBox = document.querySelector('.white-box-selector'); // Replace with actual selector
if (textBox) {
    textBox.style.backgroundColor = '#000000';
}

// Function to convert URLs to hyperlinks
function convertUrlsToLinks(text) {
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    return text.replace(urlRegex, (url) => {
        return `\x1b]8;;${url}\x1b\\${url}\x1b]8;;\x1b\\`;
    });
}

// Initialize terminal with a clean state
function initializeTerminal() {
    term.reset(); 
    term.write('\x1b[2J\x1b[H'); // Clear screen and move cursor to top-left
    term.write('$ '); // Display the prompt
}

initializeTerminal();

// Global variables
let inputBuffer = '';
let commandHistory = [];
let historyIndex = -1;
let activeChallengeId = null;

// Function to start a challenge
window.startChallenge = function (challengeId) {
    console.log(`Start Challenge invoked with challengeId: ${challengeId}`);
    activeChallengeId = challengeId;
    term.clear();
    term.write(`Challenge ${challengeId} started: Enter your command below.\r\n$ `);
};

// Terminal input handling
term.onData((data) => {
    if (data === '\r') { // Enter key pressed
        if (inputBuffer.trim() === 'clear') {
            term.clear();
            inputBuffer = '';
            return;
        }

        if (activeChallengeId) {
            console.log(`Command submitted: ${inputBuffer.trim()}, Challenge ID: ${activeChallengeId}`);
            commandHistory.push(inputBuffer.trim());
            historyIndex = -1;

            fetch('/validate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    command: inputBuffer.trim(),
                    challenge_id: activeChallengeId
                })
            })
            .then((response) => response.ok ? response.json() : Promise.reject(`HTTP error! Status: ${response.status}`))
            .then((data) => {
                console.log('Response from /validate:', data);
                term.write(convertUrlsToLinks(data.message).replace(/\n/g, '\r\n') + '\r\n$ ');
            })
            .catch((error) => {
                console.error('Error in fetch:', error);
                term.write(`\r\n❌ Error: ${error.message}\r\n$ `);
            });

            inputBuffer = '';
        } else {
            term.write('\r\n❌ No challenge selected. Click "Start Challenge" first.\r\n$ ');
        }
    } else if (data === '\u007F') { // Backspace key pressed
        if (inputBuffer.length > 0) {
            inputBuffer = inputBuffer.slice(0, -1);
            term.write('\b \b');
        }
    } else if (data === '\u001b[A') { // Up arrow key
        if (commandHistory.length > 0) {
            if (historyIndex === -1) historyIndex = commandHistory.length;
            if (historyIndex > 0) {
                historyIndex--;
                inputBuffer = commandHistory[historyIndex];
                term.write('\r\x1b[K$ ' + inputBuffer);
            }
        }
    } else if (data === '\u001b[B') { // Down arrow key
        if (historyIndex !== -1) {
            historyIndex++;
            inputBuffer = historyIndex < commandHistory.length ? commandHistory[historyIndex] : '';
            historyIndex = historyIndex < commandHistory.length ? historyIndex : -1;
            term.write('\r\x1b[K$ ' + inputBuffer);
        }
    } else {
        inputBuffer += data;
        term.write(data);
    }
});

// Helper to clear and reset the terminal
term.clear = function () {
    term.reset();
    term.write('\x1b[2J\x1b[H');
    term.write('$ ');
};

// Allow double-click word selection
term.element.addEventListener('mousedown', (event) => {
    if (event.detail >= 2) {
        event.preventDefault();
        term.selectWord();
    }
});

term.focus();
