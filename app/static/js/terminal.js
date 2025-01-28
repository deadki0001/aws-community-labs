// Create a new Terminal instance with proper configuration
const term = new Terminal({
    cursorBlink: true,
    theme: {
        background: '#000000',
        foreground: '#FFFFFF'
    },
    rightClickSelectsWord: true,
    allowProposedApi: true,
    cols: 100,  // Wider column width for better text display
    rows: 24,   // Standard number of rows
    convertEol: true,
    wordWrap: true,
    fontFamily: 'Menlo, Monaco, "Courier New", monospace',
    fontSize: 14
});

// Attach the terminal to the container
term.open(document.getElementById('terminal-container'));

// Allow text selection and copying
term.attachCustomKeyEventHandler((e) => {
    // Allow default browser behavior for copying (Ctrl+C / Cmd+C)
    if ((e.ctrlKey || e.metaKey) && e.key === 'c') {
        return true;
    }
    return true;
});

// Global variables for terminal state
let inputBuffer = '';
let commandHistory = [];
let historyIndex = -1;
let activeChallengeId = null;

// Function to convert URLs to clickable links
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
    term.write('$ ');
}

// Function to handle command submission
function submitCommand(command) {
    if (!command.trim()) {
        term.write('\r\n$ ');
        return;
    }

    if (command.trim() === 'clear') {
        term.clear();
        inputBuffer = '';
        return;
    }

    if (activeChallengeId) {
        fetch('/validate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                command: command.trim(),
                challenge_id: activeChallengeId,
            }),
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.message || `HTTP error! Status: ${response.status}`);
                }).catch(() => {
                    throw new Error(`HTTP error! Status: ${response.statusText}`);
                });
            }
            return response.json();
        })
        .then(data => {
            const formattedMessage = convertUrlsToLinks(data.message);
            term.write(`\r\n${formattedMessage.replace(/\n/g, '\r\n')}\r\n$ `);
        })
        .catch(error => {
            console.error('Error in fetch:', error);
            term.write(`\r\n❌ Error: ${error.message}\r\n$ `);
        });

        if (command.trim() !== '') {
            commandHistory.push(command.trim());
        }
    } else {
        term.write('\r\nNo challenge selected. Click "Start Challenge" first.\r\n$ ');
    }
}

// Key input handling
term.onKey(({ key, domEvent }) => {
    const ev = domEvent;

    // Handle Enter key
    if (ev.keyCode === 13) {
        term.write('\r\n');
        submitCommand(inputBuffer);
        inputBuffer = '';
        historyIndex = -1;
        return;
    }

    // Handle backspace
    if (ev.keyCode === 8) {
        if (inputBuffer.length > 0) {
            inputBuffer = inputBuffer.slice(0, -1);
            term.write('\b \b');
        }
        return;
    }

    // Handle up arrow
    if (ev.keyCode === 38) {
        if (commandHistory.length > 0) {
            if (historyIndex === -1) {
                historyIndex = commandHistory.length - 1;
            } else if (historyIndex > 0) {
                historyIndex--;
            }
            inputBuffer = commandHistory[historyIndex];
            term.write(`\r\x1b[K$ ${inputBuffer}`);
        }
        return;
    }

    // Handle down arrow
    if (ev.keyCode === 40) {
        if (historyIndex !== -1) {
            if (historyIndex < commandHistory.length - 1) {
                historyIndex++;
                inputBuffer = commandHistory[historyIndex];
            } else {
                historyIndex = -1;
                inputBuffer = '';
            }
            term.write(`\r\x1b[K$ ${inputBuffer}`);
        }
        return;
    }

    // Regular character input
    if (!ev.altKey && !ev.ctrlKey && !ev.metaKey && key.length === 1) {
        inputBuffer += key;
        term.write(key);
    }
});

// Start challenge function
window.startChallenge = function(challengeId) {
    console.log(`Starting challenge: ${challengeId}`);
    activeChallengeId = challengeId;

    term.clear();
    term.write(`Challenge ${challengeId} started\r\n$ `);
    inputBuffer = '';
    historyIndex = -1;
};

// Mouse event handling for text selection
term.element.addEventListener('mouseup', () => {
    if (window.getSelection().toString()) {
        term.blur();
    }
});

term.element.addEventListener('mousedown', (event) => {
    if (event.detail >= 2) {
        return;
    }
    term.focus();
});

// Helper to clear and reset the terminal
term.clear = function() {
    term.reset();
    term.write('\x1b[2J\x1b[H');
    term.write('$ ');
};

// Initialize terminal on page load
initializeTerminal();

