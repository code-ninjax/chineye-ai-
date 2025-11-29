/* ============================================================================ */
/* API CONFIGURATION */
/* ============================================================================ */

// Change this to your backend URL when deployed
// Use window.location.hostname to handle different environments
const API_BASE_URL = `http://${window.location.hostname}:8000/api`;

// Typing animation speed configuration (lower = faster)
const TYPING_BASE_DELAY_MS = 6; // previously ~18
const TYPING_VARIANCE_MS = 12; // previously up to ~30

// Controls for aborting generation and typing
let currentAbortController = null;
let typingEffectController = null;
let currentTypingDiv = null;

/* ============================================================================ */
/* LOCAL STORAGE FUNCTIONS */
/* ============================================================================ */

/**
 * Save JWT token to localStorage
 * @param {string} token - JWT token from server
 */
function saveTokenToLocalStorage(token) {
    localStorage.setItem('authToken', token);
}

/**
 * Get JWT token from localStorage
 * @returns {string|null} - JWT token or null if not found
 */
function getToken() {
    return localStorage.getItem('authToken');
}

/**
 * Remove JWT token from localStorage
 */
function removeTokenFromLocalStorage() {
    localStorage.removeItem('authToken');
}

/* ============================================================================ */
/* SIGNUP FUNCTION */
/* ============================================================================ */

/**
 * Handle user signup
 */
async function signupUser() {
    const username = document.getElementById('username').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    const messageDiv = document.getElementById('signupMessage');
    
    // Validation
    if (!username || !email || !password || !confirmPassword) {
        showMessage(messageDiv, 'All fields are required', 'error');
        return;
    }
    
    if (password.length < 6) {
        showMessage(messageDiv, 'Password must be at least 6 characters', 'error');
        return;
    }
    
    if (password !== confirmPassword) {
        showMessage(messageDiv, 'Passwords do not match', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/signup`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username,
                email,
                password,
            }),
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage(messageDiv, 'Account created successfully! Redirecting...', 'success');
            setTimeout(() => {
                window.location.href = 'login.html';
            }, 1500);
        } else {
            showMessage(messageDiv, data.detail || 'Signup failed', 'error');
        }
    } catch (error) {
        console.error('Signup error:', error);
        showMessage(messageDiv, 'An error occurred. Please try again.', 'error');
    }
}

/* ============================================================================ */
/* LOGIN FUNCTION */
/* ============================================================================ */

/**
 * Handle user login
 */
async function loginUser() {
    const email = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value;
    const messageDiv = document.getElementById('loginMessage');
    
    // Validation
    if (!email || !password) {
        showMessage(messageDiv, 'Email and password are required', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email,
                password,
            }),
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Save token and username
            saveTokenToLocalStorage(data.access_token);
            if (data.username) {
                localStorage.setItem('username', data.username);
            }
            showMessage(messageDiv, 'Login successful! Redirecting...', 'success');
            setTimeout(() => {
                window.location.href = 'chat.html';
            }, 900);
        } else {
            showMessage(messageDiv, data.detail || 'Login failed', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showMessage(messageDiv, 'An error occurred. Please try again.', 'error');
    }
}

/* ============================================================================ */
/* SEND MESSAGE FUNCTION */
/* ============================================================================ */

/**
 * Send a message to the chatbot
 */
async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    // chatMessages is only declared once below
    
    if (!message) return;
    
    // Check authentication
    const token = getToken();
    if (!token) {
        window.location.href = 'login.html';
        return;
    }
    
    // Add user message to chat
    addMessageToChat(message, 'user');
    input.value = '';

    // Add typing effect placeholder and show Stop button
    const chatMessages = document.getElementById('chatMessages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot-message';
    typingDiv.innerHTML = '<p><span class="typing-dots">...</span></p>';
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    currentTypingDiv = typingDiv;
    const stopBtn = document.getElementById('stopBtn');
    if (stopBtn) stopBtn.style.display = 'inline-block';
    currentAbortController = new AbortController();

    try {
        const response = await fetch(`${API_BASE_URL}/send-message`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
            },
            signal: currentAbortController.signal,
            body: JSON.stringify({
                message,
            }),
        });

        const data = await response.json();

        // Remove typing effect
        if (typingDiv && typingDiv.parentNode) {
            chatMessages.removeChild(typingDiv);
        }
        currentTypingDiv = null;

        if (response.ok) {
            // Add bot response to chat with animated typing, cancellable
            typingEffectController = { cancel: false };
            showTypingEffect(data.response, typingEffectController);
        } else {
            addMessageToChat('Sorry, something went wrong. Please try again.', 'bot');
            if (stopBtn) stopBtn.style.display = 'none';
        }
    } catch (error) {
        if (typingDiv && typingDiv.parentNode) {
            chatMessages.removeChild(typingDiv);
        }
        currentTypingDiv = null;
        console.error('Send message error:', error);
        if (error && (error.name === 'AbortError' || error.code === 'AbortError')) {
            addMessageToChat('Generation stopped.', 'bot');
        } else {
            addMessageToChat('Error connecting to the server. Please try again.', 'bot');
        }
        const stopBtn = document.getElementById('stopBtn');
        if (stopBtn) stopBtn.style.display = 'none';
    }

}

/**
 * Show animated typing effect for bot response
 */
function showTypingEffect(text, controller) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message';
    const p = document.createElement('p');
    messageDiv.appendChild(p);
    // Actions container (hidden until hover)
    const actions = document.createElement('div');
    actions.className = 'message-actions';
    actions.innerHTML = '<button class="copy-btn" title="Copy"><i class="fa-regular fa-copy"></i> Copy</button>';
    messageDiv.appendChild(actions);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    let i = 0;
    function typeChar() {
        if (controller && controller.cancel) {
            const stopBtn = document.getElementById('stopBtn');
            if (stopBtn) stopBtn.style.display = 'none';
            // leave the current partial text
            return;
        }
        p.textContent = text.slice(0, i);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        if (i < text.length) {
            i++;
            setTimeout(typeChar, TYPING_BASE_DELAY_MS + Math.random() * TYPING_VARIANCE_MS);
        } else {
            const stopBtn = document.getElementById('stopBtn');
            if (stopBtn) stopBtn.style.display = 'none';
            typingEffectController = null;
        }
    }
    typeChar();
}

/* ============================================================================ */
/* LOAD CHAT HISTORY FUNCTION */
/* ============================================================================ */

/**
 * Load chat history for the current user
 */
async function loadChatHistory() {
    const token = getToken();
    if (!token) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/history`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        });
        
        const data = await response.json();
        
        if (response.ok && data.history && data.history.length > 0) {
            const chatMessages = document.getElementById('chatMessages');
            // Clear default message
            if (chatMessages) chatMessages.innerHTML = '';

            // Add each message from history
            data.history.forEach((entry) => {
                addMessageToChat(entry.message, 'user');
                addMessageToChat(entry.response, 'bot');
            });
            return data.history;
        }
        return data.history || [];
    } catch (error) {
        console.error('Load chat history error:', error);
    }
}

