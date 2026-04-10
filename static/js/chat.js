/**
 * AI Career Coach - Chat Interface
 * Handles all chat functionality including message rendering, API calls, and UI interactions
 */

// State management
const state = {
    messages: [],
    isLoading: false,
    resumeSummary: null
};

// DOM elements
const elements = {
    chatBody: null,
    emptyState: null,
    messagesContainer: null,
    errorBanner: null,
    errorMessage: null,
    dismissError: null,
    messageInput: null,
    charCount: null,
    sendBtn: null,
    sendIcon: null,
    sendSpinner: null,
    chatForm: null,
    promptChips: null,
    copyResumeBtn: null
};

/**
 * Initialize the chat interface
 */
function init() {
    // Get DOM elements
    elements.chatBody = document.getElementById('chatBody');
    elements.emptyState = document.getElementById('emptyState');
    elements.messagesContainer = document.getElementById('messagesContainer');
    elements.errorBanner = document.getElementById('errorBanner');
    elements.errorMessage = document.getElementById('errorMessage');
    elements.dismissError = document.getElementById('dismissError');
    elements.messageInput = document.getElementById('messageInput');
    elements.charCount = document.getElementById('charCount');
    elements.sendBtn = document.getElementById('sendBtn');
    elements.sendIcon = elements.sendBtn?.querySelector('.send-icon');
    elements.sendSpinner = elements.sendBtn?.querySelector('.send-spinner');
    elements.chatForm = document.getElementById('chatForm');
    elements.copyResumeBtn = document.getElementById('copyResume');

    // Set up event listeners
    setupEventListeners();

    // Focus on input
    elements.messageInput?.focus();
}

/**
 * Set up all event listeners
 */
function setupEventListeners() {
    // Form submission
    elements.chatForm?.addEventListener('submit', handleSubmit);

    // Textarea auto-resize and character counter
    elements.messageInput?.addEventListener('input', handleInputChange);

    // Enter key handling (Enter to send, Shift+Enter for newline)
    elements.messageInput?.addEventListener('keydown', handleKeyDown);

    // Prompt chips
    const chips = document.querySelectorAll('.prompt-chip');
    chips.forEach(chip => {
        chip.addEventListener('click', () => handleChipClick(chip));
    });

    // Error banner dismiss
    elements.dismissError?.addEventListener('click', hideErrorBanner);

    // Copy resume summary button
    elements.copyResumeBtn?.addEventListener('click', handleCopyResume);
}

/**
 * Handle form submission
 */
async function handleSubmit(e) {
    e.preventDefault();

    const message = elements.messageInput.value.trim();
    if (!message || state.isLoading) return;

    // Hide empty state and show messages container
    if (elements.emptyState) {
        elements.emptyState.style.display = 'none';
    }
    if (elements.messagesContainer) {
        elements.messagesContainer.style.display = 'block';
    }

    // Add user message
    addMessage({
        role: 'user',
        content: message,
        timestamp: new Date()
    });

    // Clear input
    elements.messageInput.value = '';
    elements.charCount.textContent = '0';
    updateSendButton();
    autoResizeTextarea();

    // Set loading state
    setLoadingState(true);

    // Show typing indicator
    showTypingIndicator();

    try {
        // Send request to backend
        const response = await fetch('/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                message: message,
                question: message  // Backend might use 'question' field
            })
        });

        const data = await response.json();

        // Remove typing indicator
        hideTypingIndicator();

        if (response.ok && (data.success || data.answer || data.response)) {
            // Add assistant message
            const assistantMessage = data.answer || data.response || 'I received your message.';
            addMessage({
                role: 'assistant',
                content: assistantMessage,
                timestamp: new Date(),
                metadata: data.metadata
            });
        } else {
            // Show error
            showErrorBanner(data.error || 'Failed to get response from AI');
        }
    } catch (error) {
        hideTypingIndicator();
        showErrorBanner(`Network error: ${error.message}`);
    } finally {
        setLoadingState(false);
        // Return focus to textarea
        elements.messageInput?.focus();
    }
}

/**
 * Handle input change (character counter and auto-resize)
 */
function handleInputChange(e) {
    const value = e.target.value;
    elements.charCount.textContent = value.length;
    updateSendButton();
    autoResizeTextarea();
}

/**
 * Handle keyboard events
 */
function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        elements.chatForm.dispatchEvent(new Event('submit'));
    }
}

/**
 * Handle prompt chip click
 */
function handleChipClick(chip) {
    const prompt = chip.dataset.prompt;
    if (prompt) {
        elements.messageInput.value = prompt;
        elements.charCount.textContent = prompt.length;
        updateSendButton();
        autoResizeTextarea();
        elements.messageInput.focus();
    }
}

/**
 * Add a message to the chat
 */
