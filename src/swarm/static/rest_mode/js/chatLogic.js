import { showToast } from './toast.js';
import { validateMessage } from './validation.js';
import { renderMessage, appendRawMessage } from './rendering.js';

/**
 * Manages the chat history and context variables.
 */
export let chatHistory = [];
export let contextVariables = { active_agent_name: null };

/**
 * Renders the first (assistant) message if none exists.
 */
export function renderFirstUserMessage() {
    const firstMessageExists = chatHistory.some(msg => msg.role === "user");
    if (!firstMessageExists) {
        const firstUserMessage = {
            role: "assistant",
            content: "Welcome to Open-Swarm Chat!",
            sender: "Assistant",
            metadata: {},
        };
        chatHistory.push(firstUserMessage);
        appendRawMessage(firstUserMessage.role, { content: firstUserMessage.content }, firstUserMessage.sender, firstUserMessage.metadata);

        const firstUserMessageDiv = document.getElementById("firstUserMessage");
        if (firstUserMessageDiv) {
            firstUserMessageDiv.innerHTML = `<strong>${firstUserMessage.sender}:</strong> ${firstUserMessage.content}`;
            firstUserMessageDiv.style.display = "block";
        }

        // Clear heading text to save space
        const chatHeading = document.getElementById('chatHeading');
        if (chatHeading) {
            chatHeading.innerHTML = "";
        }
    }
}

/**
 * Handles user message submission.
 */
