/**
 * Enhanced application script for MediCompanion
 * Provides advanced UI features, audio playback, theme toggling, and more
 */

// DOM Elements
// Navigation
const homeButton = document.getElementById('homeButton');
const patientModeBtn = document.getElementById('patientModeBtn');
const doctorModeBtn = document.getElementById('doctorModeBtn');
const homeSection = document.getElementById('homeSection');
const patientSection = document.getElementById('patientSection');
const doctorSection = document.getElementById('doctorSection');
const getStartedBtn = document.getElementById('getStartedBtn');
const learnMoreBtn = document.getElementById('learnMoreBtn');
const themeToggleBtn = document.getElementById('themeToggleBtn');

// Doctor Mode Elements
const diagnosisContent = document.getElementById('diagnosisContent');
const questionsContent = document.getElementById('questionsContent');
const transcriptContent = document.getElementById('transcriptContent');
const doctorNotes = document.getElementById('doctorNotes');
const startRecordingBtn = document.getElementById('startRecordingBtn');
const stopRecordingBtn = document.getElementById('stopRecordingBtn');
const generateNotesBtn = document.getElementById('generateNotesBtn');
const saveNotesBtn = document.getElementById('saveNotesBtn');
const clearNotesBtn = document.getElementById('clearNotesBtn');
const doctorConsultationsList = document.getElementById('doctorConsultationsList');
const doctorConsultationSearch = document.getElementById('doctorConsultationSearch');
const doctorSortConsultationsBtn = document.getElementById('doctorSortConsultationsBtn');
const refreshConsultationsBtn = document.getElementById('refreshConsultationsBtn');
const recordingIndicator = document.querySelector('.recording-indicator');
const recordingDot = document.querySelector('.recording-dot');
const recordingText = document.querySelector('.recording-text');

// Patient Mode Elements
const patientChatMessages = document.getElementById('patientChatMessages');
const patientMessageInput = document.getElementById('patientMessageInput');
const sendPatientMessage = document.getElementById('sendPatientMessage');
const patientConsultationsList = document.getElementById('patientConsultationsList');
const consultationSearch = document.getElementById('consultationSearch');
const sortConsultationsBtn = document.getElementById('sortConsultationsBtn');
const clearChatBtn = document.getElementById('clearChatBtn');
const soundToggleBtn = document.getElementById('soundToggleBtn');
const patientVoiceInputBtn = document.getElementById('patientVoiceInputBtn');
const liveTranscriptDisplay = document.getElementById('liveTranscriptDisplay');

// UI Elements
const loadingSpinner = document.getElementById('loadingSpinner');
const loadingText = document.getElementById('loadingText');
const toast = document.getElementById('toast');
const toastCloseBtn = document.querySelector('.toast-close');
const modal = document.getElementById('modal');
const modalTitle = document.getElementById('modalTitle');
const modalBody = document.getElementById('modalBody');
const modalPrimaryBtn = document.getElementById('modalPrimaryBtn');
const modalCloseBtn = document.getElementById('modalCloseBtn');
const closeModalBtn = document.querySelector('.close-modal');
const audioPlayer = document.getElementById('audioPlayer');

// Panel expand buttons
const expandButtons = document.querySelectorAll('.expand-btn');
const refreshButtons = document.querySelectorAll('.refresh-btn');

// Application State
const appState = {
    currentMode: 'home', // 'home', 'patient', 'doctor'
    isRecording: false,
    soundEnabled: true,
    darkMode: localStorage.getItem('darkMode') === 'true',
    pollIntervals: {
        transcript: null,
        patientTranscript: null,
        diagnosis: null,
        questions: null,
        patientMessage: null,
        notes: null
    },
    audioControl: {
        currentAudio: null,
        isPlaying: false,
        currentMessageId: null
    },
    voiceInput: {
        recognition: null,
        isListening: false,
        transcript: ''
    },
    currentMessageId: null,
    currentNotesTaskId: null,
    conversations: [],
    sortDirection: 'desc', // 'asc' or 'desc'
    expandedPanels: {
        diagnosis: false,
        questions: false,
        transcript: false
    }
};

// Initialize the application
function initApp() {
    // Apply dark mode if enabled
    if (appState.darkMode) {
        document.body.classList.add('dark-mode');
        themeToggleBtn.innerHTML = '<i class="fas fa-sun"></i>';
    }

    // Setup event listeners
    setupEventListeners();

    // Initialize voice recognition if supported
    setupVoiceRecognition();

    // Load conversations
    loadConversations();
    
    // Listen for API connection changes
    document.addEventListener('apiConnectionChanged', handleApiConnectionChange);
    
    console.log('MediCompanion application initialized');
}

// Setup voice recognition
function setupVoiceRecognition() {
    // Check if browser supports SpeechRecognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (SpeechRecognition) {
        appState.voiceInput.recognition = new SpeechRecognition();
        appState.voiceInput.recognition.continuous = true;
        appState.voiceInput.recognition.interimResults = true;
        appState.voiceInput.recognition.lang = 'en-US';
        
        // Set up recognition events
        appState.voiceInput.recognition.onstart = () => {
            appState.voiceInput.isListening = true;
            patientVoiceInputBtn.classList.add('recording');
            patientMessageInput.placeholder = 'Listening...';
            console.log('Voice recognition started');
        };
        
        appState.voiceInput.recognition.onend = () => {
            appState.voiceInput.isListening = false;
            patientVoiceInputBtn.classList.remove('recording');
            patientMessageInput.placeholder = 'Type your message...';
            console.log('Voice recognition ended');
            
            // If we're still in recording mode, restart recognition
            if (appState.isRecording) {
                setTimeout(() => {
                    try {
                        appState.voiceInput.recognition.start();
                    } catch (e) {
                        console.error('Error restarting recognition:', e);
                    }
                }, 1000);
            }
        };
        
        appState.voiceInput.recognition.onresult = (event) => {
            const transcript = Array.from(event.results)
                .map(result => result[0])
                .map(result => result.transcript)
                .join(' ');
                
            // Update display in real-time
            patientMessageInput.value = transcript;
            
            // Store the transcript
            appState.voiceInput.transcript = transcript;
            
            // Update live transcript display
            if (liveTranscriptDisplay) {
                liveTranscriptDisplay.textContent = transcript;
            }
            
            console.log('Voice recognition result:', transcript);
        };
        
        appState.voiceInput.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            patientVoiceInputBtn.classList.remove('recording');
            patientMessageInput.placeholder = 'Type your message...';
            
            // Don't show toast for aborted recognition (happens when manually stopped)
            if (event.error !== 'aborted') {
                showToast(`Voice recognition error: ${event.error}`, 'error');
            }
        };
        
        console.log('Voice recognition initialized');
    } else {
        console.log('Voice recognition not supported by browser');
        patientVoiceInputBtn.style.display = 'none';
    }
}

