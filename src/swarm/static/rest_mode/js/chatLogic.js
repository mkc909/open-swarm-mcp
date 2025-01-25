import { showToast } from './toast.js';
import { fetchBlueprints } from './blueprint.js';
import { renderMessage, appendRawMessage } from './messages.js';

const DEBUG_MODE = true;

/**
 * Logs debug messages if debug mode is enabled.
 * @param {string} message - The message to log.
 * @param {any} data - Additional data to include in the log.
 */
function debugLog(message, data = null) {
    if (DEBUG_MODE) {
        console.log(`[DEBUG] ${message}`, data);
    }
}

// Chat History and Context Variables
export let chatHistory = [];
export let contextVariables = { active_agent_name: null };

/**
 * Renders the first (assistant) message if none exists.
 */
export function renderFirstUserMessage() {
    const firstMessageExists = chatHistory.some((msg) => msg.role === 'user');
    if (!firstMessageExists) {
        const firstUserMessage = {
            role: 'assistant',
            content: 'Welcome to Open-Swarm Chat!',
            sender: 'Assistant',
            metadata: {},
        };
        chatHistory.push(firstUserMessage);
        appendRawMessage(
            firstUserMessage.role,
            { content: firstUserMessage.content },
            firstUserMessage.sender,
            firstUserMessage.metadata
        );
    }
}

/**
 * Populates the blueprint dropdown and updates the metadata for the selected blueprint.
 * @param {Array} blueprints - The list of blueprints fetched from the API.
 */
function populateBlueprintDropdown(blueprints) {
    const blueprintDropdown = document.getElementById('blueprintDropdown');
    const blueprintMetadata = document.getElementById('blueprintMetadata');

    if (!blueprintDropdown || !blueprintMetadata) {
        console.warn('Blueprint dropdown or metadata element not found.');
        return;
    }

    // Populate the dropdown
    blueprintDropdown.innerHTML = blueprints
        .map((bp) => `<option value="${bp.id}">${bp.title}</option>`)
        .join('');

    // Get the current blueprint from the URI
    const currentBlueprintId = window.location.pathname.split('/').filter(Boolean).pop();
    const defaultBlueprint = blueprints.find((bp) => bp.id === currentBlueprintId) || blueprints[0];

    // Set the default selection and update metadata
    blueprintDropdown.value = defaultBlueprint.id;
    updateBlueprintMetadata(defaultBlueprint);

    // Add event listener for dropdown changes
    blueprintDropdown.addEventListener('change', (e) => {
        const selectedBlueprint = blueprints.find((bp) => bp.id === e.target.value);
        if (selectedBlueprint) {
            updateBlueprintMetadata(selectedBlueprint);
        }
    });
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
 * Updates the blueprint metadata section with the selected blueprint's details.
 * @param {Object} blueprint - The selected blueprint.
 */
function updateBlueprintMetadata(blueprint) {
    const blueprintMetadata = document.getElementById('blueprintMetadata');
    if (!blueprintMetadata) return;

    blueprintMetadata.innerHTML = `
        <h2>${blueprint.title}</h2>
        <p>${blueprint.description}</p>
    `;
    debugLog('Updated blueprint metadata.', blueprint);
}

/**
 * Chat History item click handler.
 */
export function handleChatHistoryClick(item) {
    const chatName = item.firstChild.textContent.trim();
    showToast(`Selected: "${chatName}"`, 'info');

    const chatHistoryItems = document.querySelectorAll('.chat-history-pane li');
    chatHistoryItems.forEach((i) => i.classList.remove('active'));
    item.classList.add('active');
}

// Initialize the application
document.addEventListener('DOMContentLoaded', async () => {
    debugLog('Initializing chat logic.');
    try {
        const blueprints = await fetchBlueprints();
        populateBlueprintDropdown(blueprints);
    } catch (error) {
        showToast('⚠️ Failed to load blueprints.', 'error');
        console.error('Error initializing blueprints:', error);
    }
});


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
    showToast('➕ Upload feature is under development.', 'info');
}

/**
 * Handles voice recording.
 */
export function handleVoiceRecord() {
    showToast('🎤 Voice recording is under development.', 'info');
}
