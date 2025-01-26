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
// import { showLoadingIndicator, hideLoadingIndicator } from './ui.js';


/**
 * Processes the assistant's response and updates context variables.
 * @param {Array} choices - The choices from the assistant's response.
 * @param {object} updatedContextVariables - Updated context variables from the server.
 */
function processAssistantResponse(choices, updatedContextVariables) {
    if (!choices || !Array.isArray(choices)) {
        console.error("Invalid choices array:", choices);
        showToast("⚠️ Invalid response from server.", "error");
        return;
    }

    // Update the local context variables
    contextVariables = { ...contextVariables, ...updatedContextVariables };

    console.log("Processing assistant response with choices:", choices);

    choices.forEach(choice => {
        const rawMessage = { ...choice.message }; // Store the raw message
        chatHistory.push(rawMessage);

        const role = rawMessage.role || "assistant";
        const content = rawMessage.content ?? "No content"; // Ensure fallback
        const sender = rawMessage.sender || (role === "user" ? "User" : "Assistant");
        const metadata = { ...rawMessage };

        console.log("Rendering message with:", { role, content, sender, metadata });

        // Render and log messages
        if (chatHistory.length > 1) { // Avoid duplicating the first message
            renderMessage(role, { content }, sender, metadata);
        }
        appendRawMessage(role, { content }, sender, metadata);

        // If Debug pane is active, render relevant debug info
        const debugPane = document.getElementById("debugPane");
        if (debugPane && debugPane.style.display === 'block') {
            renderRelevantDebugInfo();
        }
    });

    console.log("Assistant response processed successfully.");
}

/**
 * Handles user message submission.
 * Validates the input, updates the UI, and sends the message to the server.
 */
export async function handleSubmit() {
    const userInput = document.getElementById("userInput");
    if (!userInput) {
        debugLog("User input element not found.");
        return;
    }

    const userMessageContent = userInput.value.trim();
    if (!userMessageContent) {
        showToast("❌ You cannot send an empty message.", "error");
        debugLog("Empty message submission blocked.");
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
    debugLog("User message added to chat history.", userMessage);

    const isFirstUserMessage = chatHistory.filter(msg => msg.role === "user").length === 1;

    // Validate the message
    const error = validateMessage(userMessage);
    if (error) return;

    // Render the first assistant message if it's the first user message
    if (isFirstUserMessage) {
        renderFirstUserMessage();
        debugLog("First user message detected, rendering welcome message.");
    }

    // Render the user message in the UI
    renderMessage(userMessage.role, { content: userMessage.content }, userMessage.sender, userMessage.metadata);
    appendRawMessage(userMessage.role, { content: userMessage.content }, userMessage.sender, userMessage.metadata);

    // TODO
    // showLoadingIndicator(); // Show loading spinner

    try {
        const urlPath = window.location.pathname;
        const modelName = urlPath.split("/").filter(Boolean).pop() || "unknown_model";
        debugLog("Submitting message to model.", { modelName, message: userMessageContent });

        const response = await fetch("/v1/chat/completions", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": document.querySelector('meta[name="csrf-token"]')?.getAttribute("content") || "",
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
        debugLog("Message successfully processed by the model.", data);
        processAssistantResponse(data.choices, data.context_variables);
    } catch (err) {
        console.error("Error submitting message:", err);
        showToast("⚠️ Error submitting message. Please try again.", "error");
    } finally {
        //TODO
        // hideLoadingIndicator(); // Hide loading spinner
        pass
    }
}

/**
 * Initializes the chat logic.
 * Fetches blueprints and sets up the initial UI state.
 */
export async function initializeChatLogic() {
    debugLog("Initializing chat logic.");
    try {
        const blueprints = await fetchBlueprints();
        debugLog("Blueprints fetched successfully.", blueprints);
        populateBlueprintDropdown(blueprints);
    } catch (error) {
        showToast("⚠️ Failed to load blueprints.", "error");
        console.error("Error initializing blueprints:", error);
    }
}

/**
 * Handles chat deletion.
 * Confirms the action and removes the selected chat from the UI.
 * @param {HTMLElement} item - The chat item element to delete.
 */
export async function handleDeleteChat(item) {
    const chatName = item.firstChild.textContent.trim();
    const chatId = item.getAttribute('data-chat-id');
    debugLog("Attempting to delete chat.", { chatName, chatId });

    // Prevent deletion of the first user message
    if (item.classList.contains('first-user')) {
        showToast("❌ Cannot delete the first user message.", "error");
        debugLog("Deletion blocked for the first user message.");
        return;
    }

    // Confirm deletion
    const confirmed = window.confirm(`Are you sure you want to delete "${chatName}"?`);
    if (!confirmed) {
        debugLog("Deletion cancelled by user.");
        return;
    }

    try {
        const response = await fetch(`/v1/chat/delete/${chatId}`, {
            method: "DELETE",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": document.querySelector('meta[name="csrf-token"]')?.getAttribute("content") || "",
            },
        });

        if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
        item.remove();
        showToast(`✅ Chat "${chatName}" deleted.`, "success");
        debugLog("Chat deleted successfully.", { chatName });
    } catch (err) {
        console.error("Error deleting chat:", err);
        showToast("❌ Error deleting chat. Please try again.", "error");
    }
}

/**
 * Handles chat history item click.
 * Highlights the selected chat and updates the UI.
 * @param {HTMLElement} item - The clicked chat history item.
 */
export function handleChatHistoryClick(item) {
    const chatName = item.firstChild.textContent.trim();
    showToast(`Selected: "${chatName}"`, "info");
    debugLog("Chat history item clicked.", { chatName });

    const chatHistoryItems = document.querySelectorAll(".chat-history-pane li");
    chatHistoryItems.forEach(i => i.classList.remove("active"));
    item.classList.add("active");
}

// Initialize chat logic on DOMContentLoaded
document.addEventListener("DOMContentLoaded", initializeChatLogic);
