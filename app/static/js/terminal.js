const term = new Terminal();
term.open(document.getElementById('terminal-container'));
term.write('Welcome to the AWS CLI Learning Platform!\r\n$ ');

// Global variables
let inputBuffer = ''; // Store user input
let activeChallengeId = null; // Store the currently active challenge ID

// Function to start a challenge
window.startChallenge = function (challengeId) {
    console.log(`Start Challenge invoked with challengeId: ${challengeId}`);
    activeChallengeId = challengeId;
    term.clear();
    term.write(`\r\nChallenge ${challengeId} started: Enter your command below.\r\n$ `);
};

// Terminal input handling
term.onData((data) => {
    if (data === '\r') { // Enter key
        if (activeChallengeId) {
            console.log(`Command submitted: ${inputBuffer.trim()}, Challenge ID: ${activeChallengeId}`);

            fetch('/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    command: inputBuffer.trim(),
                    challenge_id: activeChallengeId
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Response from /validate:', data);
                term.write(data.message.replace(/\n/g, '\r\n') + '\r\n$ ');
            })
            .catch(error => {
                console.error('Error in fetch:', error);
                term.write(`\r\n❌ Error: ${error.message}\r\n$ `);
            });

            inputBuffer = '';
        } else {
            term.write('\r\n❌ No challenge selected. Click "Start Challenge" first.\r\n$ ');
        }
    } else if (data === '\u007F') { // Backspace key
        inputBuffer = inputBuffer.slice(0, -1);
        term.write('\b \b');
    } else {
        inputBuffer += data;
        term.write(data);
    }
});

// Helper to clear the terminal when needed
term.clear = function () {
    term.reset();
    term.write('$ ');
};
