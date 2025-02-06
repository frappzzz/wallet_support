// script.js
let currentUser = null;
const socket = io();

function loadMessages(id_user_tg) {
    currentUser = id_user_tg;
    fetch(`/get_messages/${id_user_tg}`)
        .then(response => response.json())
        .then(messages => {
            const messagesDiv = document.getElementById('messages');
            messagesDiv.innerHTML = '';
            messages.forEach(msg => {
                const messageElement = document.createElement('div');
                messageElement.className = `message ${msg.type === 'user' ? 'user-message' : 'bot-message'}`;
                messageElement.textContent = msg.message;
                messagesDiv.appendChild(messageElement);
            });
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        });
}

function handleKeyPress(event) {
    if (event.key === 'Enter') sendMessage();
}

function sendMessage() {
    if (!currentUser) return;
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    if (!message) return;

    fetch('/send_message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id_user_tg: currentUser, message })
    }).then(() => {
        input.value = '';
    });
}

socket.on('update_messages', function(data) {
    if (currentUser === data.id_user_tg) {
        const messagesDiv = document.getElementById('messages');
        const messageElement = document.createElement('div');
        messageElement.className = `message ${data.type === 'user' ? 'user-message' : 'bot-message'}`;
        messageElement.textContent = data.message;
        messagesDiv.appendChild(messageElement);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
});