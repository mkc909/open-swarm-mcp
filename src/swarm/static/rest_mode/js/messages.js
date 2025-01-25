import { debugLog } from './debug.js';

/**
 * Renders a message into the UI.
 * @param {string} role - The role of the message sender ('user', 'assistant', etc.).
 * @param {Object} content - The content of the message (text or rich content).
 * @param {string} sender - The name of the sender.
 * @param {Object} metadata - Additional metadata for the message.
 */
export function renderMessage(role, content, sender, metadata) {
    const messageContainer = document.getElementById('messageHistory');
    if (!messageContainer) {
        debugLog('Message container not found.', { role, content, sender, metadata });
        return;
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.innerHTML = `
        <strong>${sender}:</strong> ${content.text || content.content}
    `;

    // Add metadata as a tooltip (if applicable)
    if (metadata && Object.keys(metadata).length) {
        messageDiv.title = JSON.stringify(metadata);
    }

    messageContainer.appendChild(messageDiv);
    debugLog('Message rendered.', { role, content, sender, metadata });
}

/**
 * Appends a raw message object into the chat UI.
 * @param {string} role - The role of the message sender.
 * @param {Object} content - The content of the message.
 * @param {string} sender - The sender's name.
 * @param {Object} metadata - Additional metadata.
 */
export function appendRawMessage(role, content, sender, metadata) {
    renderMessage(role, content, sender, metadata);

    // Scroll to the bottom of the message history
    const messageContainer = document.getElementById('messageHistory');
    if (messageContainer) {
        messageContainer.scrollTop = messageContainer.scrollHeight;
    }

    debugLog('Raw message appended.', { role, content, sender, metadata });
}