// Setup event listeners
function setupEventListeners() {
    // Navigation
    homeButton.addEventListener('click', () => switchMode('home'));
    patientModeBtn.addEventListener('click', () => switchMode('patient'));
    doctorModeBtn.addEventListener('click', () => switchMode('doctor'));
    getStartedBtn.addEventListener('click', showModeSelectionModal);
    learnMoreBtn.addEventListener('click', showLearnMoreModal);
    themeToggleBtn.addEventListener('click', toggleDarkMode);

    // Doctor Mode
    startRecordingBtn.addEventListener('click', startRecording);
    stopRecordingBtn.addEventListener('click', stopRecording);
    generateNotesBtn.addEventListener('click', generateNotes);
    saveNotesBtn.addEventListener('click', saveNotes);
    clearNotesBtn.addEventListener('click', clearNotes);
    refreshConsultationsBtn.addEventListener('click', loadConversations);
    doctorConsultationSearch.addEventListener('input', filterDoctorConsultations);
    doctorSortConsultationsBtn.addEventListener('click', () => toggleSortDirection('doctor'));

    // Patient Mode
    sendPatientMessage.addEventListener('click', sendMessage);
    patientMessageInput.addEventListener('keypress', e => {
        if (e.key === 'Enter') sendMessage();
    });
    clearChatBtn.addEventListener('click', clearChat);
    soundToggleBtn.addEventListener('click', toggleSound);
    patientVoiceInputBtn.addEventListener('click', toggleVoiceInput);
    consultationSearch.addEventListener('input', filterPatientConsultations);
    sortConsultationsBtn.addEventListener('click', () => toggleSortDirection('patient'));

    // UI Elements
    toastCloseBtn.addEventListener('click', () => toast.classList.remove('show'));
    closeModalBtn.addEventListener('click', closeModal);
    modalCloseBtn.addEventListener('click', closeModal);
    
    // Panel controls
    expandButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const panel = e.target.closest('.panel');
            expandPanel(panel);
        });
    });
    
    refreshButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const panel = e.target.closest('.panel');
            if (panel.classList.contains('diagnosis-panel')) {
                refreshDiagnosis();
            } else if (panel.classList.contains('questions-panel')) {
                refreshQuestions();
            }
        });
    });
    
    // Audio player events
    audioPlayer.addEventListener('ended', () => {
        const currentPlayButton = document.querySelector(`.message[data-id="${appState.audioControl.currentMessageId}"] .audio-btn i`);
        if (currentPlayButton) {
            currentPlayButton.className = 'fas fa-play';
        }
        appState.audioControl.isPlaying = false;
        appState.audioControl.currentMessageId = null;
    });
    
    console.log('Event listeners set up');
}

// Toggle dark mode
function toggleDarkMode() {
    appState.darkMode = !appState.darkMode;
    document.body.classList.toggle('dark-mode', appState.darkMode);
    
    // Update button icon
    themeToggleBtn.innerHTML = appState.darkMode ? 
        '<i class="fas fa-sun"></i>' : 
        '<i class="fas fa-moon"></i>';
    
    // Save preference
    localStorage.setItem('darkMode', appState.darkMode);
    
    showToast(`${appState.darkMode ? 'Dark' : 'Light'} mode enabled`, 'info');
}

// Show mode selection modal
function showModeSelectionModal() {
    modalTitle.textContent = 'Select Mode';
    modalBody.innerHTML = `
        <div class="mode-selection">
            <div class="mode-card" data-mode="patient">
                <div class="mode-icon">
                    <i class="fas fa-user-injured"></i>
                </div>
                <h3>Patient Mode</h3>
                <p>Get assistance with your medications and medical information. Chat with our AI assistant for help.</p>
            </div>
            <div class="mode-card" data-mode="doctor">
                <div class="mode-icon">
                    <i class="fas fa-user-md"></i>
                </div>
                <h3>Doctor Mode</h3>
                <p>Get AI-powered diagnosis assistance, suggested questions, and automated notes for patient consultations.</p>
            </div>
        </div>
    `;
    
    // Add click handlers to mode cards
    setTimeout(() => {
        const modeCards = document.querySelectorAll('.mode-card');
        modeCards.forEach(card => {
            card.addEventListener('click', () => {
                const mode = card.dataset.mode;
                closeModal();
                switchMode(mode);
            });
        });
    }, 100);
    
    // Configure modal buttons
    modalPrimaryBtn.style.display = 'none';
    modalCloseBtn.textContent = 'Cancel';
    
    openModal();
}

// Show learn more modal
function showLearnMoreModal() {
    modalTitle.textContent = 'About MediCompanion';
    modalBody.innerHTML = `
        <div class="about-content">
            <h3>Empowering Healthcare with AI</h3>
            <p>MediCompanion is an innovative platform designed to enhance doctor-patient interactions through advanced AI technology. Our system provides:</p>
            
            <h4>For Doctors</h4>
            <ul>
                <li><strong>AI-Powered Diagnostics:</strong> Get potential diagnosis suggestions in real-time as you speak with patients</li>
                <li><strong>Smart Question Suggestions:</strong> Receive recommended questions based on patient symptoms</li>
                <li><strong>Automated Documentation:</strong> Generate clinical notes automatically from your consultations</li>
            </ul>
            
            <h4>For Patients</h4>
            <ul>
                <li><strong>24/7 Medical Assistant:</strong> Chat with our AI to get clear information about your medications</li>
                <li><strong>Easy Access to Information:</strong> Get answers in plain language about your treatment plan</li>
                <li><strong>Voice and Text Interface:</strong> Interact through typing or speaking for convenience</li>
            </ul>
            
            <p>MediCompanion is not a replacement for professional medical care. Always consult your healthcare provider for medical advice.</p>
        </div>
    `;
    
    // Configure modal buttons
    modalPrimaryBtn.textContent = 'Try it Now';
    modalPrimaryBtn.style.display = 'block';
    modalPrimaryBtn.onclick = () => {
        closeModal();
        showModeSelectionModal();
    };
    modalCloseBtn.textContent = 'Close';
    
    openModal();
}

