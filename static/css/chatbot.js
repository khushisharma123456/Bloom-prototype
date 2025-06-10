// chatbot.js
document.addEventListener('DOMContentLoaded', async function() {
    try {
        // Load API key first
        await loadApiKey();
        
        // Then load prompt template
        const template = await loadPromptTemplate();
        if (!template) {
            console.error('Failed to load prompt template');
        }
    } catch (error) {
        console.error('Initialization error:', error);
    }

    // DOM Elements
    const chatContainer = document.getElementById('chatContainer');
    const userInput = document.getElementById('userInput');
    const sendButton = document.getElementById('sendBtn');
    const chatHistoryList = document.getElementById('chatHistoryList');
    const newChatBtn = document.getElementById('newChatBtn');
    const clearHistoryBtn = document.querySelector('.clear-history');
    const welcomeScreen = document.getElementById('welcomeScreen');
    const chatMessages = document.getElementById('chatMessages');

    // State variables
    let currentChatId = null;
    let chats = JSON.parse(localStorage.getItem('chats')) || {};
    let isTyping = false;

    // Speech Recognition Setup
    const micBtn = document.getElementById('micBtn');
    let recognition = null;
    let isRecording = false;

    // File handling setup
    const fileInput = document.getElementById('fileInput');
    const attachmentDropdown = document.getElementById('attachmentDropdown');
    const attachmentBtn = document.getElementById('attachmentBtn');

    // Add these variables at the top of the file
    let GEMINI_API_KEY = '';
    const PROMPT_TEMPLATE_PATH = 'templates/prompt_template.txt';

    // Initialize the chat
    initChat();

    // Event Listeners
    if (sendButton) {
        sendButton.addEventListener('click', sendMessage);
    }
    if (userInput) {
        userInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !isTyping) {
                sendMessage();
            }
        });
    }
    if (newChatBtn) {
        newChatBtn.addEventListener('click', createNewChat);
    }
    if (clearHistoryBtn) {
        clearHistoryBtn.addEventListener('click', clearChatHistory);
    }

    // Handle attachment dropdown items
    document.querySelectorAll('.dropdown-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const type = this.getAttribute('data-type');
            handleAttachment(type);
        });
    });

    // Initialize speech recognition
    function initSpeechRecognition() {
        if ('webkitSpeechRecognition' in window) {
            recognition = new webkitSpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = true;
            recognition.lang = 'en-US';

            recognition.onstart = function() {
                isRecording = true;
                micBtn.classList.add('recording');
                showToast('Listening...');
            };

            recognition.onresult = function(event) {
                const transcript = Array.from(event.results)
                    .map(result => result[0].transcript)
                    .join('');
                
                userInput.value = transcript;
            };

            recognition.onerror = function(event) {
                console.error('Speech recognition error:', event.error);
                showToast('Error: ' + event.error);
                stopRecording();
            };

            recognition.onend = function() {
                stopRecording();
            };
        } else {
            micBtn.style.display = 'none';
            console.error('Speech recognition not supported');
        }
    }

    // Start recording
    function startRecording() {
        if (recognition && !isRecording) {
            recognition.start();
        }
    }

    // Stop recording
    function stopRecording() {
        if (recognition && isRecording) {
            recognition.stop();
            isRecording = false;
            micBtn.classList.remove('recording');
        }
    }

    // Toggle recording
    function toggleRecording() {
        if (isRecording) {
            stopRecording();
        } else {
            startRecording();
        }
    }

    // Initialize speech recognition
    initSpeechRecognition();

    // Add click event listener to microphone button
    if (micBtn) {
        micBtn.addEventListener('click', toggleRecording);
    }

    // Modify sendMessage to handle speech input
    const originalSendMessage = sendMessage;
    sendMessage = function() {
        if (isRecording) {
            stopRecording();
        }
        originalSendMessage();
    };

    // Initialize chat
    function initChat() {
        renderChatHistory();
        showWelcomeScreen();
    }

    // Show welcome screen
    function showWelcomeScreen() {
        welcomeScreen.style.display = 'flex';
        chatMessages.style.display = 'none';
        currentChatId = null;
    }

    // Create new chat
    function createNewChat() {
        currentChatId = generateChatId();
        chats[currentChatId] = {
            id: currentChatId,
            title: 'New Chat',
            messages: [],
            timestamp: new Date().toISOString()
        };
        saveChats();
        welcomeScreen.style.display = 'none';
        chatMessages.style.display = 'block';
        renderMessages();
        renderChatHistory();
    }    // Modify sendMessage to handle file uploads
    sendMessage = async function() {
        if (isRecording) {
            stopRecording();
        }

        const message = userInput.value.trim();
        const filePreviews = document.querySelectorAll('.file-preview');
        
        if ((message === '' && filePreviews.length === 0) || isTyping) return;

        // If no current chat exists, create one
        if (!currentChatId) {
            createNewChat();
        }

        // Collect attachment data from file previews
        let attachments = [];
        if (filePreviews.length > 0) {
            // Get attachment data from stored chat attachments
            if (chats[currentChatId].attachments) {
                attachments = chats[currentChatId].attachments.slice(); // Copy the array
                // Clear stored attachments after using them
                chats[currentChatId].attachments = [];
            }
            
            // Clear previews
            filePreviews.forEach(preview => preview.remove());
        }        // Add user message to chat with attachments
        const userMessage = {
            sender: 'user',
            text: message,
            timestamp: new Date().toISOString(),
            attachments: attachments
        };
        
        chats[currentChatId].messages.push(userMessage);
        saveChats();
        
        // Clear input
        userInput.value = '';
        
        // Reset placeholder text
        userInput.placeholder = 'Type a message...';
          // Force refresh of messages to ensure proper rendering
        setTimeout(() => {
            forceRefreshChat();
        }, 100);
        
        // Update chat title if it's the first user message
        if (chats[currentChatId].messages.length === 1) {
            updateChatTitle(message);
        }
        
        // Show typing indicator
        showTypingIndicator();
        
        // Generate AI response after a delay
        setTimeout(() => {
            hideTypingIndicator();
            generateAIResponse(message);
        }, 1500);
    };    // Add message to chat
    function addMessageToChat(sender, text) {
        const message = {
            sender,
            text,
            timestamp: new Date().toISOString()
        };
        
        chats[currentChatId].messages.push(message);
        saveChats();
          // Force refresh of messages to ensure proper rendering
        setTimeout(() => {
            forceRefreshChat();
        }, 50);
        
        // Update chat title if it's the first user message
        if (sender === 'user' && chats[currentChatId].messages.length === 1) {
            updateChatTitle(text);
        }
    }    // Render all messages in current chat
    function renderMessages() {
        if (!chatMessages) return;
        
        // Store current scroll position
        const wasAtBottom = chatContainer.scrollTop >= (chatContainer.scrollHeight - chatContainer.clientHeight - 50);
        
        chatMessages.innerHTML = '';
        
        chats[currentChatId]?.messages?.forEach((msg, index) => {
            if (msg.sender === 'user') {
                chatMessages.appendChild(createUserMessageElement(msg.text, msg.timestamp, index));
            } else {
                chatMessages.appendChild(createAIMessageElement(msg.text, msg.timestamp, index));
            }
        });
        
        // Scroll to bottom if we were already at bottom or if it's a new message
        if (wasAtBottom) {
            scrollToBottom();
        }
    }// Create user message element with all functionality
    function createUserMessageElement(text, timestamp, messageIndex) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'user-prompt';
        messageDiv.dataset.messageIndex = messageIndex;
        
        const message = chats[currentChatId].messages[messageIndex];
        let attachmentsHtml = '';
        
        if (message.attachments && message.attachments.length > 0) {
            attachmentsHtml = '<div class="message-attachments">';
            attachmentsHtml += message.attachments.map(attachment => {
                let iconClass = 'fa-file';
                if (attachment.type === 'photo') {
                    iconClass = 'fa-image';
                } else if (attachment.type === 'video') {
                    iconClass = 'fa-video';
                } else if (attachment.mimeType === 'application/pdf') {
                    iconClass = 'fa-file-pdf';
                } else if (attachment.mimeType && attachment.mimeType.includes('word')) {
                    iconClass = 'fa-file-word';
                } else if (attachment.mimeType === 'text/plain') {
                    iconClass = 'fa-file-text';
                } else if (attachment.mimeType === 'application/json') {
                    iconClass = 'fa-file-code';
                } else if (attachment.mimeType === 'text/csv') {
                    iconClass = 'fa-file-csv';
                }
                
                return `<div class="message-attachment">
                    <i class="fas ${iconClass}"></i>
                    <span class="attachment-name">${attachment.fileName}</span>
                    <span class="attachment-size">(${attachment.fileSize})</span>
                </div>`;
            }).join('');
            attachmentsHtml += '</div>';
        }
        
        messageDiv.innerHTML = `
            <div class="up">
                <i class="fas fa-user-circle" style="font-size: 24px; color: white;"></i>
                <div class="message-content">
                    <p class="message-text">${text}</p>
                    ${attachmentsHtml}
                    <div class="message-actions">
                        <button class="action-btn copy-btn" title="Copy">
                            <i class="far fa-copy"></i>
                        </button>
                        <button class="action-btn edit-btn" title="Edit">
                            <i class="far fa-edit"></i>
                        </button>
                        <button class="action-btn delete-btn" title="Delete">
                            <i class="far fa-trash-alt"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Add functionality to buttons
        addMessageFunctionality(messageDiv, text, messageIndex);
        
        return messageDiv;
    }

    // Create AI message element with all functionality
    function createAIMessageElement(text, timestamp, messageIndex) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'ai-prompt';
        messageDiv.dataset.messageIndex = messageIndex;
        
        messageDiv.innerHTML = `
            <div class="up">
                <img src="static/Images/logo1.png" alt="Bloom AI" class="ai-logo">
                <div class="message-content">
                    <p class="message-text">${text}</p>
                    <div class="message-actions">
                        <button class="action-btn copy-btn" title="Copy">
                            <i class="far fa-copy"></i>
                        </button>
                        <button class="action-btn thumbs-up" title="Helpful">
                            <i class="far fa-thumbs-up"></i>
                        </button>
                        <button class="action-btn thumbs-down" title="Not helpful">
                            <i class="far fa-thumbs-down"></i>
                        </button>
                        <button class="action-btn delete-btn" title="Delete">
                            <i class="far fa-trash-alt"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Add functionality to buttons
        addMessageFunctionality(messageDiv, text, messageIndex);
        
        return messageDiv;
    }

    // Add functionality to message buttons
    function addMessageFunctionality(messageDiv, text, messageIndex) {
        // Copy button
        const copyBtn = messageDiv.querySelector('.copy-btn');
        if (copyBtn) {
            copyBtn.addEventListener('click', () => {
                navigator.clipboard.writeText(text)
                    .then(() => showToast('Message copied to clipboard!'))
                    .catch(err => console.error('Failed to copy:', err));
            });
        }
        
        // Edit button (only for user messages)
        const editBtn = messageDiv.querySelector('.edit-btn');
        if (editBtn) {
            editBtn.addEventListener('click', () => editMessage(messageDiv, text, messageIndex));
        }
        
        // Delete button
        const deleteBtn = messageDiv.querySelector('.delete-btn');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => deleteMessage(messageIndex));
        }
        
        // Feedback buttons (only for AI messages)
        const thumbsUp = messageDiv.querySelector('.thumbs-up');
        if (thumbsUp) {
            thumbsUp.addEventListener('click', () => rateMessage(messageIndex, 'positive'));
        }
        
        const thumbsDown = messageDiv.querySelector('.thumbs-down');
        if (thumbsDown) {
            thumbsDown.addEventListener('click', () => rateMessage(messageIndex, 'negative'));
        }
    }

    // Edit message functionality
    function editMessage(messageDiv, originalText, messageIndex) {
        const messageContent = messageDiv.querySelector('.message-content');
        if (!messageContent) return;
        
        messageContent.innerHTML = `
            <textarea class="edit-textarea">${originalText}</textarea>
            <div class="edit-actions">
                <button class="action-btn save-edit">Save</button>
                <button class="action-btn cancel-edit">Cancel</button>
            </div>
        `;
        
        const textarea = messageContent.querySelector('.edit-textarea');
        textarea.focus();
        textarea.setSelectionRange(textarea.value.length, textarea.value.length);
        
        const saveBtn = messageContent.querySelector('.save-edit');
        const cancelBtn = messageContent.querySelector('.cancel-edit');
        
        saveBtn.addEventListener('click', () => {
            const newText = textarea.value.trim();
            if (newText && newText !== originalText) {
                updateMessageText(messageIndex, newText);
            }
            renderMessages();
        });
        
        cancelBtn.addEventListener('click', renderMessages);
    }

    // Delete message functionality
    function deleteMessage(messageIndex) {
        if (confirm('Are you sure you want to delete this message?')) {
            chats[currentChatId].messages.splice(messageIndex, 1);
            saveChats();
            renderMessages();
            
            // Update chat title if we deleted the first message
            if (chats[currentChatId].messages.length === 0) {
                updateChatTitle('New Chat');
            }
        }
    }

    // Rate message functionality
    function rateMessage(messageIndex, rating) {
        if (chats[currentChatId] && chats[currentChatId].messages[messageIndex]) {
            chats[currentChatId].messages[messageIndex].rating = rating;
            saveChats();
            showToast(`Thank you for your feedback!`);
        }
    }

    // Update message text in chat history
    function updateMessageText(messageIndex, newText) {
        if (chats[currentChatId] && chats[currentChatId].messages[messageIndex]) {
            chats[currentChatId].messages[messageIndex].text = newText;
            saveChats();
            
            // Update chat title if this was the first message
            if (messageIndex === 0) {
                updateChatTitle(newText);
            }
        }
    }

    // Render chat history list
    function renderChatHistory() {
        if (!chatHistoryList) return;
        
        chatHistoryList.innerHTML = '';
        
        if (Object.keys(chats).length === 0) {
            chatHistoryList.innerHTML = '<p class="no-history-message">No previous chats</p>';
            return;
        }
        
        // Sort chats by timestamp (newest first)
        const sortedChats = Object.values(chats).sort((a, b) => 
            new Date(b.timestamp) - new Date(a.timestamp)
        );
        
        sortedChats.forEach(chat => {
            const chatItem = document.createElement('div');
            chatItem.className = `chat-history-item ${chat.id === currentChatId ? 'active' : ''}`;
            
            const date = new Date(chat.timestamp);
            const dateStr = date.toLocaleDateString('en-US', { 
                month: 'short', 
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
            
            // Get the first user message as preview if available
            const firstUserMessage = chat.messages.find(msg => msg.sender === 'user');
            const previewText = firstUserMessage ? 
                firstUserMessage.text.substring(0, 30) + (firstUserMessage.text.length > 30 ? '...' : '') : 
                'New Chat';
            
            chatItem.innerHTML = `
                <div class="chat-info">
                    <div class="chat-date">${dateStr}</div>
                    <div class="chat-preview">${previewText}</div>
                </div>
                <button class="delete-chat-btn" title="Delete chat">
                    <i class="far fa-trash-alt"></i>
                </button>
            `;
            
            // Load chat when clicked
            chatItem.addEventListener('click', () => loadChat(chat.id));
            
            // Delete chat button
            const deleteBtn = chatItem.querySelector('.delete-chat-btn');
            if (deleteBtn) {
                deleteBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    deleteChatFromHistory(chat.id);
                });
            }
            
            chatHistoryList.appendChild(chatItem);
        });
    }

    // Delete chat from history
    function deleteChatFromHistory(chatId) {
        if (confirm('Are you sure you want to delete this chat?')) {
            delete chats[chatId];
            saveChats();
            
            // If we deleted the current chat, create a new one
            if (chatId === currentChatId) {
                createNewChat();
            } else {
                renderChatHistory();
            }
        }
    }

    // Load specific chat
    function loadChat(chatId) {
        currentChatId = chatId;
        welcomeScreen.style.display = 'none';
        chatMessages.style.display = 'block';
        renderMessages();
        renderChatHistory();
    }

    // Update chat title
    function updateChatTitle(firstMessage) {
        const title = firstMessage.substring(0, 30) + (firstMessage.length > 30 ? '...' : '');
        chats[currentChatId].title = title;
        saveChats();
        renderChatHistory();
    }

    // Clear all chat history
    function clearChatHistory() {
        if (confirm('Are you sure you want to clear all chat history?')) {
            chats = {};
            saveChats();
            showWelcomeScreen();
            renderChatHistory();
        }
    }

    // Save chats to localStorage
    function saveChats() {
        localStorage.setItem('chats', JSON.stringify(chats));
    }

    // Show typing indicator
    function showTypingIndicator() {
        isTyping = true;
        const typingDiv = document.createElement('div');
        typingDiv.className = 'ai-prompt typing-indicator';
        typingDiv.innerHTML = `
            <div class="up">
                <img src="static/Images/logo1.png" alt="Bloom AI" class="ai-logo">
                <div class="message-content">
                    <div class="typing-dots">
                        <div class="dot"></div>
                        <div class="dot"></div>
                        <div class="dot"></div>
                    </div>
                </div>
            </div>
        `;
        chatContainer.appendChild(typingDiv);
        scrollToBottom();
    }

    // Hide typing indicator
    function hideTypingIndicator() {
        isTyping = false;
        const typingIndicator = document.querySelector('.typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    // Show toast notification
    function showToast(message) {
        const toast = document.createElement('div');
        toast.className = 'toast-notification';
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);
        
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                toast.remove();
            }, 300);
        }, 3000);
    }

    // Scroll chat to bottom
    function scrollToBottom() {
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }    // Generate chat ID
    function generateChatId() {
        return 'chat-' + Math.random().toString(36).substr(2, 9);
    }

    // Force refresh the chat UI
    function forceRefreshChat() {
        if (!currentChatId) return;
        
        // Clear and re-render messages
        if (chatMessages) {
            chatMessages.innerHTML = '';
            setTimeout(() => {
                renderMessages();
            }, 10);
        }
        
        // Update chat history
        setTimeout(() => {
            renderChatHistory();
        }, 20);
    }

    // Function to load API key from .env file

