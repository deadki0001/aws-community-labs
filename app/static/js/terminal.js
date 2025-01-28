// Create a new Terminal instance with mobile-friendly configuration
const term = new Terminal({
    cursorBlink: true,
    theme: {
        background: '#000000',
        foreground: '#FFFFFF'
    },
    rightClickSelectsWord: true,
    allowProposedApi: true,
    convertEol: true,
    wordWrap: true,
    fontFamily: 'Menlo, Monaco, "Courier New", monospace',
    fontSize: 14
});

// Dynamically adjust terminal size based on the screen
function resizeTerminal() {
    const width = window.innerWidth;
    const height = window.innerHeight;
    
    // Adjust cols and rows based on screen size
    const cols = Math.floor(width / 8);  // Adjust for font size
    const rows = Math.floor(height / 18);
    
    term.resize(cols, rows);
}

// Attach the terminal to the container
term.open(document.getElementById('terminal-container'));
resizeTerminal();  // Initial resize
window.addEventListener('resize', resizeTerminal);  // Resize on window change

// Enable mobile input (Create a hidden input field)
const mobileInput = document.createElement('input');
mobileInput.type = 'text';
mobileInput.style.position = 'absolute';
mobileInput.style.opacity = 0;
mobileInput.style.height = '0px';
mobileInput.style.zIndex = -1;
document.body.appendChild(mobileInput);

// Focus input field on terminal click
term.element.addEventListener('click', () => {
    mobileInput.focus();
});

// Allow text input through mobile keyboard
mobileInput.addEventListener('input', (event) => {
    const value = event.target.value;
    event.target.value = '';  // Clear input field

    for (const char of value) {
        inputBuffer += char;
        term.write(char);
    }
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
        .then(response => response.json())
        .then(data => {
            const formattedMessage = convertUrlsToLinks(data.message);
            term.write(`\r\n${formattedMessage.replace(/\n/g, '\r\n')}\r\n$ `);
        })
        .catch(error => {
            console.error('Error in fetch:', error);
            term.write(`\r\n❌ Error: ${error.message}\r\n$ `);
        });

        commandHistory.push(command.trim());
    } else {
        term.write('\r\nNo challenge selected. Click "Start Challenge" first.\r\n$ ');
    }
}

// Key input handling (for physical keyboards)
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

    // Handle up arrow (navigate command history)
    if (ev.keyCode === 38 && commandHistory.length > 0) {
        historyIndex = Math.max(0, historyIndex - 1);
        inputBuffer = commandHistory[historyIndex] || '';
        term.write(`\r\x1b[K$ ${inputBuffer}`);
        return;
    }

    // Handle down arrow
    if (ev.keyCode === 40) {
        historyIndex = historyIndex < commandHistory.length - 1 ? historyIndex + 1 : -1;
        inputBuffer = historyIndex === -1 ? '' : commandHistory[historyIndex];
        term.write(`\r\x1b[K$ ${inputBuffer}`);
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

// Handle mobile touch events for text selection
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