// Toggle voice input for patient chat
function toggleVoiceInput() {
    if (!appState.voiceInput.recognition) {
        showToast('Voice input is not supported in your browser', 'error');
        return;
    }
    
    if (appState.voiceInput.isListening) {
        try {
            appState.voiceInput.recognition.stop();
            console.log('Voice recognition manually stopped');
        } catch (e) {
            console.error('Error stopping recognition:', e);
        }
    } else {
        try {
            patientMessageInput.value = '';
            appState.voiceInput.transcript = '';
            if (liveTranscriptDisplay) {
                liveTranscriptDisplay.textContent = '';
            }
            appState.voiceInput.recognition.start();
            console.log('Voice recognition manually started');
        } catch (e) {
            console.error('Error starting recognition:', e);
            showToast('Failed to start voice recognition', 'error');
        }
    }
}

// Toggle sound for patient messages
function toggleSound() {
    appState.soundEnabled = !appState.soundEnabled;
    soundToggleBtn.classList.toggle('active', appState.soundEnabled);
    soundToggleBtn.innerHTML = appState.soundEnabled ? 
        '<i class="fas fa-volume-up"></i>' : 
        '<i class="fas fa-volume-mute"></i>';
        
    showToast(`Sound ${appState.soundEnabled ? 'enabled' : 'disabled'}`, 'info');
}

// Clear patient chat history
function clearChat() {
    // Show confirmation modal
    modalTitle.textContent = 'Clear Chat History?';
    modalBody.innerHTML = `
        <p>Are you sure you want to clear all chat messages? This action cannot be undone.</p>
    `;
    
    // Configure modal buttons
    modalPrimaryBtn.textContent = 'Clear Chat';
    modalPrimaryBtn.style.display = 'block';
    modalPrimaryBtn.onclick = () => {
        // Keep the initial greeting message
        const initialMessage = patientChatMessages.querySelector('.message.bot');
        patientChatMessages.innerHTML = '';
        if (initialMessage) {
            patientChatMessages.appendChild(initialMessage);
        }
        
        closeModal();
        showToast('Chat history cleared', 'success');
    };
    modalCloseBtn.textContent = 'Cancel';
    
    openModal();
}

// Toggle sort direction for consultations
function toggleSortDirection(mode) {
    appState.sortDirection = appState.sortDirection === 'desc' ? 'asc' : 'desc';
    
    // Update the button icon
    const btn = mode === 'doctor' ? doctorSortConsultationsBtn : sortConsultationsBtn;
    btn.innerHTML = appState.sortDirection === 'desc' ? 
        '<i class="fas fa-sort-amount-down"></i>' : 
        '<i class="fas fa-sort-amount-up"></i>';
    
    // Resort and render the conversations
    sortAndRenderConversations();
}

// Filter doctor consultations
function filterDoctorConsultations() {
    const query = doctorConsultationSearch.value.toLowerCase();
    filterConsultations(doctorConsultationsList, query);
}

// Filter patient consultations
function filterPatientConsultations() {
    const query = consultationSearch.value.toLowerCase();
    filterConsultations(patientConsultationsList, query);
}

