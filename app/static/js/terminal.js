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

// Ensure Ctrl+C / Cmd+C actually copies text
document.addEventListener('keydown', (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key === 'c') {
        const selectedText = window.getSelection().toString().trim();
        if (selectedText) {
            navigator.clipboard.writeText(selectedText).then(() => {
                console.log('Copied to clipboard:', selectedText);
            }).catch(err => console.error('Clipboard copy failed:', err));
        }
    }
});

// Enable right-click to show native browser copy option
term.element.addEventListener('contextmenu', (event) => {
    event.preventDefault(); // Prevent default context menu
    document.execCommand('copy'); // Copy selected text
});

// Make the white text box (xterm-helper-textarea) blacked out
const textBox = document.querySelector('.xterm-helper-textarea');
if (textBox) {
    textBox.style.backgroundColor = '#000';
    textBox.style.color = '#000';
    textBox.style.border = 'none';
    textBox.style.caretColor = 'transparent'; // Hide cursor
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
