// Ensure the socket connection is not established immediately,
// but only after a username is set.
// The URL should point to your Flask-SocketIO server, which is usually on the same domain/port as your Flask app.
// If your Flask app is on http://127.0.0.1:5000, then the socket.io URL should also be that.
// If you're using a separate Socket.IO server on port 3001, keep that URL.
// For now, let's assume it's on the same Flask server, so we initialize it later.
let socket = null; // Initialize as null, will be set after username

// const socketIO = ('http://localhost:3001');
const chatToggle = document.getElementById('chatToggle');
const chatContainer = document.getElementById('chatContainer');
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');

// New elements for in-chat username input (assuming you've added them to index.html)
const chatUsernameSection = document.getElementById('chatUsernameSection');
const chatUsernameInput = document.getElementById('chatUsernameInput');
const setChatUsernameButton = document.getElementById('setChatUsernameButton');
const chatInputSection = document.getElementById('chatInputSection'); // The section containing messageInput and sendButton
const newMessageIndicator = document.createElement('div'); // Create the indicator
newMessageIndicator.classList.add('new-message-indicator');
chatToggle.appendChild(newMessageIndicator); // Add it to the toggle

let isChatVisible = false;
let currentUser = ''; // To store the username entered in the chatbox

// --- EVENT LISTENERS ---

// Chat Toggle button behavior
chatToggle.addEventListener('click', () => {
    isChatVisible = !isChatVisible;
    chatContainer.style.display = isChatVisible ? 'flex' : 'none';
    chatToggle.classList.remove('has-new-message'); // Remove the class when chat opens
    if (isChatVisible) {
        // If chat is now visible, scroll to the bottom of messages
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});

// Set Username button behavior
setChatUsernameButton.addEventListener('click', () => {
    const usernameAttempt = chatUsernameInput.value.trim();

    if (usernameAttempt) {
        currentUser = usernameAttempt; // Store the chosen username
        addMessage('System', `Your username is now: ${currentUser}. Connected to chat...`, 'system-message');

        // Hide username input and show chat input
        chatUsernameSection.style.display = 'none';
        chatInputSection.style.display = 'flex';

        // --- Initialize Socket.IO connection after username is set ---
        // Connect to your Flask-SocketIO server.
        // If your Flask app runs on http://127.0.0.1:5000, then it's just '/'
        // If you still have a separate Socket.IO server on port 3001, use 'http://localhost:3001'
        // For this example, assuming it's served by the Flask app.
        socket = io('http://127.0.0.1:8000'); // Pass username with connection

        // Socket.IO Connection Events
        // socket.on('connect', () => {
        //     addMessage('System', 'Connected to chat server!', 'system-message');
        //     // Emit the 'join' event with the username after successful connection
        //     socket.emit('join', currentUser);
        // });

        socket.on('disconnect', () => {
            addMessage('System', 'Disconnected from chat server.', 'system-message');
        });

        // Listen for incoming messages from the server
        socket.on('message', (message) => {
            // console.log('Received message:', message); // For debugging
            displayMessage(message.sender, message.text);
            // Show indicator if chat is not visible and message is not from self
            if (!isChatVisible && message.sender !== 'currentUser') {
                chatToggle.classList.add('has-new-message');
            }
        });

        // Listen for user join/leave events from the server
        socket.on('userJoined', (data) => {
            addMessage('System', `${data.username} joined the chat.`, 'system-message');
        });

        socket.on('userLeft', (data) => {
            addMessage('System', `${data.username} left the chat.`, 'system-message');
        });

    } else {
        alert('Please enter a username to join the chat.');
    }
});


// Send message button behavior
sendButton.addEventListener('click', () => {
    // Check if socket is connected and user has a username
    if (socket && socket.connected && currentUser) {
        const messageText = messageInput.value.trim();
        if (messageText !== '') {
            // Emit message to server, including the sender's username
            socket.emit('message', { sender: currentUser, text: messageText });
            messageInput.value = ''; // Clear input field
        }
    } else {
        addMessage('System', 'Please set a username and connect to chat first.', 'system-message');
    }
});

// Send message on Enter key press
messageInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault(); // Prevent new line in textarea
        // Trigger the click event of the send button
        sendButton.click();
    }
});


// --- HELPER FUNCTIONS ---

function addMessage(user, text, className) {
    const messageElement = document.createElement('div'); // Using div for better styling control
    messageElement.classList.add('message', className); // Add base 'message' class and specific class
    messageElement.innerHTML = `<strong>${user}:</strong> ${text}`;
    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight; // Auto-scroll to bottom
}

function displayMessage(sender, text) {
    console.log('Sender of received message:', sender);
    console.log('My username in displayMessage:', currentUser);
    const newMessage = document.createElement('p')
    const displayedSender = sender === currentUser ? 'You' : sender; // Use 'You' for self-sent messages
    const className = sender === currentUser ? 'user-message' : 'other-message'; // Apply specific class for styling
    addMessage(displayedSender, text, className);

    console.log('Message displayed:', `${displayedSender}: ${text}`);
}