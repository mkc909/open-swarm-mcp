/**
 * Contains functions for rendering messages in the chat area,
 * and appending raw messages to the debug panel.
 */
const messageContainerId = "messageHistory";
const rawMessagesContainerId = "rawMessagesContent";

/**
 * Renders a single message in the chat.
 */
export function renderMessage(role, message, sender = "", metadata = {}, isFirstUser = false) {
    const messageHistory = document.getElementById(messageContainerId);
    if (!messageHistory) return;

    const containerDiv = document.createElement("div");
    containerDiv.classList.add("message", role);
    if (isFirstUser) containerDiv.classList.add("first-user");

    // For our special "plus" icon on hover (to persist the message), we wrap the messageContent in a container
    // Then on hover, show a small plus icon in the top-right corner
    let messageContent = `<strong>${sender}:</strong> ${message.content}`;
    
    // If role === "assistant" and layout is "minimalist", remove boxes, etc.
    const containerElement = document.querySelector('.container');
    if (role === "assistant" && containerElement?.getAttribute('data-theme-layout') === 'minimalist-layout') {
        messageContent = message.content;
    }

    containerDiv.innerHTML = `
      <div class="message-text">
        ${messageContent}
      </div>
      <span class="persist-icon" title="Persist this message to the pinned area">➕</span>
    `;

    // Add event listener on the plus icon
    const plusIcon = containerDiv.querySelector('.persist-icon');
    plusIcon?.addEventListener('click', (event) => {
        event.stopPropagation();
        persistMessage(role, message, sender);
    });

    messageHistory.appendChild(containerDiv);
    messageHistory.scrollTop = messageHistory.scrollHeight;
}

/**
 * Persists a message in the "first user message" container,
 * along with any other pinned messages.
 */
function persistMessage(role, message, sender = "") {
    const firstUserMessageDiv = document.getElementById("firstUserMessage");
    if (!firstUserMessageDiv) return;

    // We'll allow multiple pinned messages by just appending
    const pinned = document.createElement("div");
    pinned.classList.add("pinned-message");
    pinned.innerHTML = `<strong>${sender}:</strong> ${message.content}`;

    firstUserMessageDiv.style.display = "block";
    firstUserMessageDiv.appendChild(pinned);
}

/**
 * Appends raw message data to the Raw Messages pane.
 */
export function appendRawMessage(role, content, sender = "", metadata = {}) {
    const rawMessagesContent = document.getElementById(rawMessagesContainerId);
    if (!rawMessagesContent) return;

    const rawMessageDiv = document.createElement("div");
    rawMessageDiv.className = "raw-message";

    const rawData = {
        role,
        sender,
        content: content?.content || "No content provided.",
        metadata
    };

    const pre = document.createElement("pre");
    pre.textContent = JSON.stringify(rawData, null, 2);
    rawMessageDiv.appendChild(pre);

    rawMessagesContent.appendChild(rawMessageDiv);
    rawMessagesContent.scrollTop = rawMessagesContent.scrollHeight;
}