export async function handleSubmit() {
    const userInput = document.getElementById("userInput");
    if (!userInput) return;

    const userMessageContent = userInput.value.trim();
    if (!userMessageContent) {
        showToast("❌ You cannot send an empty message.", "error");
        return;
    }

    // Clear input field
    userInput.value = "";

    const userMessage = {
        role: "user",
        content: userMessageContent,
        sender: "User",
        metadata: {},
    };
    chatHistory.push(userMessage);

    const isFirstUserMessage = chatHistory.filter(msg => msg.role === "user").length === 1;

    // Validate message
    const error = validateMessage(userMessage);
    if (error) return; // Toast shown from validateMessage

    // Render in UI
    if (isFirstUserMessage) {
        const firstUserMessageDiv = document.getElementById("firstUserMessage");
        if (firstUserMessageDiv) {
            firstUserMessageDiv.innerHTML = `<strong>${userMessage.sender}:</strong> ${userMessage.content}`;
            firstUserMessageDiv.style.display = "block";
        }
    } else {
        renderMessage(userMessage.role, { content: userMessage.content }, userMessage.sender, userMessage.metadata);
    }
    appendRawMessage(userMessage.role, { content: userMessage.content }, userMessage.sender, userMessage.metadata);

    if (!isFirstUserMessage) {
        const firstUserMessageDiv = document.getElementById("firstUserMessage");
        if (firstUserMessageDiv) {
            firstUserMessageDiv.style.display = "none";
        }
    }

    showLoadingIndicator();

    try {
        const urlPath = window.location.pathname;
        const modelName = urlPath.split("/").filter(Boolean).pop() || "unknown_model";

        console.log("Submitting message to model:", modelName);

        const response = await fetch("/v1/chat/completions", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '',
            },
            body: JSON.stringify({
                model: modelName,
                messages: chatHistory,
                context_variables: contextVariables,
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP Error: ${response.status}`);
        }

        const data = await response.json();
        processAssistantResponse(data.choices, data.context_variables);
    } catch (err) {
        console.error("Error submitting message:", err);
        showToast("⚠️ Error submitting message. Please try again.", "error");
    } finally {
        hideLoadingIndicator();
    }
}

/**
 * Processes the assistant's response.
 */
export function processAssistantResponse(choices, updatedContextVars) {
    if (!Array.isArray(choices)) {
        console.error("Invalid choices array:", choices);
        showToast("⚠️ Invalid response from server.", "error");
        return;
    }

    // Merge context variables
    contextVariables = { ...contextVariables, ...updatedContextVars };

    console.log("Processing assistant response with choices:", choices);

    choices.forEach(choice => {
        const rawMsg = { ...choice.message };
        chatHistory.push(rawMsg);

        const role = rawMsg.role || "assistant";
        const content = rawMsg.content ?? "No content";
        const sender = rawMsg.sender || (role === "user" ? "User" : "Assistant");
        const metadata = { ...rawMsg };

        console.log("Rendering message with:", { role, content, sender, metadata });

        // Avoid duplicating the first message
        if (chatHistory.length > 1) {
            renderMessage(role, { content }, sender, metadata);
        }
        appendRawMessage(role, { content }, sender, metadata);
    });

    console.log("Assistant response processed successfully.");
}

/**
 * Shows the loading indicator.
 */
export function showLoadingIndicator() {
    const loadingIndicator = document.getElementById("loadingIndicator");
    if (!loadingIndicator) return;

    loadingIndicator.style.display = 'flex';

    const container = document.querySelector('.container');
    const currentLayout = container?.getAttribute('data-theme-layout');

    if (currentLayout === 'mobile-layout') {
        loadingIndicator.innerHTML = `<p>Assistant is typing...</p>`;
    } else if (currentLayout === 'minimalist-layout') {
        loadingIndicator.innerHTML = `
            <div class="loader">
                <svg width="50" height="50" viewBox="0 0 120 30" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="15" cy="15" r="15" fill="var(--button-primary)">
                        <animate attributeName="r" from="15" to="15"
                            begin="0s" dur="0.8s"
                            values="15;9;15" calcMode="linear"
                            repeatCount="indefinite" />
                        <animate attributeName="fill-opacity" from="1" to="1"
                            begin="0s" dur="0.8s"
                            values="1;0.3;1" calcMode="linear"
                            repeatCount="indefinite" />
                    </circle>
                    <circle cx="60" cy="15" r="9" fill="var(--button-primary)" fill-opacity="0.3">
                        <animate attributeName="r" from="9" to="9"
                            begin="0.4s" dur="0.8s"
                            values="9;15;9" calcMode="linear"
                            repeatCount="indefinite" />
                        <animate attributeName="fill-opacity" from="0.3" to="0.3"
                            begin="0.4s" dur="0.8s"
                            values="0.3;1;0.3" calcMode="linear"
                            repeatCount="indefinite" />
                    </circle>
                    <circle cx="105" cy="15" r="15" fill="var(--button-primary)">
                        <animate attributeName="r" from="15" to="15"
                            begin="0.8s" dur="0.8s"
                            values="15;9;15" calcMode="linear"
                            repeatCount="indefinite" />
                        <animate attributeName="fill-opacity" from="1" to="1"
                            begin="0.8s" dur="0.8s"
                            values="1;0.3;1" calcMode="linear"
                            repeatCount="indefinite" />
                    </circle>
                </svg>
            </div>
        `;
    } else {
        // Default pulsating loader
        loadingIndicator.innerHTML = `
            <div class="loader">
                <svg width="50" height="50" viewBox="0 0 120 30" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="15" cy="15" r="15" fill="var(--button-primary)">
                        <animate attributeName="r" from="15" to="15"
                            begin="0s" dur="0.8s"
                            values="15;9;15" calcMode="linear"
                            repeatCount="indefinite" />
                        <animate attributeName="fill-opacity" from="1" to="1"
                            begin="0s" dur="0.8s"
                            values="1;0.3;1" calcMode="linear"
                            repeatCount="indefinite" />
                    </circle>
                    <circle cx="60" cy="15" r="9" fill="var(--button-primary)" fill-opacity="0.3">
                        <animate attributeName="r" from="9" to="9"
                            begin="0.4s" dur="0.8s"
                            values="9;15;9" calcMode="linear"
                            repeatCount="indefinite" />
                        <animate attributeName="fill-opacity" from="0.3" to="0.3"
                            begin="0.4s" dur="0.8s"
                            values="0.3;1;0.3" calcMode="linear"
                            repeatCount="indefinite" />
                    </circle>
                    <circle cx="105" cy="15" r="15" fill="var(--button-primary)">
                        <animate attributeName="r" from="15" to="15"
                            begin="0.8s" dur="0.8s"
                            values="15;9;15" calcMode="linear"
                            repeatCount="indefinite" />
                        <animate attributeName="fill-opacity" from="1" to="1"
                            begin="0.8s" dur="0.8s"
                            values="1;0.3;1" calcMode="linear"
                            repeatCount="indefinite" />
                    </circle>
                </svg>
            </div>
        `;
    }
}

/**
 * Hides the loading indicator.
 */
export function hideLoadingIndicator() {
    const loadingIndicator = document.getElementById("loadingIndicator");
    if (!loadingIndicator) return;

    loadingIndicator.style.display = 'none';
    loadingIndicator.innerHTML = '';
}

/**
 * Chat History item click handler.
 */
export function handleChatHistoryClick(item) {
    const chatName = item.firstChild.textContent.trim();
    showToast(`Selected: "${chatName}"`, "info");

    const chatHistoryItems = document.querySelectorAll('.chat-history-pane li');
    chatHistoryItems.forEach(i => i.classList.remove('active'));
    item.classList.add('active');
}

/**
 * Handles chat deletion.
 */
export async function handleDeleteChat(item) {
    const chatName = item.firstChild.textContent.trim();
    const chatId = item.getAttribute('data-chat-id');

    // Prevent deletion of the first user message
    if (item.classList.contains('first-user')) {
        showToast("❌ Cannot delete the first user message.", "error");
        return;
    }

    // Confirm deletion
    const confirmed = window.confirm(`Are you sure you want to delete "${chatName}"?`);
    if (!confirmed) {
        return;
    }

    try {
        const response = await fetch(`/v1/chat/delete/${chatId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '',
            },
        });
        if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
        item.remove();
        showToast(`✅ Chat "${chatName}" deleted.`, "success");
    } catch (err) {
        console.error("Error deleting chat:", err);
        showToast("❌ Error deleting chat. Please try again.", "error");
    }
}

/**
 * Handles user logout.
 */
export function handleLogout() {
    showToast("🚪 You have been logged out.", "info");
    window.location.href = "/login";
}

/**
 * Handles file upload.
 */
export function handleUpload() {
    showToast("➕ Upload feature is under development.", "info");
}

/**
 * Handles voice recording.
 */
export function handleVoiceRecord() {
    showToast("🎤 Voice recording is under development.", "info");
}
