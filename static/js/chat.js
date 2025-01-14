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
        const textDiv = document.createElement('div');
        textDiv.className = 'bot-text';
        textDiv.textContent = content.message;
        messageDiv.appendChild(textDiv);

        if (content.products && content.products.length > 0) {
            const productsDiv = document.createElement('div');
            productsDiv.className = 'product-buttons';

            content.products.forEach(product => {
                const button = document.createElement('a');
                button.href = product.url;
                button.target = '_blank';
                button.className = 'product-button';
                
                const title = product.title
                    .replace(/([a-z])([A-Z])/g, '$1 $2')
                    .replace(/\s+/g, ' ')
                    .trim();

                button.innerHTML = `
                    <div class="product-info">
                        <div class="product-name">${title}</div>
                        <div class="product-price">${product.price}</div>
                    </div>
                `;
                productsDiv.appendChild(button);
            });

            messageDiv.appendChild(productsDiv);
        }
    }

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
} 