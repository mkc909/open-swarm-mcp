import {
    chatHistory,
    contextVariables,
    validateMessage,
    renderFirstUserMessage,
    populateBlueprintDropdown,
    handleLogout,
    handleUpload,
    handleVoiceRecord,
    debugLog,
} from './chatHandlers.js';
import { showToast } from './toast.js';
import { fetchBlueprints } from './blueprint.js';
import { renderMessage, appendRawMessage } from './messages.js';

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
    if (error) return;

    // Render the first assistant message if it's the first user message
    if (isFirstUserMessage) {
        renderFirstUserMessage();
    }

    // Render the user message in the UI
    renderMessage(userMessage.role, { content: userMessage.content }, userMessage.sender, userMessage.metadata);
    appendRawMessage(userMessage.role, { content: userMessage.content }, userMessage.sender, userMessage.metadata);

    showLoadingIndicator();

    try {
        const urlPath = window.location.pathname;
        const modelName = urlPath.split("/").filter(Boolean).pop() || "unknown_model";

        debugLog("Submitting message to model:", modelName);

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
 * Initializes the chat logic.
 */
export async function initializeChatLogic() {
    debugLog("Initializing chat logic.");
    try {
        const blueprints = await fetchBlueprints();
        populateBlueprintDropdown(blueprints);
    } catch (error) {
        showToast("⚠️ Failed to load blueprints.", "error");
        console.error("Error initializing blueprints:", error);
    }
}

/**
 * Handles chat deletion.
 * @param {HTMLElement} item - The chat item element to delete.
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
            method: "DELETE",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '',
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
 * Handles chat history item click.
 * @param {HTMLElement} item - The clicked chat history item.
 */
export function handleChatHistoryClick(item) {
    const chatName = item.firstChild.textContent.trim();
    showToast(`Selected: "${chatName}"`, "info");

    const chatHistoryItems = document.querySelectorAll(".chat-history-pane li");
    chatHistoryItems.forEach((i) => i.classList.remove("active"));
    item.classList.add("active");
}

// Initialize chat logic on DOMContentLoaded
document.addEventListener("DOMContentLoaded", initializeChatLogic);
