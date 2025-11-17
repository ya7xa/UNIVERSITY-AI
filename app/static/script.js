// Modern ChatGPT-like UI Implementation

// Sidebar Toggle
const sidebarToggle = document.getElementById('sidebarToggle');
const sidebar = document.getElementById('sidebar');
const sidebarOverlay = document.getElementById('sidebarOverlay');

sidebarToggle?.addEventListener('click', () => {
    sidebar?.classList.toggle('hidden');
    sidebarOverlay?.classList.toggle('hidden');
});

sidebarOverlay?.addEventListener('click', () => {
    sidebar?.classList.add('hidden');
    sidebarOverlay?.classList.add('hidden');
});

// Auto-resize textarea
const messageInput = document.getElementById('messageInput');
messageInput?.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 128) + 'px';
});

// Handle Enter/Shift+Enter
messageInput?.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm?.requestSubmit();
    }
});

// File Upload Handling
const uploadForm = document.getElementById('uploadForm');
const fileInput = document.getElementById('fileInput');
const uploadStatus = document.getElementById('uploadStatus');
const uploadBtn = document.getElementById('uploadBtn');

uploadForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const file = fileInput?.files[0];
    if (!file) {
        showUploadStatus('Please select a file', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    uploadBtn.disabled = true;
    showUploadStatus('Uploading and processing...', 'info');
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            showUploadStatus('✓ Uploaded successfully!', 'success');
            fileInput.value = '';
            loadFileList();
            updateModeIndicator();
        } else {
            showUploadStatus('✗ ' + (result.message || 'Upload failed'), 'error');
        }
    } catch (error) {
        showUploadStatus('✗ Error: ' + error.message, 'error');
    } finally {
        uploadBtn.disabled = false;
    }
});

function showUploadStatus(message, type) {
    if (!uploadStatus) return;
    uploadStatus.textContent = message;
    uploadStatus.className = 'mt-2 text-xs';
    
    if (type === 'success') {
        uploadStatus.classList.add('text-green-400');
    } else if (type === 'error') {
        uploadStatus.classList.add('text-red-400');
    } else {
        uploadStatus.classList.add('text-blue-400');
    }
    
    if (type === 'success') {
        setTimeout(() => {
            uploadStatus.textContent = '';
        }, 3000);
    }
}