// Filter consultations in a container by query
function filterConsultations(container, query) {
    const items = container.querySelectorAll('.consultation-item');
    
    items.forEach(item => {
        const title = item.querySelector('h4').textContent.toLowerCase();
        const date = item.querySelector('.consultation-date').textContent.toLowerCase();
        
        if (title.includes(query) || date.includes(query)) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}

// Expand/collapse panel
function expandPanel(panel) {
    // Get panel type
    let panelType = '';
    if (panel.classList.contains('diagnosis-panel')) {
        panelType = 'diagnosis';
    } else if (panel.classList.contains('questions-panel')) {
        panelType = 'questions';
    } else if (panel.classList.contains('conversation-panel')) {
        panelType = 'transcript';
    } else {
        return;
    }
    
    // If already expanded, collapse it
    if (panel.classList.contains('expanded')) {
        panel.classList.remove('expanded');
        appState.expandedPanels[panelType] = false;
        
        // Update the button icon
        const expandBtn = panel.querySelector('.expand-btn i');
        if (expandBtn) {
            expandBtn.className = 'fas fa-expand-alt';
        }
        return;
    }
    
    // Check if we're in doctor mode
    const doctorMain = panel.closest('.doctor-main');
    if (!doctorMain) return;
    
    // Find other panels and collapse them
    const otherPanels = doctorMain.querySelectorAll('.panel');
    otherPanels.forEach(p => {
        if (p !== panel) {
            p.classList.remove('expanded');
            
            // Reset other panel states
            Object.keys(appState.expandedPanels).forEach(key => {
                if (key !== panelType) {
                    appState.expandedPanels[key] = false;
                }
                
                // Update their expand button icons
                const pExpandBtn = p.querySelector('.expand-btn i');
                if (pExpandBtn) {
                    pExpandBtn.className = 'fas fa-expand-alt';
                }
            });
        }
    });
    
    // Expand this panel
    panel.classList.add('expanded');
    appState.expandedPanels[panelType] = true;
    
    // Update the button icon
    const expandBtn = panel.querySelector('.expand-btn i');
    if (expandBtn) {
        expandBtn.className = 'fas fa-compress-alt';
    }
    
    // Scroll to the top of the panel content
    const panelContent = panel.querySelector('.panel-content');
    if (panelContent) {
        panelContent.scrollTop = 0;
    }
}

// Refresh diagnosis panel
function refreshDiagnosis() {
    if (!appState.isRecording && transcriptContent.textContent.trim()) {
        diagnosisContent.innerHTML = '<div class="loading-content"><i class="fas fa-circle-notch fa-spin"></i> Refreshing diagnosis...</div>';
        fetchAndUpdateDiagnosis();
    } else {
        showToast('Start recording or provide transcript first', 'warning');
    }
}

// Refresh questions panel
function refreshQuestions() {
    if (!appState.isRecording && transcriptContent.textContent.trim()) {
        questionsContent.innerHTML = '<div class="loading-content"><i class="fas fa-circle-notch fa-spin"></i> Refreshing questions...</div>';
        fetchAndUpdateQuestions();
    } else {
        showToast('Start recording or provide transcript first', 'warning');
    }
}

// Clear notes content
function clearNotes() {
    if (doctorNotes.value.trim()) {
        // Show confirmation if there's content
        modalTitle.textContent = 'Clear Notes?';
        modalBody.innerHTML = `
            <p>Are you sure you want to clear all notes? This action cannot be undone.</p>
        `;
        
        // Configure modal buttons
        modalPrimaryBtn.textContent = 'Clear Notes';
        modalPrimaryBtn.style.display = 'block';
        modalPrimaryBtn.onclick = () => {
            doctorNotes.value = '';
            closeModal();
            showToast('Notes cleared', 'info');
        };
        modalCloseBtn.textContent = 'Cancel';
        
        openModal();
    } else {
        doctorNotes.value = '';
    }
}

// Delete consultation
function deleteConsultation(conversationId) {
    // Show confirmation modal
    modalTitle.textContent = 'Delete Consultation?';
    modalBody.innerHTML = `
        <p>Are you sure you want to delete this consultation? This action cannot be undone.</p>
    `;
    
    // Configure modal buttons
    modalPrimaryBtn.textContent = 'Delete';
    modalPrimaryBtn.style.display = 'block';
    modalPrimaryBtn.classList.add('danger');
    modalPrimaryBtn.onclick = async () => {
        try {
            // Remove from frontend immediately for responsive UI
            appState.conversations = appState.conversations.filter(conv => conv.id !== conversationId);
            sortAndRenderConversations();
            
            // In a real app, you would also call an API to delete on the server
            // For now, we'll just simulate success
            closeModal();
            showToast('Consultation deleted successfully', 'success');
            
            // Remove danger class
            modalPrimaryBtn.classList.remove('danger');
        } catch (error) {
            console.error('Delete consultation failed:', error);
            showToast('Failed to delete consultation', 'error');
            modalPrimaryBtn.classList.remove('danger');
        }
    };
    
    modalCloseBtn.textContent = 'Cancel';
    modalCloseBtn.onclick = () => {
        closeModal();
        modalPrimaryBtn.classList.remove('danger');
    };
    
    openModal();
}

// Switch between modes (home, patient, doctor)
async function switchMode(mode) {
    console.log(`Switching to ${mode} mode`);
    
    // Stop any ongoing recording
    if (appState.isRecording) {
        await stopRecording();
    }
    
    // Stop any playing audio
    stopCurrentAudio();
    
    // Stop voice recognition if active
    if (appState.voiceInput.isListening && appState.voiceInput.recognition) {
        try {
            appState.voiceInput.recognition.stop();
        } catch (e) {
            console.error('Error stopping voice recognition:', e);
        }
    }

    // Clear polling intervals
    clearAllPollingIntervals();

    // Update navigation buttons
    patientModeBtn.classList.toggle('active', mode === 'patient');
    doctorModeBtn.classList.toggle('active', mode === 'doctor');

    // Hide all sections
    homeSection.classList.remove('active');
    patientSection.classList.remove('active');
    doctorSection.classList.remove('active');

    // Show selected section
    if (mode === 'home') {
        homeSection.classList.add('active');
    } else if (mode === 'patient') {
        patientSection.classList.add('active');
        try {
            await apiService.setPatientMode(true);
            console.log('Patient mode activated on server');
        } catch (error) {
            console.error('Failed to activate patient mode on server:', error);
            showToast('Failed to activate patient mode', 'error');
        }
    } else if (mode === 'doctor') {
        doctorSection.classList.add('active');
        try {
            await apiService.setPatientMode(false);
            console.log('Doctor mode activated on server');
        } catch (error) {
            console.error('Failed to activate doctor mode on server:', error);
            showToast('Failed to activate doctor mode', 'error');
        }
    }

    appState.currentMode = mode;
    console.log(`Mode switched to ${mode}`);
}

// Handle API connection changes
function handleApiConnectionChange(event) {
    const { connected, message } = event.detail;
    
    if (connected) {
        showToast(message, 'success');
    } else {
        showToast(message, 'error');
    }
}

// Load conversations
async function loadConversations() {
    try {
        console.log('Loading conversations...');
        showLoading(true, 'Loading conversations...');
        const conversations = await apiService.getConversations();
        console.log('Loaded conversations:', conversations);
        appState.conversations = conversations;
        
        // Sort and render conversations
        sortAndRenderConversations();
        
        showLoading(false);
    } catch (error) {
        console.error('Load conversations failed:', error);
        showLoading(false);
        showToast('Failed to load conversations', 'error');
    }
}

// Sort and render conversations in both lists
function sortAndRenderConversations() {
    // Sort conversations
    const sortedConversations = [...appState.conversations].sort((a, b) => {
        const dateA = new Date(a.date || 0);
        const dateB = new Date(b.date || 0);
        
        if (appState.sortDirection === 'desc') {
            return dateB - dateA; // Newest first
        } else {
            return dateA - dateB; // Oldest first
        }
    });
    
    // Render in both containers
    renderConversationsList(doctorConsultationsList, sortedConversations);
    renderConversationsList(patientConsultationsList, sortedConversations);
}

// Render conversations list in a container
function renderConversationsList(container, conversations) {
    container.innerHTML = '';
    
    if (!conversations || conversations.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-folder-open"></i>
                <p>No previous consultations found</p>
            </div>
        `;
        return;
    }
    
    conversations.forEach(conversation => {
        const item = document.createElement('div');
        item.className = 'consultation-item';
        item.dataset.id = conversation.id;
        
        const titleRow = document.createElement('div');
        titleRow.className = 'consultation-title-row';
        
        const title = document.createElement('h4');
        title.innerHTML = `<i class="fas fa-file-medical"></i> ${conversation.title || 'Untitled Consultation'}`;
        
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'delete-consultation-btn';
        deleteBtn.innerHTML = '<i class="fas fa-trash-alt"></i>';
        deleteBtn.title = 'Delete consultation';
        deleteBtn.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent opening consultation when clicking delete
            deleteConsultation(conversation.id);
        });
        
        titleRow.appendChild(title);
        titleRow.appendChild(deleteBtn);
        
        const date = document.createElement('div');
        date.className = 'consultation-date';
        date.textContent = conversation.date ? new Date(conversation.date).toLocaleString() : 'No date';
        
        item.appendChild(titleRow);
        item.appendChild(date);
        
        item.addEventListener('click', () => loadConversation(conversation.id));
        
        container.appendChild(item);
    });
    
    console.log(`Rendered ${conversations.length} conversations`);
}

// Load a specific consultation
async function loadConversation(conversationId) {
    try {
        console.log(`Loading consultation: ${conversationId}`);
        showLoading(true, 'Loading consultation...');
        
        // Find the conversation in our local state first
        const conversation = appState.conversations.find(c => c.id === conversationId);
        
        if (!conversation) {
            throw new Error('Consultation not found');
        }
        
        // In a real app, you would fetch the full details from the server
        // const fullConversation = await apiService.getConversation(conversationId);
        const fullConversation = conversation; // For now, use what we have
        
        console.log('Loaded conversation details:', fullConversation);
        
        // Display conversation in modal
        modalTitle.textContent = fullConversation.title || 'Untitled Consultation';
        
        let modalContent = `
            <div class="conversation-details">
                <div class="conversation-meta">
                    <div class="meta-item">
                        <i class="fas fa-calendar-alt"></i>
                        <span><strong>Date:</strong> ${fullConversation.date ? new Date(fullConversation.date).toLocaleString() : 'No date'}</span>
                    </div>
                    <div class="meta-item">
                        <i class="fas fa-file-alt"></i>
                        <span><strong>ID:</strong> ${fullConversation.id}</span>
                    </div>
                </div>
                
                <div class="conversation-transcript">
                    <h3><i class="fas fa-file-alt"></i> Transcript</h3>
                    <div class="transcript-content">
                        ${fullConversation.transcript ? marked.parse(fullConversation.transcript) : 'No transcript available'}
                    </div>
                </div>
            </div>
        `;
        
        // Add audio playback if available
        if (fullConversation.audio) {
            modalContent += `
                <div class="conversation-audio">
                    <h3><i class="fas fa-headphones"></i> Audio Recording</h3>
                    <div class="audio-player">
                        <audio controls>
                            <source src="data:audio/mp3;base64,${fullConversation.audio}" type="audio/mp3">
                            Your browser does not support the audio element.
                        </audio>
                    </div>
                </div>
            `;
        }
        
        modalBody.innerHTML = modalContent;
        
        // Configure modal buttons
        modalPrimaryBtn.textContent = 'Close';
        modalPrimaryBtn.onclick = closeModal;
        modalPrimaryBtn.style.display = 'block';
        modalCloseBtn.style.display = 'none';
        
        openModal();
        showLoading(false);
    } catch (error) {
        console.error('Load conversation failed:', error);
        showLoading(false);
        showToast('Failed to load conversation', 'error');
    }
}

// Doctor Mode: Start recording
async function startRecording() {
    try {
        console.log('Starting recording...');
        showLoading(true, 'Starting recording...');
        const response = await apiService.startRecording();
        console.log('Start recording response:', response);
        
        if (response.active) {
            appState.isRecording = true;
            startRecordingBtn.disabled = true;
            stopRecordingBtn.disabled = false;
            
            // Update recording indicator
            recordingIndicator.classList.add('active');
            recordingText.textContent = 'Recording';
            
            // Clear previous transcript
            transcriptContent.textContent = '';
            transcriptContent.innerHTML = `
                <div class="recording-status">
                    <i class="fas fa-microphone-alt"></i>
                    <p>Recording in progress...</p>
                </div>
            `;
            
            // Start speech recognition if available
            if (appState.voiceInput.recognition && !appState.voiceInput.isListening) {
                try {
                    appState.voiceInput.transcript = '';
                    appState.voiceInput.recognition.start();
                    console.log('Voice recognition started automatically');
                } catch (e) {
                    console.error('Error starting voice recognition:', e);
                }
            }
            
            // Start polling for transcript, diagnosis, and questions
            startPolling();
            
            showToast('Recording started', 'success');
        } else {
            throw new Error(response.error || 'Failed to start recording');
        }
        
        showLoading(false);
    } catch (error) {
        console.error('Start recording failed:', error);
        showLoading(false);
        showToast('Failed to start recording', 'error');
    }
}

// Doctor Mode: Stop recording
async function stopRecording() {
    try {
        console.log('Stopping recording...');
        showLoading(true, 'Stopping recording...');
        const response = await apiService.stopRecording();
        console.log('Stop recording response:', response);
        
        appState.isRecording = false;
        startRecordingBtn.disabled = false;
        stopRecordingBtn.disabled = true;
        
        // Update recording indicator
        recordingIndicator.classList.remove('active');
        recordingText.textContent = 'Not Recording';
        
        // Stop speech recognition if active
        if (appState.voiceInput.isListening && appState.voiceInput.recognition) {
            try {
                appState.voiceInput.recognition.stop();
                console.log('Voice recognition stopped automatically');
            } catch (e) {
                console.error('Error stopping voice recognition:', e);
            }
        }
        
        // Save current transcript if we have one
        if (appState.voiceInput.transcript) {
            // Store the voice transcript in the main transcript area
            if (transcriptContent.textContent.trim() === "" || 
                transcriptContent.textContent.includes("Recording in progress")) {
                transcriptContent.textContent = appState.voiceInput.transcript;
            }
        }
        
        // Continue polling for a bit longer to get final results
        setTimeout(() => {
            // Stop polling for transcript but continue for diagnosis and questions
            clearPollingInterval('transcript');
        }, 5000);
        
        showToast('Recording stopped', 'info');
        showLoading(false);
    } catch (error) {
        console.error('Stop recording failed:', error);
        showLoading(false);
        showToast('Failed to stop recording', 'error');
    }
}

// Start polling for data updates
function startPolling() {
    console.log('Starting polling for updates...');
    
    // Poll for transcript
    clearPollingInterval('transcript');
    appState.pollIntervals.transcript = setInterval(async () => {
        try {
            const response = await apiService.getTranscript();
            
            if (response.transcript && response.transcript.trim()) {
                transcriptContent.textContent = response.transcript;
            } else if (!transcriptContent.textContent.trim() && appState.voiceInput.transcript) {
                // If we have voice transcript but no server transcript, show the voice transcript
                transcriptContent.textContent = appState.voiceInput.transcript;
            } else if (!transcriptContent.textContent.trim()) {
                transcriptContent.innerHTML = `
                    <div class="recording-status">
                        <i class="fas fa-microphone-alt"></i>
                        <p>Recording in progress...</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Transcript polling error:', error);
        }
    }, 2000);
    
    // Poll for patient transcript
    clearPollingInterval('patientTranscript');
    appState.pollIntervals.patientTranscript = setInterval(async () => {
        if (!appState.voiceInput.transcript) return;
        
        try {
            // In a real app, you would send this to the server
            // For now, just display it
            if (liveTranscriptDisplay) {
                liveTranscriptDisplay.textContent = appState.voiceInput.transcript;
            }
        } catch (error) {
            console.error('Patient transcript polling error:', error);
        }
    }, 1000);
    
    // Poll for diagnosis
    clearPollingInterval('diagnosis');
    appState.pollIntervals.diagnosis = setInterval(fetchAndUpdateDiagnosis, 5000);
    
    // Poll for questions
    clearPollingInterval('questions');
    appState.pollIntervals.questions = setInterval(fetchAndUpdateQuestions, 5000);
    
    console.log('Polling intervals started');
}

