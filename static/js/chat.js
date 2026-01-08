let CURRENT_CHAT_ID = null;

async function loadChatSessions() {
    if (!DEVICE_ID) return;
    try {
        const res = await fetch(`/user/chats?device_id=${encodeURIComponent(DEVICE_ID)}`);
        const chats = await res.json();
        const historyList = document.getElementById('history-list');
        historyList.innerHTML = ''; // Clear existing list

        if (chats && chats.length > 0) {
            if (!CURRENT_CHAT_ID) {
                CURRENT_CHAT_ID = chats[0].id;
            }
            chats.forEach(chat => {
                const item = document.createElement('div');
                item.className = 'history-item';
                item.dataset.chatId = chat.id;
                if (chat.id === CURRENT_CHAT_ID) {
                    item.classList.add('active');
                }

                item.innerHTML = `
                    <span class="history-item-title">${chat.title}</span>
                    <div class="history-item-actions">
                        <button onclick="renameChat('${chat.id}')"><span class="material-symbols-rounded">edit</span></button>
                        <button onclick="deleteChat('${chat.id}')"><span class="material-symbols-rounded">delete</span></button>
                    </div>
                `;
                item.addEventListener('click', () => {
                    switchChat(chat.id);
                });
                historyList.appendChild(item);
            });
            await loadChatHistory(CURRENT_CHAT_ID);
        } else {
            // No chats, start a new one
            await startNewChat();
        }
    } catch (e) {
        console.error('Failed to load chat sessions', e);
    }
}

async function switchChat(chatId) {
    if (chatId === CURRENT_CHAT_ID) return;
    CURRENT_CHAT_ID = chatId;
    // Update active class
    document.querySelectorAll('.history-item').forEach(item => {
        item.classList.toggle('active', item.dataset.chatId === chatId);
    });
    // Load history for the new chat
    await loadChatHistory(chatId);
}

async function loadChatHistory(chatId) {
    if (!DEVICE_ID || !chatId) return;
    try {
        const res = await fetch(`/user/history?device_id=${encodeURIComponent(DEVICE_ID)}&chat_id=${encodeURIComponent(chatId)}`);
        const data = await res.json();
        const chatBox = document.getElementById('chat-box');
        chatBox.innerHTML = ''; // Clear chat box
        if (data.history && data.history.length) {
            document.getElementById('welcome').style.display = 'none';
            data.history.forEach(h => {
                if (h.startsWith('User:')) {
                    const msg = h.split('\n')[0].replace('User: ', '');
                    addMsg(msg, 'user', false);
                }
                if (h.includes('Vyom AI:')) {
                    const ans = h.split('Vyom AI:')[1];
                    addMsg(marked.parse(ans.trim()), 'ai', true);
                }
            });
        } else {
            document.getElementById('welcome').style.display = 'block';
        }
    } catch (e) {
        console.warn('Failed to load history', e);
    }
}

async function startNewChat() {
    if (!DEVICE_ID) return;
    try {
        const res = await fetch('/user/new_chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ device_id: DEVICE_ID })
        });
        const newChat = await res.json();
        if (newChat && newChat.id) {
            CURRENT_CHAT_ID = newChat.id;
            await loadChatSessions(); // Reload the whole list
            document.getElementById('chat-box').innerHTML = '';
            document.getElementById('welcome').style.display = 'block';
        }
    } catch (e) {
        console.error('Failed to start new chat', e);
    }
}

async function renameChat(chatId) {
    const newTitle = prompt('Enter new chat title:');
    if (!newTitle) return;
    try {
        await fetch('/user/rename_chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ device_id: DEVICE_ID, chat_id: chatId, new_title: newTitle })
        });
        await loadChatSessions(); // Refresh list
    } catch (e) {
        console.error('Failed to rename chat', e);
    }
}

async function deleteChat(chatId) {
    if (!confirm('Are you sure you want to delete this chat?')) return;
    try {
        await fetch('/user/delete_chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ device_id: DEVICE_ID, chat_id: chatId })
        });
        // If we deleted the current chat, switch to another
        if (CURRENT_CHAT_ID === chatId) {
            CURRENT_CHAT_ID = null;
        }
        await loadChatSessions(); // Refresh list
    } catch (e) {
        console.error('Failed to delete chat', e);
    }
}