// Load and display file list
async function loadFileList() {
    try {
        const response = await fetch('/files');
        const data = await response.json();
        const fileList = document.getElementById('fileList');
        
        if (!fileList) return;
        
        if (data.files.length === 0) {
            fileList.innerHTML = '<p class="text-xs text-gray-500 text-center py-4">No files uploaded yet</p>';
            return;
        }
        
        fileList.innerHTML = data.files.map(file => `
            <div class="bg-gray-700/50 rounded-lg p-3 border border-gray-700 hover:bg-gray-700 transition-colors">
                <div class="flex items-start justify-between">
                    <div class="flex-1 min-w-0">
                        <p class="text-xs font-medium text-gray-200 truncate">${escapeHtml(file.filename)}</p>
                    </div>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading file list:', error);
    }
}

// Update mode indicator
async function updateModeIndicator() {
    const modeIndicator = document.getElementById('modeIndicator');
    const contextIndicator = document.getElementById('contextIndicator');
    
    try {
        const response = await fetch('/files');
        const data = await response.json();
        const hasFiles = data.files.length > 0;
        
        if (modeIndicator) {
            modeIndicator.textContent = hasFiles ? 'Mixed Mode (RAG)' : 'Direct Mode';
            modeIndicator.className = hasFiles ? 'text-xs text-blue-400' : 'text-xs text-purple-400';
        }
        
        if (contextIndicator) {
            contextIndicator.textContent = hasFiles 
                ? `Using ${data.files.length} file(s) for context` 
                : 'Ready to chat (no files)';
        }
    } catch (error) {
        console.error('Error updating mode indicator:', error);
    }
}

// Chat Handling
const chatForm = document.getElementById('chatForm');
const chatMessages = document.getElementById('chatMessages');
const sendButton = document.getElementById('sendButton');

chatForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const message = messageInput.value.trim();
    if (!message) return;
    
    // Add user message to chat
    addMessageToChat('user', message);
    messageInput.value = '';
    messageInput.style.height = 'auto';
    sendButton.disabled = true;
    
    // Start AI response
    const aiMessageDiv = addMessageToChat('ai', '');
    await streamChatResponse(message, aiMessageDiv);
    
    sendButton.disabled = false;
    messageInput.focus();
});

async function streamChatResponse(message, messageDiv) {
    const formData = new FormData();
    formData.append('message', message);
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Chat request failed');
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let fullResponse = '';
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        
                        if (data.error) {
                            messageDiv.innerHTML = '<span class="text-red-400">Error: ' + escapeHtml(data.error) + '</span>';
                            return;
                        }
                        
                        if (data.chunk) {
                            fullResponse += data.chunk;
                            messageDiv.innerHTML = formatMessage(fullResponse);
                            messageDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
                        }
                        
                        if (data.done) {
                            return;
                        }
                    } catch (e) {
                        console.error('Error parsing SSE data:', e);
                    }
                }
            }
        }
    } catch (error) {
        messageDiv.innerHTML = '<span class="text-red-400">Error: ' + escapeHtml(error.message) + '</span>';
    }
}

function formatMessage(text) {
    // Basic markdown formatting
    let formatted = escapeHtml(text);
    // Bold
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Italic
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
    // Code blocks
    formatted = formatted.replace(/`(.*?)`/g, '<code class="bg-gray-800 px-1 py-0.5 rounded text-blue-400 text-sm">$1</code>');
    // Line breaks
    formatted = formatted.replace(/\n/g, '<br>');
    return formatted;
}

function addMessageToChat(role, content) {
    // Remove welcome message if present
    const welcomeMsg = chatMessages.querySelector('.max-w-3xl.mx-auto.text-center');
    if (welcomeMsg && welcomeMsg.id !== 'message-container') {
        welcomeMsg.remove();
    }
    
    const messageContainer = document.createElement('div');
    messageContainer.className = `flex ${role === 'user' ? 'justify-end' : 'justify-start'} mb-6`;
    messageContainer.id = 'message-container';
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `max-w-3xl ${role === 'user' ? 'bg-blue-600 text-white rounded-2xl rounded-tr-sm' : 'bg-gray-800 text-gray-100 rounded-2xl rounded-tl-sm'} px-4 py-3 shadow-lg`;
    
    if (role === 'ai' && !content) {
        messageDiv.innerHTML = '<div class="flex items-center space-x-2"><div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div><div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div><div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div></div>';
    } else if (role === 'user') {
        messageDiv.textContent = content;
    } else {
        messageDiv.innerHTML = formatMessage(content);
    }
    
    messageContainer.appendChild(messageDiv);
    chatMessages.appendChild(messageContainer);
    messageContainer.scrollIntoView({ behavior: 'smooth', block: 'end' });
    
    return messageDiv;
}

// Suggestion buttons
document.querySelectorAll('.suggestion-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const suggestion = btn.getAttribute('data-suggestion');
        if (suggestion && messageInput) {
            messageInput.value = suggestion;
            messageInput.focus();
            chatForm?.requestSubmit();
        }
    });
});

// File attach button
const fileAttachBtn = document.getElementById('fileAttachBtn');
const quickFileInput = document.getElementById('quickFileInput');

fileAttachBtn?.addEventListener('click', () => {
    quickFileInput?.click();
});

quickFileInput?.addEventListener('change', (e) => {
    if (e.target.files[0]) {
        fileInput.files = e.target.files;
        uploadForm?.requestSubmit();
    }
});

// Utility function
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize: Load file list and update mode indicator on page load
loadFileList();
updateModeIndicator();
setInterval(updateModeIndicator, 5000); // Update every 5 seconds

// Auto-focus message input
messageInput?.focus();
