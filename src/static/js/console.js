document.addEventListener('DOMContentLoaded', function() {
    const socket = io();
    const userInput = document.getElementById('user-input');
    const submitButton = document.getElementById('submit-button');
    const responseArea = document.getElementById('response-area');

    // Listen for console output from the server
    socket.on('console_output', function(data) {
        responseArea.innerHTML += `<div class="message">${data.message}</div>`;
        responseArea.scrollTop = responseArea.scrollHeight;
    });

    submitButton.addEventListener('click', function() {
        const query = userInput.value;
        if (query.trim() === '') {
            return;
        }

        responseArea.innerHTML += `<div>User: ${query}</div>`;
        userInput.value = '';

        fetch('/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: query })
        })
        .then(response => response.json())
        .then(data => {
            responseArea.innerHTML += `<div>Agent: ${data.response}</div>`;
            responseArea.scrollTop = responseArea.scrollHeight; // Scroll to the bottom
        })
        .catch(error => {
            console.error('Error:', error);
            responseArea.innerHTML += `<div>Error: ${error.message}</div>`;
        });
    });

    userInput.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            submitButton.click();
        }
    });
});