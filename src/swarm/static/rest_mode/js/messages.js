import { debugLog } from './debug.js';

let quickPrompts = ["What is Open-Swarm?", "Explain the architecture.", "How do I set up a new blueprint?"];

/**
 * Renders a message into the UI.
 */
export function renderMessage(role, content, sender, metadata) {
    debugLog('Rendering message...', { role, content, sender, metadata });

    const messageContainer = document.getElementById('messageHistory');
    if (!messageContainer) {
        debugLog('Message container not found.', { role, content, sender, metadata });
        return;
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.innerHTML = `
        <span><strong>${sender}:</strong> ${content.text || content.content || 'No content available'}</span>
        <div class="message-toolbar">
            <button class="toolbar-btn" aria-label="Thumbs Up">
                <img src="/static/rest_mode/svg/thumbs_up.svg" alt="Thumbs Up Icon" class="icon-svg" />
            </button>
            <button class="toolbar-btn" aria-label="Thumbs Down">
                <img src="/static/rest_mode/svg/thumbs_down.svg" alt="Thumbs Down Icon" class="icon-svg" />
            </button>
            <div class="toolbar-gap"></div>
            <button class="toolbar-btn" aria-label="Append to Persistent Message">
                <img src="/static/rest_mode/svg/plus.svg" alt="Plus Icon" class="icon-svg" />
            </button>
            <button class="toolbar-btn" aria-label="Edit Message">
                <img src="/static/rest_mode/svg/edit.svg" alt="Edit Icon" class="icon-svg" />
            </button>
            <button class="toolbar-btn" aria-label="Copy Message">
                <img src="/static/rest_mode/svg/copy.svg" alt="Copy Icon" class="icon-svg" />
            </button>
            <div class="toolbar-gap"></div>
            <button class="toolbar-btn" aria-label="Delete Message">
                <img src="/static/rest_mode/svg/trash.svg" alt="Trash Icon" class="icon-svg" />
            </button>
        </div>
    `;

    if (metadata && Object.keys(metadata).length) {
        messageDiv.title = JSON.stringify(metadata, null, 2);
    }

    messageContainer.appendChild(messageDiv);
    debugLog('Message rendered successfully.', { role, content, sender, metadata });

    attachToolbarActions(messageDiv);
}

/**
 * Appends a raw message object into the chat UI.
 */
export function appendRawMessage(role, content, sender, metadata) {
    debugLog('Appending raw message...', { role, content, sender, metadata });

    renderMessage(role, content, sender, metadata);

    const messageContainer = document.getElementById('messageHistory');
    if (messageContainer) {
        messageContainer.scrollTop = messageContainer.scrollHeight;
        debugLog('Scrolled to the bottom of the message history.');
    }
}

/**
 * Renders quick prompts in the UI.
 */
export function renderQuickPrompts() {
    const quickPromptsContainer = document.getElementById('quickPrompts');
    if (!quickPromptsContainer) {
        debugLog('Quick prompts container not found.');
        return;
    }

    quickPromptsContainer.innerHTML = quickPrompts
        .map(
            (prompt, index) => `
            <button class="quick-prompt-button" data-index="${index}">
                ${prompt}
            </button>`
        )
        .join('');

    document.querySelectorAll('.quick-prompt-button').forEach((button) =>
        button.addEventListener('click', (e) => handleQuickPromptSelection(e))
    );
    debugLog('Quick prompts rendered successfully.');
}

/**
 * Handles quick prompt selection.
 */
function handleQuickPromptSelection(event) {
    const promptIndex = event.target.getAttribute('data-index');
    const promptText = quickPrompts[promptIndex];

    appendRawMessage('user', { content: promptText }, 'User', {});
    clearQuickPrompts();
}

/**
 * Clears all quick prompts from the UI.
 */
function clearQuickPrompts() {
    const quickPromptsContainer = document.getElementById('quickPrompts');
    if (quickPromptsContainer) {
        quickPromptsContainer.innerHTML = '';
        debugLog('Quick prompts cleared.');
    }
}

/**
 * Allows adding a new quick prompt dynamically.
 */
export function addQuickPrompt(prompt) {
    quickPrompts.push(prompt);
    renderQuickPrompts();
    debugLog('Quick prompt added.', { prompt });
}

/**
 * Removes a quick prompt by index.
 */
export function removeQuickPrompt(index) {
    if (index < 0 || index >= quickPrompts.length) {
        debugLog('Invalid quick prompt index.', { index });
        return;
    }
    quickPrompts.splice(index, 1);
    renderQuickPrompts();
    debugLog('Quick prompt removed.', { index });
}

/**
 * Clears all messages from the chat history UI.
 */
export function clearMessages() {
    debugLog('Clearing all messages from the chat history.');

    const messageContainer = document.getElementById('messageHistory');
    if (messageContainer) {
        messageContainer.innerHTML = '';
        debugLog('Chat history cleared successfully.');
    }
}

/**
 * Attaches toolbar actions to a message element.
 */
function attachToolbarActions(messageDiv) {
    const persistentMessage = document.getElementById("persistentMessage");

    messageDiv.addEventListener("click", (event) => {
        const target = event.target.closest('button');
        if (!target) return;

        const action = target.getAttribute('aria-label');

        switch (action) {
            case 'Thumbs Up':
                debugLog('Thumbs up clicked.');
                break;
            case 'Thumbs Down':
                debugLog('Thumbs down clicked.');
                break;
            case 'Append to Persistent Message':
                appendToPersistentMessage(messageDiv, persistentMessage);
                break;
            case 'Edit Message':
                editMessage(messageDiv);
                break;
            case 'Copy Message':
                copyMessageToClipboard(messageDiv);
                break;
            case 'Delete Message':
                deleteMessage(messageDiv);
                break;
        }
    });
}

/**
 * Appends the content of a message to the persistent message area.
 */
function appendToPersistentMessage(messageDiv, persistentMessage) {
    const content = messageDiv.querySelector('span').innerText;
    const persistentMessageContent = persistentMessage.querySelector('.message span');
    if (persistentMessageContent) {
        persistentMessageContent.innerText = content;
    }
    debugLog('Message appended to persistent message area.', { content });
}

/**
 * Allows the user to edit a message.
 */
function editMessage(messageDiv) {
    const span = messageDiv.querySelector('span');
    const content = span.innerText;
    const newContent = prompt('Edit your message:', content);
    if (newContent !== null) {
        span.innerText = newContent;
        debugLog('Message edited successfully.', { newContent });
    }
}

/**
 * Copies a message's content to the clipboard.
 */
function copyMessageToClipboard(messageDiv) {
    const content = messageDiv.querySelector('span').innerText;
    navigator.clipboard.writeText(content).then(() => {
        alert('Message copied to clipboard!');
        debugLog('Message copied to clipboard.', { content });
    });
}

/**
 * Deletes a message from the chat history.
 */
function deleteMessage(messageDiv) {
    if (confirm('Are you sure you want to delete this message?')) {
        messageDiv.remove();
        debugLog('Message deleted successfully.');
    }
}