// Replace the loadApiKey function with this:
async function loadApiKey() {
    try {
        const response = await fetch('/api/get-api-key');
        if (!response.ok) {
            throw new Error('Failed to load API key from server');
        }
        const data = await response.json();
        if (!data.apiKey) {
            throw new Error('No API key received from server');
        }
        GEMINI_API_KEY = data.apiKey;
        console.log('API key loaded successfully');
    } catch (error) {
        console.error('Error loading API key:', error);
        // Show error to user
        addMessageToChat('assistant', "I'm having trouble connecting to the AI service. Please try again later.");
        throw error;
    }
}

    // Modify the callGeminiAPI function in chatbot.js to use the correct endpoint
async function callGeminiAPI(prompt) {
    try {
        if (!GEMINI_API_KEY) {
            throw new Error('API key not loaded');
        }

        // Updated API URL - note the model name change
        const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro-latest:generateContent?key=${GEMINI_API_KEY}`;
        
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                contents: [{
                    parts: [{
                        text: prompt
                    }]
                }]
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`API request failed: ${response.status} - ${JSON.stringify(errorData)}`);
        }

        const data = await response.json();
        
        if (!data.candidates?.[0]?.content?.parts?.[0]?.text) {
            throw new Error('Invalid API response format');
        }

        return data.candidates[0].content.parts[0].text;
    } catch (error) {
        console.error('Error calling Gemini API:', error);
        throw error;
    }
}

async function loadPromptTemplate() {
    try {
        const response = await fetch('/api/get-prompt-template');
        if (!response.ok) {
            throw new Error('Failed to load prompt template');
        }
        return await response.text();
    } catch (error) {
        console.error('Error loading prompt template:', error);
        // Fallback template if the request fails
        return `You are Bloom, a helpful AI assistant focused on women's health and wellness. 
Respond to the user's query in a friendly, professional tone.

User Query: {USER_QUERY}

Response:`;
    }
}

// Function to format prompt with user query
function formatPrompt(template, userQuery) {
    if (!template) {
        // Fallback if no template is available
        return `User Query: ${userQuery}\n\nResponse:`;
    }
    return template.replace('{USER_QUERY}', userQuery);
}    // Modify the existing generateAIResponse function
    async function generateAIResponse(userMessage) {
    try {
        // Load prompt template
        const template = await loadPromptTemplate();
        
        // Get the current message with attachments
        const currentMessage = chats[currentChatId].messages[chats[currentChatId].messages.length - 1];
        let enhancedPrompt = userMessage;
          // If there are attachments, include their content in the prompt
        if (currentMessage.attachments && currentMessage.attachments.length > 0) {
            let attachmentContext = '\n\nAttached Files:\n';
            let hasProcessableText = false;
            
            for (const attachment of currentMessage.attachments) {
                if (attachment.type === 'file') {
                    try {
                        // Extract text content from document files
                        const textContent = await extractTextFromFile(attachment.fileData, attachment.mimeType);
                        if (textContent) {
                            attachmentContext += `\nFile: ${attachment.fileName}\nContent:\n${textContent}\n`;
                            if (attachment.mimeType === 'text/plain' || attachment.mimeType === 'application/json' || attachment.mimeType === 'text/csv') {
                                hasProcessableText = true;
                            }
                        } else {
                            attachmentContext += `\nFile: ${attachment.fileName} (${attachment.fileSize}) - Unable to extract text content\n`;
                        }
                    } catch (error) {
                        console.error('Error extracting text from file:', error);
                        attachmentContext += `\nFile: ${attachment.fileName} (${attachment.fileSize}) - Error processing file\n`;
                    }
                } else if (attachment.type === 'photo') {
                    attachmentContext += `\nImage: ${attachment.fileName} (${attachment.fileSize}) - Image file attached\n`;
                } else if (attachment.type === 'video') {
                    attachmentContext += `\nVideo: ${attachment.fileName} (${attachment.fileSize}) - Video file attached\n`;
                }
            }
            
            enhancedPrompt += attachmentContext;
            
            // If user didn't provide a specific question but uploaded processable text, provide guidance
            if (hasProcessableText && (!userMessage || userMessage.trim().length < 10)) {
                enhancedPrompt += '\n\nUser has uploaded a document with text content. Please acknowledge that you have received and can analyze the document, and ask what specific questions they have about the content or how they would like you to help with the document.';
            }
        }
        
        // Format prompt with enhanced message including attachments
        const formattedPrompt = formatPrompt(template, enhancedPrompt);
        console.log('Formatted prompt:', formattedPrompt);

        // Call Gemini API
        const aiResponse = await callGeminiAPI(formattedPrompt);

        // Add AI response to chat
        addMessageToChat('assistant', aiResponse);
        
        // Save chat
        saveChats();
    } catch (error) {
        console.error('Error generating AI response:', error);
        addMessageToChat('assistant', `I apologize, but I encountered an error: ${error.message}. Please try again.`);
    }
}

    // Function to extract text content from uploaded files
    async function extractTextFromFile(base64Data, mimeType) {
        try {
            // For text files, extract content directly
            if (mimeType === 'text/plain' || mimeType === 'text/csv') {
                const base64Content = base64Data.split(',')[1];
                const textContent = atob(base64Content);
                return textContent;
            }
            
            // For JSON files
            if (mimeType === 'application/json') {
                const base64Content = base64Data.split(',')[1];
                const jsonContent = atob(base64Content);
                try {
                    const parsedJson = JSON.parse(jsonContent);
                    return `JSON Content:\n${JSON.stringify(parsedJson, null, 2)}`;
                } catch (e) {
                    return jsonContent; // Return raw content if JSON parsing fails
                }
            }
            
            // For other document types, we'll provide basic file info
            // In a production environment, you'd use libraries like pdf-lib for PDFs
            // or mammoth.js for Word documents
            if (mimeType === 'application/pdf') {
                return `[PDF Document - To analyze the content of this PDF, please copy and paste the relevant text portions you'd like me to review. I can help with document analysis, summarization, and answering questions about the content once you provide the text.]`;
            }
            
            if (mimeType.includes('word') || mimeType.includes('document')) {
                return `[Word Document - To analyze the content of this document, please copy and paste the relevant text portions you'd like me to review. I can help with document analysis, editing suggestions, and answering questions about the content once you provide the text.]`;
            }
            
            // For unsupported file types
            return `[File type ${mimeType} - Content extraction not supported. Please describe the content or copy relevant text that you'd like me to analyze.]`;
            
        } catch (error) {
            console.error('Error extracting text from file:', error);
            return `[Error processing file - Please try uploading the file again or copy the text content manually.]`;
        }
    }// Handle attachment selection
    function handleAttachment(type) {
        // Set accept attribute based on type
        switch(type) {
            case 'photo':
                fileInput.accept = 'image/*';
                break;
            case 'video':
                fileInput.accept = 'video/*';
                break;
            case 'file':
                fileInput.accept = '.txt,.pdf,.doc,.docx,.rtf,.csv,.json';
                break;
        }

        // Trigger file input click
        fileInput.click();
    }

    // Handle file selection
    fileInput.addEventListener('change', async function(e) {
        const file = e.target.files[0];
        if (file) {
            try {
                // Show loading state
                showToast('Processing file...');
                
                // Check file size (limit to 10MB)
                const maxSize = 10 * 1024 * 1024; // 10MB in bytes
                if (file.size > maxSize) {
                    showToast('File size too large. Please upload a file less than 10MB');
                    // Add a message to the chat about the file size limit
                    addMessageToChat('assistant', 'I notice you tried to upload a file. Please make sure your file is less than 10MB in size. You can try compressing the file or choosing a smaller one.');
                    return;
                }                // Validate file type before processing
                const fileType = fileInput.accept;
                if (fileType.includes('image') && !file.type.startsWith('image/')) {
                    showToast('Please select a valid image file (JPG, PNG, GIF)');
                    addMessageToChat('assistant', 'I can only process image files in JPG, PNG, or GIF format. Please try again with a supported image file.');
                    return;
                }
                if (fileType.includes('video') && !file.type.startsWith('video/')) {
                    showToast('Please select a valid video file (MP4, WebM)');
                    addMessageToChat('assistant', 'I can only process video files in MP4 or WebM format. Please try again with a supported video file.');
                    return;
                }
                if (fileType.includes('.txt,.pdf,.doc,.docx') && 
                    !['text/plain', 'application/pdf', 'application/msword', 
                      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                      'text/csv', 'application/json'].includes(file.type)) {
                    showToast('Please select a valid document file (TXT, PDF, DOC, DOCX, CSV, JSON)');
                    addMessageToChat('assistant', 'I can process text documents in TXT, PDF, DOC, DOCX, CSV, and JSON formats. Please try again with a supported document file.');
                    return;
                }

                // Read file as base64 with timeout
                const base64File = await Promise.race([
                    readFileAsBase64(file),
                    new Promise((_, reject) => 
                        setTimeout(() => reject(new Error('File processing timeout')), 30000)
                    )
                ]);
                
                // Create a preview message
                const previewMessage = {
                    type: fileInput.accept.includes('image') ? 'photo' : 
                          fileInput.accept.includes('video') ? 'video' : 'file',
                    fileName: file.name,
                    fileSize: formatFileSize(file.size),
                    fileData: base64File,
                    timestamp: new Date().toISOString(),
                    mimeType: file.type
                };
                  // Add preview to chat
                addFilePreviewToChat(previewMessage);
                
                // Ensure we have a current chat to store the file
                if (!currentChatId) {
                    createNewChat();
                }
                
                // Store file data in current chat
                if (!chats[currentChatId].attachments) {
                    chats[currentChatId].attachments = [];
                }
                chats[currentChatId].attachments.push(previewMessage);
                saveChats();
                
                // Show appropriate success message based on file type
                if (previewMessage.type === 'file') {
                    if (previewMessage.mimeType === 'text/plain' || previewMessage.mimeType === 'application/json' || previewMessage.mimeType === 'text/csv') {
                        showToast('Document processed! Text content extracted successfully.');
                    } else {
                        showToast('Document uploaded! Please describe what you\'d like me to help you with.');
                    }
                } else {
                    showToast('File ready to send');
                }
            } catch (error) {
                console.error('Error processing file:', error);
                let errorMessage = 'Error processing file';
                
                if (error.message === 'File processing timeout') {
                    errorMessage = 'File processing took too long. Please try a smaller file.';
                } else if (error.message.includes('Failed to read file')) {
                    errorMessage = 'Unable to read the file. Please make sure it\'s not corrupted.';
                }
                
                showToast(errorMessage);
                addMessageToChat('assistant', `I encountered an issue while processing your file: ${errorMessage}. Please try again with a different file.`);
            } finally {
                // Reset file input
                fileInput.value = '';
            }
        }
    });

    // Read file as base64 with error handling
    function readFileAsBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            
            reader.onload = () => {
                try {
                    // Validate the base64 data
                    const base64Data = reader.result;
                    if (!base64Data.startsWith('data:')) {
                        throw new Error('Invalid file data');
                    }
                    resolve(base64Data);
                } catch (error) {
                    reject(new Error('Failed to process file data'));
                }
            };
            
            reader.onerror = (error) => {
                console.error('Error reading file:', error);
                reject(new Error('Failed to read file'));
            };
            
            reader.onabort = () => {
                reject(new Error('File reading was aborted'));
            };
            
            try {
                reader.readAsDataURL(file);
            } catch (error) {
                reject(new Error('Failed to start file reading'));
            }
        });
    }

    // Format file size
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }    // Add file preview to chat
    function addFilePreviewToChat(fileData) {
        const previewDiv = document.createElement('div');
        previewDiv.className = 'file-preview';
        
        // Determine icon based on file type
        let iconClass = 'fa-file';
        if (fileData.type === 'photo') {
            iconClass = 'fa-image';
        } else if (fileData.type === 'video') {
            iconClass = 'fa-video';
        } else if (fileData.mimeType === 'application/pdf') {
            iconClass = 'fa-file-pdf';
        } else if (fileData.mimeType.includes('word')) {
            iconClass = 'fa-file-word';
        } else if (fileData.mimeType === 'text/plain') {
            iconClass = 'fa-file-text';
        } else if (fileData.mimeType === 'application/json') {
            iconClass = 'fa-file-code';
        } else if (fileData.mimeType === 'text/csv') {
            iconClass = 'fa-file-csv';
        }
        
        previewDiv.innerHTML = `
            <div class="preview-header">
                <i class="fas ${iconClass}"></i>
                <span class="preview-title">${fileData.fileName}</span>
                <span class="file-size">(${fileData.fileSize})</span>
                <button class="remove-preview" onclick="removeFilePreview(this)">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        // Add preview to input area instead of chat messages
        const inputArea = document.querySelector('.input-area');
        const typingWrapper = document.querySelector('.typing-wrapper');
        inputArea.insertBefore(previewDiv, typingWrapper);
        
        // Enable input after adding preview
        userInput.disabled = false;
        userInput.focus();
        
        // Update placeholder text
        userInput.placeholder = `File "${fileData.fileName}" ready to send. Type your message...`;
    }    // Function to remove file preview
    window.removeFilePreview = function(button) {
        const previewDiv = button.closest('.file-preview');
        if (previewDiv) {
            previewDiv.remove();
            // Re-enable input after removing preview
            userInput.disabled = false;
            userInput.focus();
            // Reset placeholder text
            userInput.placeholder = 'Type a message...';
            
            // Remove the file from stored attachments
            if (currentChatId && chats[currentChatId].attachments) {
                const fileName = previewDiv.querySelector('.preview-title').textContent;
                chats[currentChatId].attachments = chats[currentChatId].attachments.filter(
                    attachment => attachment.fileName !== fileName
                );
                saveChats();
            }
        }
    };

    // Test API connection
async function testApiConnection() {
    try {
        await loadApiKey();
        console.log('API key loaded:', GEMINI_API_KEY ? 'Yes' : 'No');
        
        if (GEMINI_API_KEY) {
            const testResponse = await callGeminiAPI("Hello, who are you?");
            console.log('Test API response:', testResponse);
        }
    } catch (error) {
        console.error('API connection test failed:', error);
    }
}

// Call it after initialization
testApiConnection();
});
