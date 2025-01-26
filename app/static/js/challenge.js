document.addEventListener('DOMContentLoaded', function() {
    const commandForm = document.getElementById('command-form');
    
    if (commandForm) {
        commandForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const commandInput = document.getElementById('command-input');
            const challengeId = document.getElementById('challenge-id').value;
            const command = commandInput.value.trim();
            
            fetch('/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    command: command,
                    challenge_id: challengeId
                })
            })
            .then(response => response.json())
            .then(data => {
                // Display response message
                const messageDiv = document.getElementById('command-message');
                messageDiv.textContent = data.message;
                
                // Check for Cloud Warrior badge
                if (data.cloud_warrior) {
                    showCloudWarriorPopup();
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
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