document.addEventListener('DOMContentLoaded', function () {
    console.log('DOM fully loaded and parsed'); // Confirm DOM is ready

    const commandForm = document.getElementById('command-form');
    console.log('commandForm:', commandForm); // Log whether commandForm is found

    if (commandForm) {
        console.log('commandForm exists, adding event listener...');
        commandForm.addEventListener('submit', function (e) {
            e.preventDefault();

            const commandInput = document.getElementById('command-input');
            const challengeId = document.getElementById('challenge-id')?.value || null; // Safely get the challenge ID
            const command = commandInput?.value.trim() || ''; // Safely get the command input

            console.log('Submitting command:', {
                command: command,
                challenge_id: challengeId,
            }); // Log the values being sent

            // Ensure both command and challengeId are provided
            if (!challengeId) {
                console.error('❌ Challenge ID is missing!');
                const messageDiv = document.getElementById('command-message');
                messageDiv.textContent = '❌ No challenge selected. Please start a challenge first.';
                return;
            }

            if (!command) {
                console.error('❌ Command is missing!');
                const messageDiv = document.getElementById('command-message');
                messageDiv.textContent = '❌ Command cannot be empty.';
                return;
            }

            // Fetch request to /validate
            fetch('/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    command: command,
                    challenge_id: challengeId,
                }),
            })
                .then((response) => {
                    console.log('Raw response from /validate:', response); // Log raw response
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                })
                .then((data) => {
                    console.log('Response data from /validate:', data); // Log parsed response data

                    // Display response message
                    const messageDiv = document.getElementById('command-message');
                    messageDiv.textContent = data.message;

                    // Check for badges
                    if (data.cloud_warrior) {
                        console.log('Cloud Warrior badge achieved!');
                        showCloudWarriorPopup();
                    }
                    if (data.cloud_sorcerer) {
                        console.log('Cloud Sorcerer badge achieved!');
                        showCloudSorcererPopup();
                    }
                })
                .catch((error) => {
                    console.error('Error in fetch:', error);
                    const messageDiv = document.getElementById('command-message');
                    messageDiv.textContent = `❌ Error: ${error.message}`;
                });
        });
    } else {
        console.error('❌ commandForm not found! Ensure the form is in the HTML.');
    }
});

function showCloudWarriorPopup() {
    const popup = document.createElement('div');
    popup.innerHTML = `
        <div style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
                    background-color: #f0f0f0; padding: 20px; border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; z-index: 1000;">
            <h2>🏆 Cloud Warrior Unlocked! 🏆</h2>
            <p>Congratulations! You've earned the Cloud Warrior badge by reaching 10 points!</p>
            <button onclick="this.parentElement.remove()">Close</button>
        </div>
    `;
    document.body.appendChild(popup);
}

function showCloudSorcererPopup() {
    const popup = document.createElement('div');
    popup.innerHTML = `
        <div style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
                    background-color: #f8f9fa; padding: 20px; border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; z-index: 1000;">
            <img src="/static/magic.png" alt="Cloud Sorcerer Badge" style="width: 100px; margin-bottom: 15px;">
            <h2>✨ Cloud Sorcerer Unlocked! ✨</h2>
            <p>You've reached 50 points and earned the Cloud Sorcerer badge!</p>
            <button onclick="this.parentElement.remove()">Close</button>
        </div>
    `;
    document.body.appendChild(popup);
}

