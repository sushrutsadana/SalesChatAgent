const APP_VERSION = '1.1';
console.log('Chat app version:', APP_VERSION);

let conversationHistory = [];

const chatForm = document.getElementById('chat-form');
const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const loadingIndicator = document.getElementById('loading');

chatForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const message = userInput.value.trim();
    if (!message) return;

    addMessage(message, 'user');
    userInput.value = '';
    loadingIndicator.style.display = 'block';

    try {
        conversationHistory.push({
            role: 'user',
            content: message
        });

        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                message, 
                history: conversationHistory 
            })
        });

        const data = await response.json();
        
        conversationHistory.push({
            role: 'assistant',
            content: data.message
        });

        addMessage(data, 'bot');
    } catch (error) {
        console.error('Error:', error);
        addMessage('Sorry, I encountered an error. Please try again.', 'bot');
    } finally {
        loadingIndicator.style.display = 'none';
    }
});

function addMessage(content, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;

    if (type === 'user') {
        messageDiv.textContent = content;
    } else {
        try {
            // Add the message text
            const textDiv = document.createElement('div');
            textDiv.className = 'bot-text';
            textDiv.textContent = content.message;
            messageDiv.appendChild(textDiv);

            // Add product buttons if there are products
            if (content.products && content.products.length > 0) {
                const productsDiv = document.createElement('div');
                productsDiv.className = 'product-buttons';

                content.products.forEach(product => {
                    const productLink = document.createElement('a');
                    productLink.href = product.url;
                    productLink.className = 'product-button';
                    productLink.target = '_blank';
                    
                    // Clean up the title
                    const displayTitle = product.title
                        .replace(/([a-z])([A-Z])/g, '$1 $2')
                        .replace(/\s+/g, ' ')
                        .trim();

                    productLink.innerHTML = `
                        <div class="product-info">
                            <div class="product-name">${displayTitle}</div>
                            <div class="product-price">${product.price}</div>
                        </div>
                    `;
                    productsDiv.appendChild(productLink);
                });

                messageDiv.appendChild(productsDiv);
            }
        } catch (error) {
            console.error('Error rendering message:', error);
            messageDiv.textContent = 'Error displaying message';
        }
    }

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
} 