function addMessage(message) {
    state.messages.push(message);

    const messageEl = document.createElement('div');
    messageEl.className = `msg msg--${message.role}`;

    if (message.role === 'user') {
        messageEl.innerHTML = `
            <div class="msg-avatar">👤</div>
            <div class="msg-content">
                <div class="msg-bubble">
                    <p>${escapeHtml(message.content)}</p>
                </div>
                <div class="msg-footer">
                    <span class="msg-timestamp">${formatTimestamp(message.timestamp)}</span>
                </div>
            </div>
        `;
    } else {
        // Render markdown for assistant messages
        const renderedContent = renderMarkdown(message.content);
        const messageId = `msg-${Date.now()}`;

        messageEl.innerHTML = `
            <div class="msg-avatar">🤖</div>
            <div class="msg-content">
                <div class="msg-bubble">
                    ${renderedContent}
                </div>
                <div class="msg-footer">
                    <span class="msg-timestamp">${formatTimestamp(message.timestamp)}</span>
                    <button class="copy-btn-msg" data-message-id="${messageId}" aria-label="Copy message">
                        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                            <rect x="2" y="2" width="7" height="9" rx="1" stroke="currentColor" stroke-width="1.2" fill="none"/>
                            <path d="M5 2V1a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1h-1" stroke="currentColor" stroke-width="1.2" fill="none"/>
                        </svg>
                        Copy
                    </button>
                </div>
            </div>
        `;

        // Add copy button event listener
        const copyBtn = messageEl.querySelector('.copy-btn-msg');
        copyBtn.addEventListener('click', () => handleCopyMessage(message.content, copyBtn));
    }

    elements.messagesContainer.appendChild(messageEl);
    scrollToBottom();
    
    // Enhanced scroll: ensure the new message is fully visible
    if (message.role === 'assistant') {
        setTimeout(() => {
            messageEl.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }, 150);
    }
}

/**
 * Show typing indicator
 */
function showTypingIndicator() {
    const typingEl = document.createElement('div');
    typingEl.className = 'msg msg--assistant typing-indicator';
    typingEl.id = 'typingIndicator';
    typingEl.innerHTML = `
        <div class="msg-avatar">🤖</div>
        <div class="msg-content">
            <div class="msg-bubble">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        </div>
    `;
    elements.messagesContainer.appendChild(typingEl);
    scrollToBottom();
}

/**
 * Hide typing indicator
 */
function hideTypingIndicator() {
    const typingEl = document.getElementById('typingIndicator');
    if (typingEl) {
        typingEl.remove();
    }
}

/**
 * Render markdown content with sanitization
 */
function renderMarkdown(content) {
    // Configure marked options
    marked.setOptions({
        breaks: true,
        gfm: true
    });

    // Render markdown
    const html = marked.parse(content);

    // Sanitize with DOMPurify
    const clean = DOMPurify.sanitize(html, {
        ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'code', 'pre', 'blockquote', 'a'],
        ALLOWED_ATTR: ['href', 'target', 'rel']
    });

    return clean;
}

/**
 * Handle copy message
 */
let copyDebounceTimer = null;
async function handleCopyMessage(content, button) {
    // Debounce guard - prevent rapid clicks
    if (copyDebounceTimer) {
        return;
    }

    try {
        await navigator.clipboard.writeText(content);
        
        // Update button state
        const originalText = button.innerHTML;
        button.classList.add('copied');
        button.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M2 7l4 4 8-8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            Copied
        `;

        // Set debounce timer
        copyDebounceTimer = setTimeout(() => {
            copyDebounceTimer = null;
        }, 500);

        // Reset after 2 seconds
        setTimeout(() => {
            button.classList.remove('copied');
            button.innerHTML = originalText;
        }, 2000);
    } catch (error) {
        console.error('Failed to copy:', error);
    }
}

/**
 * Handle copy resume summary
 */
let copyResumeDebounceTimer = null;
async function handleCopyResume() {
    // Debounce guard
    if (copyResumeDebounceTimer) {
        return;
    }

    const resumeContent = elements.copyResumeBtn.closest('.aside-card').querySelector('.aside-content p');
    if (resumeContent) {
        try {
            await navigator.clipboard.writeText(resumeContent.textContent);
            
            // Visual feedback
            const originalHTML = elements.copyResumeBtn.innerHTML;
            elements.copyResumeBtn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M3 8l4 4 8-8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            `;

            // Set debounce timer
            copyResumeDebounceTimer = setTimeout(() => {
                copyResumeDebounceTimer = null;
            }, 500);

            setTimeout(() => {
                elements.copyResumeBtn.innerHTML = originalHTML;
            }, 2000);
        } catch (error) {
            console.error('Failed to copy resume:', error);
        }
    }
}

/**
 * Show error banner
 */
function showErrorBanner(message) {
    elements.errorMessage.textContent = message;
    elements.errorBanner.style.display = 'flex';
    elements.errorBanner.focus();
    scrollToBottom();
}

/**
 * Hide error banner
 */
function hideErrorBanner() {
    elements.errorBanner.style.display = 'none';
}

/**
 * Set loading state
 */
function setLoadingState(loading) {
    state.isLoading = loading;
    elements.sendBtn.disabled = loading;
    elements.messageInput.disabled = loading;

    if (loading) {
        elements.sendIcon.style.display = 'none';
        elements.sendSpinner.style.display = 'flex';
    } else {
        elements.sendIcon.style.display = 'flex';
        elements.sendSpinner.style.display = 'none';
    }
}

/**
 * Update send button state
 */
function updateSendButton() {
    const hasContent = elements.messageInput.value.trim().length > 0;
    elements.sendBtn.disabled = !hasContent || state.isLoading;
}

/**
 * Auto-resize textarea
 */
function autoResizeTextarea() {
    elements.messageInput.style.height = 'auto';
    elements.messageInput.style.height = Math.min(elements.messageInput.scrollHeight, 144) + 'px';
}

/**
 * Scroll to bottom of chat
 */
function scrollToBottom() {
    setTimeout(() => {
        elements.chatBody.scrollTop = elements.chatBody.scrollHeight;
    }, 100);
}

/**
 * Format timestamp
 */
function formatTimestamp(date) {
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) {
        return 'Just now';
    } else if (diff < 3600000) {
        const minutes = Math.floor(diff / 60000);
        return `${minutes}m ago`;
    } else {
        return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
    }
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}