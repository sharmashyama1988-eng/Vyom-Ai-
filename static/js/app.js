// State
let currentChatId = null;
let isGenerating = false;
let deviceId = localStorage.getItem('vyom_device_id') || crypto.randomUUID();
localStorage.setItem('vyom_device_id', deviceId);

// DOM Elements
const els = {
    sidebar: document.getElementById('sidebar'),
    input: document.getElementById('user-input'),
    messages: document.getElementById('messages-area'),
    welcome: document.getElementById('welcome-screen'),
    chatContainer: document.getElementById('chat-container'),
    historyList: document.getElementById('history-list')
};

// Init
document.addEventListener('DOMContentLoaded', () => {
    loadHistory();
    els.input.focus();
});

// Sidebar Toggle
function toggleSidebar() {
    // If mobile
    if (window.innerWidth <= 768) {
        els.sidebar.classList.toggle('open');
    } else {
        els.sidebar.classList.toggle('collapsed');
    }
}

// Input Handling
function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
}

function handleEnter(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

function setInput(text) {
    els.input.value = text;
    els.input.focus();
    autoResize(els.input);
    sendMessage();
}

// History
async function loadHistory() {
    try {
        const res = await fetch(`/user/chats?device_id=${deviceId}`);
        const chats = await res.json();
        els.historyList.innerHTML = '';
        chats.forEach(chat => {
            const div = document.createElement('div');
            div.className = `history-item ${chat.id === currentChatId ? 'active' : ''}`;
            div.innerHTML = `
                <span class="material-symbols-rounded" style="font-size:18px;">chat_bubble_outline</span>
                <span>${chat.title}</span>
            `;
            div.onclick = () => loadChat(chat.id);
            els.historyList.appendChild(div);
        });
    } catch(e) { console.error(e); }
}

async function loadChat(chatId) {
    currentChatId = chatId;
    els.welcome.style.display = 'none';
    els.messages.innerHTML = '';
    
    // Highlight sidebar item
    document.querySelectorAll('.history-item').forEach(el => el.classList.remove('active'));
    // (Ideally find the specific element to add active class)

    const res = await fetch(`/user/history?device_id=${deviceId}&chat_id=${chatId}`);
    const data = await res.json();
    
    if (data.history) {
        data.history.forEach(msgStr => {
            // "User: Content" or "Vyom AI: Content"
            let role = 'user';
            let content = msgStr;
            if (msgStr.startsWith('User: ')) {
                content = msgStr.replace('User: ', '');
            } else if (msgStr.startsWith('Vyom AI: ')) {
                role = 'ai';
                content = msgStr.replace('Vyom AI: ', '');
            }
            appendMessage(role, content, false);
        });
    }
    scrollToBottom();
}

async function startNewChat() {
    currentChatId = null;
    els.welcome.style.display = 'block';
    els.messages.innerHTML = '';
    els.input.value = '';
    els.input.focus();
}

// Messaging
async function sendMessage() {
    const text = els.input.value.trim();
    if (!text || isGenerating) return;

    // UI Updates
    els.input.value = '';
    els.input.style.height = 'auto';
    els.welcome.style.display = 'none';
    
    // Append User Message
    appendMessage('user', text);
    
    isGenerating = true;
    
    // Placeholder for AI
    const aiId = 'ai-' + Date.now();
    appendMessage('ai', '', true, aiId); // Empty with ID
    
    try {
        const res = await fetch('/ask', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                message: text,
                device_id: deviceId,
                chat_id: currentChatId
            })
        });
        
        const data = await res.json();
        const aiResponse = data.answer || "I'm having trouble connecting.";
        
        // Remove Placeholder logic if we were strictly streaming, 
        // but here we stream the text INTO the placeholder
        await streamText(aiId, aiResponse);
        
        // Refresh history to see new chat title
        loadHistory();
        
    } catch (e) {
        document.getElementById(aiId).innerHTML = "<span style='color:var(--danger)'>Error connecting to server.</span>";
    } finally {
        isGenerating = false;
    }
}

function appendMessage(role, content, isEmpty = false, id = null) {
    const row = document.createElement('div');
    row.className = `message-row ${role}`;
    
    let html = '';
    if (role === 'user') {
        html = `
            <div class="msg-content">
                ${escapeHtml(content)}
            </div>
            <div class="avatar">
                <img src="https://ui-avatars.com/api/?name=User&background=random" alt="User">
            </div>
        `;
    } else {
        html = `
            <div class="avatar">
                <img src="/static/img/logo.svg" onerror="this.src='https://ui-avatars.com/api/?name=Vyom'" alt="Vyom">
            </div>
            <div class="msg-content ai-text" id="${id || ''}">
                ${isEmpty ? '<span class="spin material-symbols-rounded" style="font-size:20px;">sync</span>' : marked.parse(content)}
            </div>
        `;
    }
    
    row.innerHTML = html;
    els.messages.appendChild(row);
    scrollToBottom();
    return row;
}

// Simulated Streaming (Typewriter Effect)
async function streamText(elementId, fullText) {
    const el = document.getElementById(elementId);
    if (!el) return;
    
    el.innerHTML = ''; // Clear spinner
    
    // Header with Sparkle
    const header = document.createElement('div');
    header.className = 'ai-header';
    header.innerHTML = `
        <span class="brand-mobile" style="font-size:0.9rem;">Vyom Ai</span>
        <span class="material-symbols-rounded sparkle-icon" style="font-size:16px; color:#4b90ff;">sparkle</span>
    `;
    el.parentNode.insertBefore(header, el); // Insert header before content

    // Chunking for speed
    const words = fullText.split(' ');
    let currentText = '';
    
    for (let i = 0; i < words.length; i++) {
        currentText += words[i] + ' ';
        // Render Markdown every few words to keep formatting intact
        // Optimized: only render full markdown every 5 words or at end
        if (i % 3 === 0 || i === words.length - 1) {
            el.innerHTML = marked.parse(currentText);
            scrollToBottom();
        }
        await new Promise(r => setTimeout(r, 20)); // Typing speed
    }
}

function scrollToBottom() {
    els.chatContainer.scrollTo({
        top: els.chatContainer.scrollHeight,
        behavior: 'smooth'
    });
}

function escapeHtml(text) {
    if (!text) return text;
    return text.replace(/&/g, "&amp;")
               .replace(/</g, "&lt;")
               .replace(/>/g, "&gt;")
               .replace(/"/g, "&quot;")
               .replace(/'/g, "&#039;");
}

function handleFileUpload(input) {
    if (input.files && input.files[0]) {
        // Implement upload preview logic here
        // For now just alert
        alert("Image attached: " + input.files[0].name);
    }
}

function toggleMic() {
    alert("Voice input listening...");
}
