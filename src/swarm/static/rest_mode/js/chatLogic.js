import {
    chatHistory,
    validateMessage,
    fetchBlueprintMetadata,
    handleLogout,
    handleUpload,
    handleVoiceRecord,
    debugLog,
} from './chatHandlers.js';
import { showToast } from './toast.js';
import { renderMessage, appendRawMessage } from './messages.js';
import { showLoadingIndicator, hideLoadingIndicator } from './ui.js';

export let contextVariables = { active_agent_name: null };

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

    choices.forEach((choice) => {
        const rawMessage = { ...choice.message }; // Store the raw message
        chatHistory.push(rawMessage);

        const role = rawMessage.role || "assistant";
        const content = rawMessage.content ?? "No content"; // Ensure fallback
        const sender = rawMessage.sender || (role === "user" ? "User" : "Assistant");
        const metadata = { ...rawMessage };

        console.log("Rendering message with:", { role, content, sender, metadata });

        // Render and log messages
        renderMessage(role, { content }, sender, metadata);
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

    const isFirstUserMessage = chatHistory.filter((msg) => msg.role === "user").length === 1;

    // Validate the message
    const error = validateMessage(userMessage);
    if (error) return;

    // Render the user message in the UI
    renderMessage(userMessage.role, { content: userMessage.content }, userMessage.sender, userMessage.metadata);
    appendRawMessage(userMessage.role, { content: userMessage.content }, userMessage.sender, userMessage.metadata);

    // If it's the first user message, update the persistent message
    if (isFirstUserMessage) {
        const persistentMessageElement = document.getElementById('firstUserMessage');
        persistentMessageElement.innerHTML = `<p>${userMessageContent}</p>`;
        debugLog("Persistent message updated with the first user message.");
    }

    showLoadingIndicator(); // Show loading spinner

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
        hideLoadingIndicator(); // Hide loading spinner
    }
}

/**
 * Initializes the chat logic.
 * Fetches blueprint metadata and sets up the initial UI state.
 */
export async function initializeChatLogic() {
    debugLog("Initializing chat logic.");
    try {
        // Fetch blueprint metadata and populate UI
        await fetchBlueprintMetadata();
    } catch (error) {
        showToast("⚠️ Failed to load blueprint metadata.", "error");
        console.error("Error initializing blueprint metadata:", error);
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
    chatHistoryItems.forEach((i) => i.classList.remove("active"));
    item.classList.add("active");
}

// Initialize chat logic on DOMContentLoaded
document.addEventListener("DOMContentLoaded", initializeChatLogic);