/**
 * Populate the left sidebar with history entries.
 * Called by chat.html after loadChatHistory returns.
 */
function populateSidebar(history) {
    const list = document.getElementById('chatList');
    if (!list || !history) return;
    list.innerHTML = '';
    history.forEach((entry, idx) => {
        const li = document.createElement('li');
        li.className = 'chat-item';
        li.textContent = `${new Date(entry.timestamp).toLocaleString()}: ${entry.message.slice(0, 40)}...`;
        li.addEventListener('click', () => {
            const chatMessages = document.getElementById('chatMessages');
            if (!chatMessages) return;
            chatMessages.innerHTML = '';
            addMessageToChat(entry.message, 'user');
            addMessageToChat(entry.response, 'bot');
        });
        list.appendChild(li);
    });
}

/* ============================================================================ */
/* LOGOUT FUNCTION */
/* ============================================================================ */

/**
 * Handle user logout
 */
async function logoutUser() {
    const token = getToken();
    
    try {
        await fetch(`${API_BASE_URL}/logout`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        });
    } catch (error) {
        console.error('Logout error:', error);
    }
    
    // Remove token and redirect
    removeTokenFromLocalStorage();
    // remove stored username
    try { localStorage.removeItem('username'); } catch (e) {}
    window.location.href = 'index.html';
}

/* ============================================================================ */
/* HELPER FUNCTIONS */
/* ============================================================================ */

/**
 * Add a message to the chat display
 * @param {string} text - Message text
 * @param {string} sender - 'user' or 'bot'
 */
