import { showToast } from './toast.js';
import { renderMessage, appendRawMessage } from './messages.js';

const DEBUG_MODE = true;
let blueprints = [];
let blueprintName = '';
let blueprintMetadata = '';

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

/**
 * Validates the user message.
 * @param {Object} message - The message object to validate.
 * @returns {string|null} - Error message if invalid, or null if valid.
 */
export function validateMessage(message) {
    if (!message.content || message.content.trim() === '') {
        showToast('❌ Message cannot be empty.', 'error');
        return 'Message cannot be empty.';
    }
    if (message.content.length > 5000) {
        showToast('❌ Message too long. Please limit to 5000 characters.', 'error');
        return 'Message too long.';
    }
    return null; // Valid message
}

/**
 * Fetches and renders blueprint metadata from /v1/models/.
 */
export async function fetchBlueprintMetadata() {
    try {
        const response = await fetch('/v1/models/');
        if (!response.ok) throw new Error('Failed to fetch metadata.');

        const data = await response.json();
        blueprints = data.data || [];
        if (blueprints.length === 0) throw new Error('No blueprints available.');

        // Set default blueprint
        const defaultBlueprint = blueprints[0];
        blueprintName = defaultBlueprint.title;
        blueprintMetadata = defaultBlueprint.description;

        // Post blueprint metadata as an Assistant message
        appendRawMessage(
            'assistant',
            {
                content: `Blueprint loaded: <strong>${blueprintName}</strong><br>${blueprintMetadata}`,
            },
            'Assistant'
        );

        populateBlueprintDialog(blueprints); // Populate blueprint dialog options
    } catch (error) {
        console.error('Error fetching blueprint metadata:', error);

        // Add fallback messages for errors
        appendRawMessage(
            'assistant',
            {
                content:
                    'Could not retrieve blueprint metadata. Check out the troubleshooting guide at <a href="https://github.com/matthewhand/open-swarm/TROUBLESHOOTING.md">Troubleshooting Guide</a>.',
            },
            'Assistant'
        );
    }
}

/**
 * Populates the blueprint selection dialog.
 * @param {Array} blueprints - The list of blueprints fetched from the API.
 */
function populateBlueprintDialog(blueprints) {
    const blueprintDialogElement = document.getElementById('blueprintDialog');
    if (!blueprintDialogElement) {
        console.warn('Blueprint dialog element not found.');
        return;
    }

    blueprintDialogElement.innerHTML = blueprints
        .map(
            (bp) => `
        <div class="blueprint-option" data-id="${bp.id}">
            <p class="blueprint-title">${bp.title}</p>
            <p class="blueprint-description">${bp.description}</p>
        </div>`
        )
        .join('');

    // Add click event for each blueprint option
    document.querySelectorAll('.blueprint-option').forEach((option) => {
        option.addEventListener('click', () => {
            const selectedId = option.getAttribute('data-id');
            const selectedBlueprint = blueprints.find((bp) => bp.id === selectedId);
            if (selectedBlueprint) {
                selectBlueprint(selectedBlueprint);
            }
        });
    });
}

/**
 * Updates the UI and metadata when a blueprint is selected.
 * @param {Object} blueprint - The selected blueprint.
 */
function selectBlueprint(blueprint) {
    blueprintName = blueprint.title;
    blueprintMetadata = blueprint.description;

    // Post updated blueprint metadata
    appendRawMessage(
        'assistant',
        {
            content: `Blueprint loaded: <strong>${blueprintName}</strong><br>${blueprintMetadata}`,
        },
        'Assistant'
    );

    // Hide the blueprint dialog
    const blueprintDialogElement = document.getElementById('blueprintDialog');
    if (blueprintDialogElement) {
        blueprintDialogElement.classList.add('hidden');
    }
}

/**
 * Handles user logout.
 */
export function handleLogout() {
    showToast('🚪 You have been logged out.', 'info');
    window.location.href = '/login';
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
    showToast(`Selected: "${chatName}"`, 'info');

    const chatHistoryItems = document.querySelectorAll('.chat-history-pane li');
    chatHistoryItems.forEach((i) => i.classList.remove('active'));
    item.classList.add('active');
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
        showToast('❌ Cannot delete the first user message.', 'error');
        return;
    }

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
        showToast(`✅ Chat "${chatName}" deleted.`, 'success');
    } catch (err) {
        console.error('Error deleting chat:', err);
        showToast('❌ Error deleting chat. Please try again.', 'error');
    }
}
