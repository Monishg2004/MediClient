/**
 * Enhanced API service for MediCompanion
 * Handles all API calls to the backend with improved error handling and diagnostics
 */

const API_BASE_URL = 'http://localhost:5000/api';

// API service object
const apiService = {
    /**
     * Make a generic fetch request with retry capability
     * @param {string} endpoint - The API endpoint
     * @param {string} method - HTTP method (GET, POST, etc.)
     * @param {Object} data - Data to send in request body
     * @param {number} retries - Number of retries on failure (default: 2)
     * @returns {Promise<any>} - Response data
     */
    async fetchRequest(endpoint, method = 'GET', data = null, retries = 2) {
        try {
            const url = `${API_BASE_URL}${endpoint}`;
            const headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            };

            const config = {
                method,
                headers,
                mode: 'cors',
                ...(data && { body: JSON.stringify(data) })
            };

            console.log(`API Request: ${method} ${url}`, data ? data : '');
            
            let response;
            try {
                response = await fetch(url, config);
            } catch (networkError) {
                console.error('Network error:', networkError);
                
                // If we have retries left, wait and try again
                if (retries > 0) {
                    console.log(`Retrying request (${retries} attempts left)...`);
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    return this.fetchRequest(endpoint, method, data, retries - 1);
                }
                
                throw new Error('Network error: Unable to connect to the server');
            }
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error(`API Error (${response.status}): ${errorText}`);
                
                // Handle specific error codes
                if (response.status === 401) {
                    throw new Error('Authentication error: Please log in again');
                } else if (response.status === 403) {
                    throw new Error('Permission denied: You do not have access to this resource');
                } else if (response.status === 404) {
                    throw new Error(`Resource not found: ${endpoint}`);
                } else if (response.status === 429) {
                    // Rate limiting - wait and retry
                    if (retries > 0) {
                        console.log('Rate limited, retrying after delay...');
                        await new Promise(resolve => setTimeout(resolve, 2000));
                        return this.fetchRequest(endpoint, method, data, retries - 1);
                    }
                    throw new Error('Rate limit exceeded: Please try again later');
                } else if (response.status >= 500) {
                    throw new Error('Server error: The server encountered an issue processing your request');
                } else {
                    throw new Error(`API request failed: ${errorText || response.statusText}`);
                }
            }

            const responseData = await response.json();
            console.log(`API Response: ${method} ${url}`, responseData);
            return responseData;
        } catch (error) {
            console.error('API request error:', error);
            throw error;
        }
    },

    /**
     * Check API status
     * @returns {Promise<Object>} - Status object
     */
    async checkStatus() {
        return this.fetchRequest('/status');
    },

    /**
     * Start recording session
     * @returns {Promise<Object>} - Recording state
     */
    async startRecording() {
        return this.fetchRequest('/start_recording', 'POST', { value: true });
    },

    /**
     * Stop recording session
     * @returns {Promise<Object>} - Recording state
     */
    async stopRecording() {
        return this.fetchRequest('/stop_recording', 'POST', { value: true });
    },

    /**
     * Get transcript from current recording
     * @returns {Promise<Object>} - Transcript object
     */
    async getTranscript() {
        return this.fetchRequest('/transcript');
    },

    /**
     * Get patient transcript from current recording
     * @returns {Promise<Object>} - Transcript object
     */
    async getPatientTranscript() {
        return this.fetchRequest('/patient_transcript');
    },

    /**
     * Generate clinical notes based on transcript
     * @param {string} doctorsHints - Doctor's notes/hints
     * @returns {Promise<Object>} - Task ID for status polling
     */
    async generateNotes(doctorsHints) {
        return this.fetchRequest('/generate_notes', 'POST', { doctors_hints: doctorsHints });
    },

    /**
     * Check status of notes generation
     * @param {string} taskId - Task ID from generate_notes call
     * @returns {Promise<Object>} - Notes status and content
     */
    async checkNotesStatus(taskId) {
        return this.fetchRequest(`/notes_status/${taskId}`);
    },

    /**
     * Send patient message
     * @param {string} text - Message text
     * @returns {Promise<Object>} - Message ID for status polling
     */
    async sendPatientMessage(text) {
        return this.fetchRequest('/patient_message', 'POST', { text });
    },

    /**
     * Check status of patient message
     * @param {string} messageId - Message ID from sendPatientMessage call
     * @returns {Promise<Object>} - Message status and response
     */
    async checkPatientMessageStatus(messageId) {
        return this.fetchRequest(`/patient_message_status/${messageId}`);
    },

    /**
     * Get differential diagnosis suggestions
     * @returns {Promise<Object>} - Diagnosis content
     */
    async getDifferentialDiagnosis() {
        return this.fetchRequest('/cds_ddx');
    },

    /**
     * Get suggested questions
     * @returns {Promise<Object>} - Questions content
     */
    async getSuggestedQuestions() {
        return this.fetchRequest('/cds_qa');
    },

    /**
     * Toggle patient mode
     * @param {boolean} enabled - Whether to enable patient mode
     * @returns {Promise<Object>} - Status
     */
    async setPatientMode(enabled) {
        return this.fetchRequest('/patient_mode', 'POST', { enabled });
    },

    /**
     * Set doctor's summary
     * @param {string} text - Summary text
     * @returns {Promise<Object>} - Status
     */
    async setDoctorSummary(text) {
        return this.fetchRequest('/set_summary', 'POST', { text });
    },

    /**
     * Save conversation
     * @param {string} transcript - Conversation transcript
     * @param {string} title - Conversation title
     * @param {string} audio - Base64 encoded audio (optional)
     * @returns {Promise<Object>} - Status and conversation ID
     */
    async saveConversation(transcript, title, audio = null) {
        return this.fetchRequest('/save_conversation', 'POST', {
            transcript,
            title,
            audio
        });
    },

    /**
     * Get list of previous conversations
     * @returns {Promise<Array>} - List of conversations
     */
    async getConversations() {
        return this.fetchRequest('/conversations');
    },

    /**
     * Get conversation by ID
     * @param {string} conversationId - Conversation ID
     * @returns {Promise<Object>} - Conversation data
     */
    async getConversation(conversationId) {
        return this.fetchRequest(`/conversation/${conversationId}`);
    }
};

