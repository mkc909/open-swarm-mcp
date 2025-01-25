import { showToast } from './toast.js';
import { fetchBlueprints } from './blueprint.js';
import { renderMessage, appendRawMessage } from './messages.js';

const DEBUG_MODE = true;

/**
 * Logs debug messages if debug mode is enabled.
 * @param {string} message - The message to log.
 * @param {any} data - Additional data to include in the log.
 */
export function debugLog(message, data = null) {
    if (DEBUG_MODE) {
        console.log(`[DEBUG] ${message}`, data);
    }
}

// Chat History and Context Variables
export let chatHistory = [];
export let contextVariables = { active_agent_name: null };

/**
 * Validates the user message.
 * @param {Object} message - The message object to validate.
 * @returns {string|null} - Error message if invalid, or null if valid.
 */
export function validateMessage(message) {
    if (!message.content || message.content.trim() === "") {
        showToast("❌ Message cannot be empty.", "error");
        return "Message cannot be empty.";
    }
    if (message.content.length > 500) {
        showToast("❌ Message too long. Please limit to 500 characters.", "error");
        return "Message too long.";
    }
    return null; // Valid message
}

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
export function populateBlueprintDropdown(blueprints) {
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
 * Updates the blueprint metadata section with the selected blueprint's details.
 * @param {Object} blueprint - The selected blueprint.
 */
export function updateBlueprintMetadata(blueprint) {
    const blueprintMetadata = document.getElementById('blueprintMetadata');
    if (!blueprintMetadata) return;

    blueprintMetadata.innerHTML = `
        <h2>${blueprint.title}</h2>
        <p>${blueprint.description}</p>
    `;
    debugLog('Updated blueprint metadata.', blueprint);
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
