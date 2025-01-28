// Existing terminal setup
const term = new Terminal({
    cursorBlink: true,
    theme: { background: '#000', foreground: '#FFF' },
    rightClickSelectsWord: true,
});
term.open(document.getElementById('terminal-container'));

// Helper for URL conversion
function convertUrlsToLinks(text) {
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    return text.replace(urlRegex, (url) => `\x1b]8;;${url}\x1b\\${url}\x1b]8;;\x1b\\`);
}

// Initialize terminal
term.write('$ ');

// Global variables
let inputBuffer = '';
let commandHistory = [];
let historyIndex = -1;
let activeChallengeId = null;

// Start a challenge
window.startChallenge = function (challengeId, challengeName) {
    if (!challengeId || !challengeName) {
        console.error('Invalid challenge ID or name.');
        term.write('\r\n❌ No challenge selected.\r\n$ ');
        return;
    }
    activeChallengeId = challengeId;
    term.clear();
    term.write(`\r\n✅ Challenge '${challengeName}' started. Type your AWS CLI commands below.\r\n$ `);
};

// Handle terminal input
term.onData((data) => {
    if (data === '\r') {
        if (activeChallengeId) {
            console.log(`Command submitted: ${inputBuffer.trim()}`);
            fetch('/validate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    command: inputBuffer.trim(),
                    challenge_id: activeChallengeId,
                }),
            })
                .then((response) => response.json())
                .then((data) => {
                    const formattedMessage = convertUrlsToLinks(data.message);
                    term.write(`\r\n${formattedMessage}\r\n$ `);
                })
                .catch((err) => term.write(`\r\n❌ Error: ${err.message}\r\n$ `));
        } else {
            term.write('\r\n❌ No challenge selected. Click "Start Challenge" first.\r\n$ ');
        }
        inputBuffer = '';
    } else {
        inputBuffer += data;
        term.write(data);
    }
});

// Clear the terminal
term.clear = function () {
    term.reset();
    term.write('\x1b[2J\x1b[H$ ');
};