// API connection status tracker
const apiConnectionMonitor = {
    connected: false,
    lastChecked: null,
    
    // Initialize the connection monitor
    init() {
        // Check connection immediately
        this.checkConnection();
        
        // Set up periodic checking
        setInterval(() => this.checkConnection(), 30000); // Check every 30 seconds
        
        // Handle window online/offline events
        window.addEventListener('online', () => this.checkConnection());
        window.addEventListener('offline', () => {
            this.connected = false;
            this.notifyStatusChange(false, 'Network connection lost');
        });
    },
    
    // Check API connection
    async checkConnection() {
        try {
            await apiService.checkStatus();
            this.lastChecked = new Date();
            
            // Only trigger event if status changed from disconnected to connected
            if (!this.connected) {
                this.connected = true;
                this.notifyStatusChange(true, 'Connected to MediCompanion API');
            }
        } catch (error) {
            // Only trigger event if status changed from connected to disconnected
            if (this.connected) {
                this.connected = false;
                this.notifyStatusChange(false, 'Lost connection to MediCompanion API');
            }
        }
    },
    
    // Notify application of connection status change
    notifyStatusChange(connected, message) {
        const event = new CustomEvent('apiConnectionChanged', {
            detail: { connected, message, timestamp: new Date() }
        });
        document.dispatchEvent(event);
        
        console.log(`API Connection: ${connected ? 'Connected' : 'Disconnected'} - ${message}`);
    }
};

// Initialize API connection monitor on page load
document.addEventListener('DOMContentLoaded', () => {
    // Short delay to let the page render first
    setTimeout(() => {
        apiConnectionMonitor.init();
    }, 500);
});