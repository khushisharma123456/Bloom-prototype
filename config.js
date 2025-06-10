// Configuration file for the chatbot
// This file contains API configurations and other settings

// API Configuration
const CONFIG = {
    GEMINI_API_KEY: '', // Add your Gemini API key here
    API_ENDPOINT: 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent',
    MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
    SUPPORTED_FILE_TYPES: {
        images: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
        videos: ['video/mp4', 'video/webm'],
        documents: ['text/plain', 'application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    }
};

// Make CONFIG available globally
window.CONFIG = CONFIG;
