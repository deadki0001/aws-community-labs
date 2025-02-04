const term = new Terminal({
    cursorBlink: true,
    theme: {
        background: '#000000',
        foreground: '#FFFFFF',
        cursor: '#FFFFFF',
        selection: 'rgba(255, 255, 255, 0.3)'
    },
    rightClickSelectsWord: true,
    allowProposedApi: true,
    convertEol: true,
    fontFamily: 'Menlo, Monaco, "Courier New", monospace',
    fontSize: 14,
    lineHeight: 1.2
});

term.open(document.getElementById('terminal-container'));

let inputBuffer = '';
let commandHistory = [];
let historyIndex = -1;
let activeChallengeId = null;

// URL handling
const urlRegex = /(https?:\/\/[^\s]+)/g;
term.registerLinkMatcher(urlRegex, (event, uri) => {
    window.open(uri, '_blank');
});

// Copy handling
document.addEventListener('copy', (e) => {
    const selection = window.getSelection().toString();
    if (selection) {
        e.clipboardData.setData('text/plain', selection);
        e.preventDefault();
    }
});

term.attachCustomKeyEventHandler((e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'c') {
        const selection = window.getSelection().toString();
        if (selection) {
            navigator.clipboard.writeText(selection);
            return false;
        }
        return true;
    }
    return true;
});

function initializeTerminal() {
    term.reset();
    term.write('\x1b[2J\x1b[H');
    term.write('$ ');
}

window.startChallenge = function(challengeId) {
    activeChallengeId = challengeId;
    term.clear();
    term.write(`Challenge ${challengeId} started: Enter your command below.\r\n$ `);
};

term.onData((data) => {
    switch(data) {
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
            inputBuffer += data;
            term.write(data);
    }
});

function handleEnterKey() {
    if (inputBuffer.trim() === 'clear') {
        term.clear();
        inputBuffer = '';
        return;
    }

    if (!activeChallengeId) {
        term.write('\r\n❌ No challenge selected. Click "Start Challenge" first.\r\n$ ');
        inputBuffer = '';
        return;
    }

    commandHistory.push(inputBuffer.trim());
    historyIndex = -1;

    validateCommand(inputBuffer.trim());
    inputBuffer = '';
}

function validateCommand(command) {
    fetch('/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            command: command,
            challenge_id: activeChallengeId
        })
    })
    .then(response => {
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        return response.json();
    })
    .then(data => {
        const formattedMessage = data.message.replace(/\n/g, '\r\n');
        term.write(`\r\n${formattedMessage}\r\n$ `);
    })
    .catch(error => {
        term.write(`\r\n❌ Error: ${error.message}\r\n$ `);
    });
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
            displayHistoryCommand(commandHistory[historyIndex]);
        }
    }
}

function handleDownArrow() {
    if (historyIndex !== -1) {
        historyIndex++;
        if (historyIndex < commandHistory.length) {
            displayHistoryCommand(commandHistory[historyIndex]);
        } else {
            displayHistoryCommand('');
            historyIndex = -1;
        }
    }
}

function displayHistoryCommand(command) {
    inputBuffer = command;
    term.write('\r\x1b[K$ ' + command);
}

term.clear = function() {
    term.reset();
    term.write('\x1b[2J\x1b[H$ ');
};

// Enable text selection
term.element.style.userSelect = 'text';
term.element.addEventListener('mousedown', (event) => {
    if (event.detail >= 2) {
        event.preventDefault();
        term.selectWord();
    }
});

// Initialize
initializeTerminal();
term.focus();