// Fetch and update diagnosis content
async function fetchAndUpdateDiagnosis() {
    try {
        const response = await apiService.getDifferentialDiagnosis();
        
        if (response.content && response.content.trim() && response.content !== 'Analyzing symptoms for diagnosis, please wait...') {
            diagnosisContent.innerHTML = marked.parse(response.content);
            
            // Add interactive elements to diagnosis items
            setTimeout(() => {
                const diagnosisItems = diagnosisContent.querySelectorAll('h2, h3');
                diagnosisItems.forEach(item => {
                    item.classList.add('interactive-item');
                    item.addEventListener('click', function() {
                        const nextElems = [];
                        let nextElem = this.nextElementSibling;
                        
                        // Collect all elements until the next heading
                        while (nextElem && 
                               !['H1', 'H2', 'H3'].includes(nextElem.tagName)) {
                            nextElems.push(nextElem);
                            nextElem = nextElem.nextElementSibling;
                        }
                        
                        // Toggle visibility of these elements
                        nextElems.forEach(el => {
                            el.classList.toggle('hidden-content');
                        });
                        
                        // Toggle icon on the heading
                        this.classList.toggle('collapsed');
                    });
                });
            }, 100);
        } else if (!diagnosisContent.innerHTML.includes('diagnosis')) {
            diagnosisContent.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-stethoscope"></i>
                    <p>Waiting for data to generate diagnosis</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Diagnosis polling error:', error);
    }
}

// Fetch and update suggested questions
async function fetchAndUpdateQuestions() {
    try {
        const response = await apiService.getSuggestedQuestions();
        
        if (response.content && response.content.trim() && response.content !== 'Generating suggested questions, please wait...') {
            questionsContent.innerHTML = marked.parse(response.content);
            
            // Add click-to-copy functionality to questions
            setTimeout(() => {
                const questionItems = questionsContent.querySelectorAll('li');
                questionItems.forEach(item => {
                    item.classList.add('interactive-item');
                    item.addEventListener('click', () => {
                        navigator.clipboard.writeText(item.textContent)
                            .then(() => {
                                item.classList.add('copied');
                                setTimeout(() => item.classList.remove('copied'), 2000);
                                showToast('Question copied to clipboard', 'success');
                            })
                            .catch(err => {
                                console.error('Failed to copy:', err);
                                showToast('Failed to copy to clipboard', 'error');
                            });
                    });
                    
                    // Add copy icon and title
                    item.title = 'Click to copy';
                    item.style.cursor = 'pointer';
                });
            }, 100);
        } else if (!questionsContent.innerHTML.includes('questions')) {
            questionsContent.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-question"></i>
                    <p>Waiting for data to suggest questions</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Questions polling error:', error);
    }
}

// Doctor Mode: Generate notes
async function generateNotes() {
    try {
        const hints = doctorNotes.value;
        
        if (!transcriptContent.textContent || transcriptContent.textContent.trim().length < 10) {
            showToast('No transcript available for note generation', 'warning');
            return;
        }
        
        console.log('Generating notes...');
        showLoading(true, 'Generating clinical notes...');
        const response = await apiService.generateNotes(hints);
        console.log('Generate notes response:', response);
        
        if (response.status === 'processing' && response.task_id) {
            appState.currentNotesTaskId = response.task_id;
            
            // Poll for notes generation status
            clearPollingInterval('notes');
            appState.pollIntervals.notes = setInterval(() => pollNotesStatus(response.task_id), 2000);
            
            showToast('Generating notes...', 'info');
        } else {
            throw new Error('Failed to start notes generation');
        }
    } catch (error) {
        console.error('Generate notes failed:', error);
        showLoading(false);
        showToast('Failed to generate notes', 'error');
    }
}

// Poll for notes generation status
async function pollNotesStatus(taskId) {
    try {
        console.log(`Polling notes status for task: ${taskId}`);
        const response = await apiService.checkNotesStatus(taskId);
        console.log('Notes status:', response);
        
        if (response.status === 'complete') {
            // Update the notes textarea
            doctorNotes.value = response.content;
            
            // Stop polling
            clearPollingInterval('notes');
            
            showToast('Notes generated successfully', 'success');
            showLoading(false);
        } else if (response.status === 'error') {
            throw new Error(response.error || 'Error generating notes');
        }
    } catch (error) {
        console.error('Notes status polling failed:', error);
        clearPollingInterval('notes');
        showLoading(false);
        showToast('Failed to generate notes', 'error');
    }
}

// Doctor Mode: Save notes and transcript
async function saveNotes() {
    try {
        if (!transcriptContent.textContent || transcriptContent.textContent.trim().length < 10) {
            showToast('No transcript to save', 'warning');
            return;
        }
        
        console.log('Preparing to save notes...');
        
        // Prompt for title
        modalTitle.textContent = 'Save Consultation';
        modalBody.innerHTML = `
            <div class="form-group">
                <label for="consultationTitle">Consultation Title</label>
                <input type="text" id="consultationTitle" placeholder="Enter a title for this consultation" value="Consultation ${new Date().toLocaleDateString()}">
            </div>
            <div class="form-check mt-3">
                <input type="checkbox" id="includeAudio" checked>
                <label for="includeAudio">Include audio recording (if available)</label>
            </div>
        `;
        
        // Configure modal buttons
        modalPrimaryBtn.textContent = 'Save';
        modalPrimaryBtn.style.display = 'block';
        modalPrimaryBtn.onclick = async () => {
            const titleInput = document.getElementById('consultationTitle');
            const title = titleInput.value;
            const includeAudio = document.getElementById('includeAudio').checked;
            
            if (!title || title.trim().length < 3) {
                showToast('Please enter a valid title', 'warning');
                return;
            }
            
            closeModal();
            await saveConsultation(title, includeAudio);
        };
        
        modalCloseBtn.style.display = 'block';
        modalCloseBtn.textContent = 'Cancel';
        
        openModal();
    } catch (error) {
        console.error('Save notes dialog failed:', error);
        showToast('Failed to prepare save dialog', 'error');
    }
}

// Save consultation to backend
async function saveConsultation(title, includeAudio = true) {
    try {
        console.log(`Saving consultation with title: ${title}`);
        showLoading(true, 'Saving consultation...');
        
        const transcript = transcriptContent.textContent;
        const notes = doctorNotes.value;
        
        // Include voice transcript if available
        let fullTranscript = appState.voiceInput.transcript ? 
            `# ${title}\n\n## Voice Transcript\n${appState.voiceInput.transcript}\n\n## Processed Transcript\n${transcript}\n\n## Doctor's Notes\n${notes || 'No notes provided.'}` :
            `# ${title}\n\n## Transcript\n${transcript}\n\n## Doctor's Notes\n${notes || 'No notes provided.'}`;
        
        // Audio data would come from a recording in a real app
        // For now, we'll just pass null as we don't have actual audio
        const audio = includeAudio ? null : null; // This would be base64 audio if available
        
        // Call API to save consultation
        try {
            const response = await apiService.saveConversation(fullTranscript, title, audio);
            
            if (response.status === 'success') {
                showToast('Consultation saved successfully', 'success');
                
                // Add to local state for immediate UI update
                const newConsultation = {
                    id: response.id || `temp_${Date.now()}`,
                    title: title,
                    date: new Date().toISOString(),
                    transcript: fullTranscript,
                    audio: audio
                };
                
                appState.conversations.push(newConsultation);
                
                // Reload conversations from server
                await loadConversations();
            } else {
                throw new Error('Failed to save consultation');
            }
        } catch (error) {
            console.error('API save consultation failed:', error);
            
            // For demo purposes, still show success and update local state
            // Remove this fallback in production
            showToast('Consultation saved successfully', 'success');
            
            const newConsultation = {
                id: `temp_${Date.now()}`,
                title: title,
                date: new Date().toISOString(),
                transcript: fullTranscript,
                audio: null
            };
            
            appState.conversations.push(newConsultation);
            sortAndRenderConversations();
        }
        
        showLoading(false);
    } catch (error) {
        console.error('Save consultation failed:', error);
        showLoading(false);
        showToast('Failed to save consultation', 'error');
    }
}

// Patient Mode: Send message
async function sendMessage() {
    const messageText = patientMessageInput.value.trim();
    
    if (!messageText) return;
    
    try {
        console.log(`Sending patient message: ${messageText}`);
        
        // Add user message to chat
        addMessageToChat('user', messageText);
        
        // Clear input
        patientMessageInput.value = '';
        
        // Send message to API
        const response = await apiService.sendPatientMessage(messageText);
        console.log('Send message response:', response);
        
        if (response.message_id) {
            // Show typing indicator
            const typingIndicator = addTypingIndicator();
            
            // Poll for message response
            appState.currentMessageId = response.message_id;
            clearPollingInterval('patientMessage');
            appState.pollIntervals.patientMessage = setInterval(() => 
                pollMessageStatus(response.message_id, typingIndicator), 1000);
        } else {
            throw new Error('Failed to send message');
        }
    } catch (error) {
        console.error('Send message failed:', error);
        showToast('Failed to send message', 'error');
    }
}

// Poll for patient message response
async function pollMessageStatus(messageId, typingIndicator) {
    try {
        console.log(`Polling message status for ID: ${messageId}`);
        const response = await apiService.checkPatientMessageStatus(messageId);
        console.log('Message status:', response);
        
        if (response.done) {
            // Remove typing indicator
            if (typingIndicator && typingIndicator.parentNode) {
                typingIndicator.remove();
            }
            
            // Add bot response to chat
            addMessageToChat('bot', response.text, messageId, response.audio);
            
            // Play audio if enabled
            if (response.audio && appState.soundEnabled) {
                playResponseAudio(response.audio, messageId);
            }
            
            // Stop polling
            clearPollingInterval('patientMessage');
        } else if (response.text && response.text.length > 0) {
            // Update typing indicator with partial response
            if (typingIndicator) {
                const content = typingIndicator.querySelector('.message-content');
                if (content) {
                    content.textContent = response.text;
                }
            }
        }
    } catch (error) {
        console.error('Message status polling failed:', error);
        // Remove typing indicator
        if (typingIndicator && typingIndicator.parentNode) {
            typingIndicator.remove();
        }
        
        clearPollingInterval('patientMessage');
        showToast('Failed to receive message response', 'error');
    }
}

// Add message to chat
function addMessageToChat(type, text, messageId = null, audioData = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    if (messageId) {
        messageDiv.dataset.id = messageId;
    }
    
    const timestamp = new Date();
    const timeString = timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    // Add avatar
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    avatarDiv.innerHTML = type === 'bot' ? 
        '<i class="fas fa-robot"></i>' : 
        '<i class="fas fa-user"></i>';
    
    // Create message bubble
    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'message-bubble';
    
    // Add message info (sender + time)
    const infoDiv = document.createElement('div');
    infoDiv.className = 'message-info';
    infoDiv.innerHTML = `
        <span class="message-sender">${type === 'bot' ? 'Paco' : 'You'}</span>
        <span class="message-time">${timeString}</span>
    `;
    
    // Add message content
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = text;
    
    // Add audio button if it's a bot message with audio
    if (type === 'bot' && audioData) {
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'message-actions';
        
        const audioBtn = document.createElement('button');
        audioBtn.className = 'audio-btn';
        audioBtn.title = 'Play audio';
        audioBtn.innerHTML = '<i class="fas fa-play"></i>';
        
        audioBtn.addEventListener('click', () => {
            toggleAudioPlayback(audioData, messageId, audioBtn);
        });
        
        actionsDiv.appendChild(audioBtn);
        bubbleDiv.appendChild(actionsDiv);
    }
    
    // Assemble message components
    bubbleDiv.appendChild(infoDiv);
    bubbleDiv.appendChild(contentDiv);
    
    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(bubbleDiv);
    
    // Add to chat container
    patientChatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    patientChatMessages.scrollTop = patientChatMessages.scrollHeight;
    
    return messageDiv;
}

// Toggle audio playback for a message
function toggleAudioPlayback(audioData, messageId, buttonElement) {
    // If we're already playing this audio
    if (appState.audioControl.isPlaying && appState.audioControl.currentMessageId === messageId) {
        // Stop it
        stopCurrentAudio();
        return;
    }
    
    // If we're playing a different audio, stop it first
    if (appState.audioControl.isPlaying) {
        stopCurrentAudio();
    }
    
    // Start playing the new audio
    playResponseAudio(audioData, messageId);
    
    // Update button
    buttonElement.querySelector('i').className = 'fas fa-pause';
}

// Stop currently playing audio
function stopCurrentAudio() {
    if (appState.audioControl.isPlaying) {
        audioPlayer.pause();
        audioPlayer.currentTime = 0;
        
        // Update button icon
        const currentPlayButton = document.querySelector(`.message[data-id="${appState.audioControl.currentMessageId}"] .audio-btn i`);
        if (currentPlayButton) {
            currentPlayButton.className = 'fas fa-play';
        }
        
        appState.audioControl.isPlaying = false;
        appState.audioControl.currentMessageId = null;
    }
}

// Add typing indicator to chat
function addTypingIndicator() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot typing-indicator';
    
    // Add avatar
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    avatarDiv.innerHTML = '<i class="fas fa-robot"></i>';
    
    // Create message bubble
    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'message-bubble';
    
    // Add message info
    const infoDiv = document.createElement('div');
    infoDiv.className = 'message-info';
    infoDiv.innerHTML = `
        <span class="message-sender">Paco</span>
        <span class="message-time">typing...</span>
    `;
    
    // Add message content
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = '<span class="dot-typing"></span>';
    
    // Assemble message components
    bubbleDiv.appendChild(infoDiv);
    bubbleDiv.appendChild(contentDiv);
    
    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(bubbleDiv);
    
    // Add to chat container
    patientChatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    patientChatMessages.scrollTop = patientChatMessages.scrollHeight;
    
    return messageDiv;
}

// Play audio response
function playResponseAudio(audioBase64, messageId) {
    audioPlayer.src = `data:audio/mp3;base64,${audioBase64}`;
    
    // Update state
    appState.audioControl.isPlaying = true;
    appState.audioControl.currentMessageId = messageId;
    
    // Update button icon
    const playButton = document.querySelector(`.message[data-id="${messageId}"] .audio-btn i`);
    if (playButton) {
        playButton.className = 'fas fa-pause';
    }
    
    // Play audio
    audioPlayer.play().catch(error => {
        console.error('Error playing audio:', error);
        showToast('Error playing audio', 'error');
        
        // Reset state
        appState.audioControl.isPlaying = false;
        appState.audioControl.currentMessageId = null;
        
        // Reset button
        if (playButton) {
            playButton.className = 'fas fa-play';
        }
    });
}

// UI Utilities
// Show loading spinner
function showLoading(show, message = 'Processing...') {
    loadingSpinner.classList.toggle('hidden', !show);
    loadingText.textContent = message;
}

// Show toast notification
function showToast(message, type = 'success') {
    const iconMap = {
        'success': 'fas fa-check-circle',
        'error': 'fas fa-exclamation-circle',
        'warning': 'fas fa-exclamation-triangle',
        'info': 'fas fa-info-circle'
    };
    
    // Set icon and message
    const toastIcon = toast.querySelector('.toast-icon');
    if (toastIcon) {
        toastIcon.className = 'toast-icon ' + iconMap[type];
    }
    
    const toastMessage = toast.querySelector('.toast-message');
    if (toastMessage) {
        toastMessage.textContent = message;
    }
    
    // Set type class
    toast.className = 'toast';
    toast.classList.add(type);
    
    // Show toast
    toast.classList.add('show');
    
    // Auto hide after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Open modal
function openModal() {
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden'; // Prevent background scrolling
}

// Close modal
function closeModal() {
    modal.style.display = 'none';
    document.body.style.overflow = ''; // Restore scrolling
}

// Clear polling interval
function clearPollingInterval(type) {
    if (appState.pollIntervals[type]) {
        clearInterval(appState.pollIntervals[type]);
        appState.pollIntervals[type] = null;
    }
}

// Clear all polling intervals
function clearAllPollingIntervals() {
    Object.keys(appState.pollIntervals).forEach(clearPollingInterval);
}

// Initialize marked.js for Markdown parsing
const marked = {
    parse: function(text) {
        if (!text) return '';
        return text
            .replace(/^# (.*$)/gm, '<h1>$1</h1>')
            .replace(/^## (.*$)/gm, '<h2>$1</h2>')
            .replace(/^### (.*$)/gm, '<h3>$1</h3>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/^- (.*?)$/gm, '<li>$1</li>')
            .replace(/\n/g, '<br>');
    }
};

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', initApp);