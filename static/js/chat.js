const chatForm = document.getElementById('chat-form');
const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const loadingIndicator = document.getElementById('loading');
const voiceButton = document.getElementById('voice-button');

let chatHistory = [];
let isRecording = false;
let recognition = null;

// Chat form submission handler
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const message = userInput.value.trim();
    if (!message) return;

    // Add user message to chat history
    chatHistory.push({
        role: "user",
        content: message
    });

    // Add user message to display
    addMessage(message, 'user');
    userInput.value = '';

    // Show loading indicator
    loadingIndicator.style.display = 'block';

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                message,
                history: chatHistory
            }),
        });

        const data = await response.json();
        
        if (response.ok) {
            // Add bot response to chat history
            chatHistory.push({
                role: "assistant",
                content: data.response
            });
            
            // Add bot response to display
            addMessage(data.response, 'bot', data.products);
        } else {
            addMessage('Sorry, I encountered an error. Please try again.', 'bot');
        }
    } catch (error) {
        addMessage('Sorry, I encountered an error. Please try again.', 'bot');
    } finally {
        loadingIndicator.style.display = 'none';
    }
});

// Message display handler
function addMessage(text, sender, products = []) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    messageDiv.textContent = text;

    if (products && products.length > 0) {
        const linksDiv = document.createElement('div');
        linksDiv.className = 'product-links';
        
        // Create a Set to store unique URLs
        const uniqueProducts = new Map();
        products.forEach(product => {
            if (!uniqueProducts.has(product.url)) {
                // Extract product name from URL
                const urlPath = new URL(product.url).pathname;
                const productName = urlPath
                    .split('/products/')[1]  // Get part after /products/
                    .split('?')[0]  // Remove variant query
                    .replace(/-/g, ' ')  // Replace hyphens with spaces
                    .split(' ')  // Split into words
                    .map(word => word.charAt(0).toUpperCase() + word.slice(1))  // Capitalize each word
                    .join(' ');  // Join back with spaces
                
                uniqueProducts.set(product.url, {
                    url: product.url,
                    displayName: productName
                });
            }
        });
        
        // Add unique product links
        uniqueProducts.forEach(product => {
            const link = document.createElement('a');
            link.href = product.url;
            link.target = '_blank';
            link.textContent = `View: ${product.displayName}`;
            linksDiv.appendChild(link);
            linksDiv.appendChild(document.createElement('br'));
        });
        
        messageDiv.appendChild(linksDiv);
    }

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Voice input initialization
if ('webkitSpeechRecognition' in window) {
    recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = function() {
        isRecording = true;
        voiceButton.classList.add('recording');
        userInput.placeholder = "Listening...";
    };

    recognition.onend = function() {
        isRecording = false;
        voiceButton.classList.remove('recording');
        userInput.placeholder = "Type your message here...";
    };

    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        userInput.value = transcript;
        // Automatically submit the form after voice input
        chatForm.dispatchEvent(new Event('submit'));
    };

    recognition.onerror = function(event) {
        console.error('Speech recognition error:', event.error);
        voiceButton.classList.remove('recording');
        userInput.placeholder = "Type your message here...";
        if (event.error === 'not-allowed') {
            alert('Please enable microphone access to use voice input.');
        }
    };

    voiceButton.addEventListener('click', () => {
        if (!isRecording) {
            recognition.start();
        } else {
            recognition.stop();
        }
    });
} else {
    voiceButton.style.display = 'none';
    console.log('Speech recognition not supported');
}

// Embed code functionality
const embedButton = document.getElementById('embed-button');
const embedModal = document.getElementById('embed-modal');
const modalOverlay = document.getElementById('modal-overlay');
const closeModal = document.getElementById('close-modal');
const closeButton = document.getElementById('close-button');
const copyButton = document.getElementById('copy-button');
const embedCode = document.getElementById('embed-code');

// Replace YOUR_DOMAIN with actual domain
const currentDomain = window.location.origin;
embedCode.textContent = embedCode.textContent.replace(/YOUR_DOMAIN/g, currentDomain);

// Show modal
embedButton.addEventListener('click', () => {
    embedModal.classList.add('active');
    modalOverlay.classList.add('active');
});

// Hide modal
const hideModal = () => {
    embedModal.classList.remove('active');
    modalOverlay.classList.remove('active');
};

closeModal.addEventListener('click', hideModal);
closeButton.addEventListener('click', hideModal);
modalOverlay.addEventListener('click', hideModal);

// Copy embed code
copyButton.addEventListener('click', async () => {
    try {
        await navigator.clipboard.writeText(embedCode.textContent);
        copyButton.innerHTML = '<i class="fas fa-check"></i> Copied!';
        setTimeout(() => {
            copyButton.innerHTML = '<i class="fas fa-copy"></i> Copy Code';
        }, 2000);
    } catch (err) {
        console.error('Failed to copy:', err);
        copyButton.textContent = 'Failed to copy';
    }
}); 