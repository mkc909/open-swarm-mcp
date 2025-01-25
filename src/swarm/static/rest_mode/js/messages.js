import { debugLog } from './debug.js';

/**
 * Renders a message into the UI.
 * @param {string} role - The role of the message sender ('user', 'assistant', etc.).
 * @param {Object} content - The content of the message (text or rich content).
 * @param {string} sender - The name of the sender.
 * @param {Object} metadata - Additional metadata for the message.
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
            <button class="toolbar-btn" aria-label="Append to Persistent Message">
                <img src="/static/rest_mode/svg/plus.svg" alt="Plus Icon" class="icon-svg" />
            </button>
            <button class="toolbar-btn" aria-label="Edit Message">
                <img src="/static/rest_mode/svg/edit.svg" alt="Edit Icon" class="icon-svg" />
            </button>
            <button class="toolbar-btn" aria-label="Copy Message">
                <img src="/static/rest_mode/svg/copy.svg" alt="Copy Icon" class="icon-svg" />
            </button>
            <button class="toolbar-btn" aria-label="Delete Message">
                <img src="/static/rest_mode/svg/trash.svg" alt="Trash Icon" class="icon-svg" />
            </button>
            <button class="toolbar-btn" aria-label="Thumbs Up">
                <img src="/static/rest_mode/svg/thumbs_up.svg" alt="Thumbs Up Icon" class="icon-svg" />
            </button>
            <button class="toolbar-btn" aria-label="Thumbs Down">
                <img src="/static/rest_mode/svg/thumbs_down.svg" alt="Thumbs Down Icon" class="icon-svg" />
            </button>
        </div>
    `;

    // Add metadata as a tooltip (if applicable)
    if (metadata && Object.keys(metadata).length) {
        messageDiv.title = JSON.stringify(metadata, null, 2);
    }

    messageContainer.appendChild(messageDiv);
    debugLog('Message rendered successfully.', { role, content, sender, metadata });

    // Attach toolbar functionality
    attachToolbarActions(messageDiv);
}

/**
 * Appends a raw message object into the chat UI.
 * @param {string} role - The role of the message sender.
 * @param {Object} content - The content of the message.
 * @param {string} sender - The sender's name.
 * @param {Object} metadata - Additional metadata.
 */
export function appendRawMessage(role, content, sender, metadata) {
    debugLog('Appending raw message...', { role, content, sender, metadata });

    renderMessage(role, content, sender, metadata);

    // Scroll to the bottom of the message history
    const messageContainer = document.getElementById('messageHistory');
    if (messageContainer) {
        messageContainer.scrollTop = messageContainer.scrollHeight;
        debugLog('Scrolled to the bottom of the message history.');
    } else {
        debugLog('Message container not found while appending raw message.', { role, content, sender, metadata });
    }
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
    } else {
        debugLog('Message container not found while clearing messages.');
    }
}

/**
 * Attaches toolbar actions to a message element.
 * @param {HTMLElement} messageDiv - The message element to attach toolbar actions to.
 */
function attachToolbarActions(messageDiv) {
    const persistentMessage = document.getElementById("persistentMessage");

    messageDiv.addEventListener("click", (event) => {
        const target = event.target.closest("button");
        if (!target) return;

        const action = target.getAttribute("aria-label");

        switch (action) {
            case "Append to Persistent Message":
                appendToPersistentMessage(messageDiv, persistentMessage);
                break;
            case "Edit Message":
                editMessage(messageDiv);
                break;
            case "Copy Message":
                copyMessageToClipboard(messageDiv);
                break;
            case "Delete Message":
                deleteMessage(messageDiv);
                break;
            default:
                debugLog(`Unknown action: ${action}`);
        }
    });
}

/**
 * Appends the content of a message to the persistent message area.
 * @param {HTMLElement} messageDiv - The message element.
 * @param {HTMLElement} persistentMessage - The persistent message area.
 */
function appendToPersistentMessage(messageDiv, persistentMessage) {
    const content = messageDiv.querySelector("span").innerText;
    const persistentMessageContent = persistentMessage.querySelector(".message span");
    if (persistentMessageContent) {
        persistentMessageContent.innerText = content;
    }
    debugLog("Message appended to persistent message area.", { content });
}

/**
 * Allows the user to edit a message.
 * @param {HTMLElement} messageDiv - The message element.
 */
function editMessage(messageDiv) {
    const span = messageDiv.querySelector("span");
    const content = span.innerText;
    const newContent = prompt("Edit your message:", content);
    if (newContent !== null) {
        span.innerText = newContent;
        debugLog("Message edited successfully.", { newContent });
    }
}

/**
 * Copies a message's content to the clipboard.
 * @param {HTMLElement} messageDiv - The message element.
 */
function copyMessageToClipboard(messageDiv) {
    const content = messageDiv.querySelector("span").innerText;
    navigator.clipboard.writeText(content).then(() => {
        alert("Message copied to clipboard!");
        debugLog("Message copied to clipboard.", { content });
    });
}

/**
 * Deletes a message from the chat history.
 * @param {HTMLElement} messageDiv - The message element.
 */
function deleteMessage(messageDiv) {
    if (confirm("Are you sure you want to delete this message?")) {
        messageDiv.remove();
        debugLog("Message deleted successfully.");
    }
}
