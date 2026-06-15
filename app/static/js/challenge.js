document.addEventListener('DOMContentLoaded', function () {
    const commandForm = document.getElementById('command-form');
    if (commandForm) {
        commandForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const challengeId = document.getElementById('challenge-id').value;
            const command = document.getElementById('command-input').value.trim();

            fetch('/validate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command, challenge_id: challengeId }),
            })
                .then((response) => response.json())
                .then((data) => {
                    const messageDiv = document.getElementById('command-message');
                    messageDiv.textContent = data.message;
                })
                .catch((err) => console.error('Validation Error:', err));
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
