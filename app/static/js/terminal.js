// Create a new Terminal instance
const term = new Terminal({
    cursorBlink: true, // Enable blinking cursor for better UX
    theme: {
        background: '#000000', // Black background
        foreground: '#FFFFFF' // White text
    },
    // Enable link handling
    linkHandler: {
        activate: (event, uri) => {
            window.open(uri, '_blank');
        }
    }
});

// Attach the terminal to the container
term.open(document.getElementById('terminal-container'));

// Function to convert URLs to hyperlinks
function convertUrlsToLinks(text) {
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    return text.replace(urlRegex, (url) => {
        // Create a hyperlink that can be clicked
        return `\x1b]8;;${url}\x1b\\${url}\x1b]8;;\x1b\\`;
    });
}

// Initialize terminal with a clean state
function initializeTerminal() {
    term.reset(); // Clear and reset terminal state
    term.write('\x1b[2J\x1b[3J\x1b[H\x1b[?25l'); // Clear screen, scrollback, and hide cursor
    term.write('$ '); // Display the prompt
}

// Call initializeTerminal to set up a clean environment
initializeTerminal();

// Global variables
let inputBuffer = ''; // Store user input
let activeChallengeId = null; // Track the current active challenge

// Function to start a challenge
window.startChallenge = function (challengeId) {
    console.log(`Start Challenge invoked with challengeId: ${challengeId}`);
    activeChallengeId = challengeId;

    // Clear the terminal for the new challenge
    term.clear();
    term.write(`Challenge ${challengeId} started: Enter your command below.\r\n$ `);
};

// Terminal input handling
term.onData((data) => {
    if (data === '\r') { // Enter key pressed
        if (activeChallengeId) {
            console.log(`Command submitted: ${inputBuffer.trim()}, Challenge ID: ${activeChallengeId}`);

            // Send the user command to the server for validation
            fetch('/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    command: inputBuffer.trim(),
                    challenge_id: activeChallengeId,
                }),
            })
                .then((response) => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                })
                .then((data) => {
                    console.log('Response from /validate:', data);
                    // Convert URLs to hyperlinks and display the response
                    const formattedMessage = convertUrlsToLinks(data.message);
                    term.write(formattedMessage.replace(/\n/g, '\r\n') + '\r\n$ ');
                })
                .catch((error) => {
                    console.error('Error in fetch:', error);
                    term.write(`\r\n❌ Error: ${error.message}\r\n$ `);
                });

            inputBuffer = ''; // Clear the input buffer after submission
        } else {
            term.write('\r\n❌ No challenge selected. Click "Start Challenge" first.\r\n$ ');
        }
    } else if (data === '\u007F') { // Backspace key pressed
        if (inputBuffer.length > 0) {
            inputBuffer = inputBuffer.slice(0, -1);
            term.write('\b \b'); // Remove the last character from the terminal display
        }
    } else {
        inputBuffer += data; // Add typed data to the input buffer
        term.write(data); // Display the typed character in the terminal
    }
});

// Helper to clear and reset the terminal
term.clear = function () {
    term.reset(); // Reset the terminal's internal state
    term.write('\x1b[2J'); // Clear the visible terminal screen
    term.write('\x1b[H');  // Move the cursor to the top-left
    term.write('$ ');      // Display the prompt
};