function addMessageToChat(text, sender) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const p = document.createElement('p');
    p.textContent = text;
    
    messageDiv.appendChild(p);
    if (sender === 'bot') {
        const actions = document.createElement('div');
        actions.className = 'message-actions';
        actions.innerHTML = '<button class="copy-btn" title="Copy"><i class="fa-regular fa-copy"></i> Copy</button>';
        messageDiv.appendChild(actions);
    }
    chatMessages.appendChild(messageDiv);
    
    // Auto scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Stop generation handler
function stopGeneration() {
    if (currentAbortController) {
        try { currentAbortController.abort(); } catch (e) {}
        currentAbortController = null;
    }
    if (typingEffectController) {
        typingEffectController.cancel = true;
    }
    if (currentTypingDiv && currentTypingDiv.parentNode) {
        currentTypingDiv.parentNode.removeChild(currentTypingDiv);
        currentTypingDiv = null;
    }
    const stopBtn = document.getElementById('stopBtn');
    if (stopBtn) stopBtn.style.display = 'none';
}

// Copy button delegation
document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chatMessages');
    if (chatMessages) {
        chatMessages.addEventListener('click', (e) => {
            const btn = e.target.closest('.copy-btn');
            if (btn) {
                const messageDiv = btn.closest('.message');
                const text = messageDiv && messageDiv.querySelector('p') ? messageDiv.querySelector('p').textContent : '';
                if (text) {
                    navigator.clipboard.writeText(text).catch(() => {});
                }
            }
        });
    }
    // Bind stop button if present
    const stopBtn = document.getElementById('stopBtn');
    if (stopBtn) {
        stopBtn.addEventListener('click', (e) => {
            e.preventDefault();
            stopGeneration();
        });
    }
});

/**
 * Show success or error message
 * @param {HTMLElement} element - Message container element
 * @param {string} text - Message text
 * @param {string} type - 'success' or 'error'
 */
function showMessage(element, text, type) {
    element.textContent = text;
    element.className = `auth-message ${type}`;
    
    // Auto-hide after 5 seconds
    if (type === 'success') {
        setTimeout(() => {
            element.className = 'auth-message';
        }, 5000);
    }
}

/* ============================================================================ */
/* NEWSLETTER SUBSCRIPTION */
/* ============================================================================ */

/**
 * Handle newsletter email subscription
 */
async function subscribeToNewsletter(email) {
    try {
        const response = await fetch(`${API_BASE_URL}/newsletter`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
            }),
        });
        
        const data = await response.json();
        
        if (response.ok) {
            return {
                success: true,
                message: data.message || 'Successfully subscribed to newsletter!',
                email: email
            };
        } else {
            return {
                success: false,
                message: data.detail || 'Subscription failed'
            };
        }
    } catch (error) {
        console.error('Newsletter subscription error:', error);
        return {
            success: false,
            message: 'An error occurred. Please try again.'
        };
    }
}

/* ============================================================================ */
/* THEME: Light / Dark mode helpers                                            */
/* Adds/removes body.dark-mode, persists selection to localStorage, and ties
   any .theme-toggle buttons to the toggle action. */
/* ============================================================================ */

function applyTheme(theme) {
    if (theme === 'dark') {
        document.body.classList.add('dark-mode');
    } else {
        document.body.classList.remove('dark-mode');
    }
    updateToggleIcons();
}

function saveTheme(theme) { localStorage.setItem('theme', theme); }

function initTheme() {
    const saved = localStorage.getItem('theme');
    if (saved) {
        applyTheme(saved);
    } else {
        // Respect system preference when no explicit choice
        const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        applyTheme(prefersDark ? 'dark' : 'light');
    }
    // wire up toggle buttons (may be present on multiple pages)
    document.querySelectorAll('.theme-toggle').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const isDark = document.body.classList.toggle('dark-mode');
            const theme = isDark ? 'dark' : 'light';
            saveTheme(theme);
            updateToggleIcons();
        });
    });
}

function updateToggleIcons() {
    document.querySelectorAll('.theme-toggle').forEach(btn => {
        const icon = btn.querySelector('i');
        if (!icon) return;
        if (document.body.classList.contains('dark-mode')) {
            icon.className = 'fa-solid fa-sun';
            icon.style.color = 'var(--accent-blue)';
        } else {
            icon.className = 'fa-solid fa-moon';
            icon.style.color = 'var(--muted-text)';
        }
    });
}

// Initialize theme as soon as possible
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTheme);
} else {
    initTheme();
}
