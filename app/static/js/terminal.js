const term = new Terminal();
term.open(document.getElementById('terminal'));
term.write('Welcome to the AWS CLI Learning Platform!\r\n$ ');

// Capture user input
let inputBuffer = '';  // Store user input

term.onData((data) => {
    if (data === '\r') {  // Enter key
        // Send input to the server for validation
        fetch('/validate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: inputBuffer.trim() })  // Send the complete command
        })
        .then(response => response.json())
        .then(data => {
            term.write(`\r\n${data.message}\r\n$ `);
        });

        inputBuffer = '';  // Clear the input buffer after submission
    } else if (data === '\u007F') {  // Backspace key (remove last character)
        inputBuffer = inputBuffer.slice(0, -1);
        term.write('\b \b');
    } else {
        inputBuffer += data;  // Append character to the buffer
        term.write(data);
    }
});

