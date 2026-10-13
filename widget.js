(function () {
    const BACKEND_URL = "https://hotel-ai-bot-w6cn.onrender.com/chat";

    // 1. Inject Styles
    const style = document.createElement('style');
    style.innerHTML = `
        #hotel-ai-widget-container * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
        #ai-chat-toggle-btn { background: #2563eb; color: white; border: none; padding: 14px 22px; border-radius: 35px; cursor: pointer; font-weight: 600; font-size: 15px; box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4); display: flex; align-items: center; gap: 8px; transition: transform 0.2s ease; }
        #ai-chat-window { display: none; width: 350px; height: 480px; background: #ffffff; border: 1px solid #e5e7eb; border-radius: 16px; flex-direction: column; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15); position: absolute; bottom: 65px; right: 0; overflow: hidden; z-index: 999999; }
    `;
    document.head.appendChild(style);

    // 2. Inject HTML Structure
    const container = document.createElement('div');
    container.id = 'hotel-ai-widget-container';
    container.style.cssText = 'position: fixed; bottom: 20px; right: 20px; z-index: 999999;';
    
    container.innerHTML = `
        <button id="ai-chat-toggle-btn" onclick="window.toggleHotelChat()">
            <span>💬 Chat with Reception</span>
        </button>
        <div id="ai-chat-window">
            <div style="background: #2563eb; color: white; padding: 16px; font-weight: 600; font-size: 16px; display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="width: 8px; height: 8px; background: #4ade80; border-radius: 50%;"></span>
                    <span>The Librish Assistant</span>
                </div>
                <button onclick="window.toggleHotelChat()" style="background: none; border: none; color: white; font-size: 18px; cursor: pointer; padding: 0;">✕</button>
            </div>
            <div id="ai-chat-messages" style="flex: 1; padding: 16px; overflow-y: auto; font-size: 14px; background: #f8fafc; display: flex; flex-direction: column; gap: 12px; scroll-behavior: smooth;">
                <div style="align-self: flex-start; background: #ffffff; color: #1e293b; padding: 10px 14px; border-radius: 12px; border: 1px solid #e2e8f0; max-width: 80%; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                    Hello! Welcome to Hotel The Librish. How can I assist you with your stay or booking today?
                </div>
            </div>
            <div style="display: flex; border-top: 1px solid #e2e8f0; background: #ffffff; padding: 10px; gap: 8px; align-items: center;">
                <input type="text" id="ai-chat-input" placeholder="Ask about rooms, timings..." onkeypress="if(event.key==='Enter')window.sendUserMessage()" style="flex: 1; border: 1px solid #cbd5e1; border-radius: 8px; padding: 10px 12px; outline: none; font-size: 14px;">
                <button onclick="window.sendUserMessage()" style="background: #2563eb; color: white; border: none; border-radius: 8px; padding: 10px 16px; cursor: pointer; font-weight: 600; font-size: 14px;">Send</button>
            </div>
        </div>
    `;
    document.body.appendChild(container);

    // 3. Widget Functions
    window.toggleHotelChat = function() {
        const chatWindow = document.getElementById('ai-chat-window');
        const toggleBtn = document.getElementById('ai-chat-toggle-btn');
        if (chatWindow.style.display === 'none' || chatWindow.style.display === '') {
            chatWindow.style.display = 'flex';
            toggleBtn.style.transform = 'scale(0.95)';
            document.getElementById('ai-chat-input').focus();
        } else {
            chatWindow.style.display = 'none';
            toggleBtn.style.transform = 'scale(1)';
        }
    };

    window.sendUserMessage = async function() {
        const inputField = document.getElementById('ai-chat-input');
        const messageContainer = document.getElementById('ai-chat-messages');
        const userText = inputField.value.trim();
        if (!userText) return;

        messageContainer.innerHTML += `
            <div style="align-self: flex-end; background: #2563eb; color: white; padding: 10px 14px; border-radius: 12px; max-width: 80%; word-break: break-word;">
                ${escapeHtml(userText)}
            </div>
        `;
        inputField.value = '';
        messageContainer.scrollTop = messageContainer.scrollHeight;

        const typingId = 'typing-' + Date.now();
        messageContainer.innerHTML += `
            <div id="${typingId}" style="align-self: flex-start; background: #ffffff; color: #64748b; padding: 10px 14px; border-radius: 12px; border: 1px solid #e2e8f0; font-style: italic; font-size: 13px;">
                Typing...
            </div>
        `;
        messageContainer.scrollTop = messageContainer.scrollHeight;

        try {
            const response = await fetch(BACKEND_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: userText })
            });
            const data = await response.json();
            document.getElementById(typingId).remove();

            const formattedReply = escapeHtml(data.reply).replace(/\n/g, '<br>');
            messageContainer.innerHTML += `
                <div style="align-self: flex-start; background: #ffffff; color: #1e293b; padding: 12px 14px; border-radius: 12px; border: 1px solid #e2e8f0; max-width: 85%; word-break: break-word; box-shadow: 0 1px 2px rgba(0,0,0,0.05); line-height: 1.5;">
                    ${formattedReply}
                </div>
            `;
        } catch (error) {
            document.getElementById(typingId).remove();
            messageContainer.innerHTML += `
                <div style="align-self: flex-start; background: #fee2e2; color: #991b1b; padding: 10px 14px; border-radius: 12px; font-size: 13px;">
                    Connection error. Please try again later.
                </div>
            `;
        }
        messageContainer.scrollTop = messageContainer.scrollHeight;
    };

    function escapeHtml(text) {
        const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
        return text.replace(/[&<>"']/g, function(m) { return map[m]; });
    }
})();
