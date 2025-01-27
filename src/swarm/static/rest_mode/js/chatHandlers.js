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
        // showToast('❌ Message cannot be empty.', 'error');
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
    const blueprintMetadataElement = document.getElementById('blueprintMetadata');
    const persistentMessageElement = document.getElementById('firstUserMessage');
    const blueprintDropdown = document.getElementById('blueprintDropdown');

    // Check if the elements exist
    if (!blueprintMetadataElement || !persistentMessageElement || !blueprintDropdown) {
        console.error("Error: Required DOM elements not found.");
        return;
    }

    // Timeout messages
    setTimeout(() => {
        if (!blueprintName) {
            appendRawMessage(
                'assistant',
                {
                    content: 'Waiting for blueprint to download...',
                },
                'Assistant'
            );
        }
    }, 3000);

    setTimeout(() => {
        if (!blueprintName) {
            appendRawMessage(
                'assistant',
                {
                    content:
                        'Could not retrieve blueprint metadata. Check out the troubleshooting guide at <a href="https://github.com/matthewhand/open-swarm/TROUBLESHOOTING.md">Troubleshooting Guide</a>.',
                },
                'Assistant'
            );
        }
    }, 8000);

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

        // Update UI
        blueprintMetadataElement.innerHTML = `<h2>${blueprintName}</h2>`;
        persistentMessageElement.innerHTML = `<h2>${blueprintName}</h2><p>${blueprintMetadata}</p>`;

        // appendRawMessage(
        //     'assistant',
        //     {
        //         content: `Blueprint loaded: ${blueprintName}`,
        //     },
        //     'Assistant'
        // );

        populateBlueprintDialog(blueprints); // Populate blueprint dialog and dropdown
    } catch (error) {
        console.error('Error fetching blueprint metadata:', error);

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
 * Populates the blueprint selection dialog and dropdown.
 * @param {Array} blueprints - The list of blueprints fetched from the API.
 */
function populateBlueprintDialog(blueprints) {
    const blueprintDialogElement = document.getElementById('blueprintDialog');
    const blueprintDropdown = document.getElementById('blueprintDropdown');
    const currentPath = window.location.pathname; // Get the current URL path

    if (!blueprintDialogElement || !blueprintDropdown) {
        console.warn('Blueprint dialog or dropdown element not found.');
        return;
    }

    // Populate dialog
    blueprintDialogElement.innerHTML = blueprints
        .map(
            (bp) => `
        <div class="blueprint-option" data-id="${bp.id}">
            <p class="blueprint-title">${bp.title}</p>
            <p class="blueprint-description">${bp.description}</p>
        </div>`
        )
        .join('');

    // Populate dropdown
    blueprintDropdown.innerHTML = blueprints
        .map(
            (bp) => `
        <option value="${bp.id}">${bp.title}</option>`
        )
        .join('');

    // Find the blueprint matching the current path
    const matchedBlueprint = blueprints.find((bp) =>
        currentPath.includes(bp.route) // Assuming each blueprint has a `route` property
    );

    // Set the default dropdown value
    if (matchedBlueprint) {
        blueprintDropdown.value = matchedBlueprint.id; // Set the dropdown value
        selectBlueprint(matchedBlueprint); // Select the blueprint by default
    }

    // Add click event for each dialog option
    document.querySelectorAll('.blueprint-option').forEach((option) => {
        option.addEventListener('click', () => {
            const selectedId = option.getAttribute('data-id');
            const selectedBlueprint = blueprints.find((bp) => bp.id === selectedId);
            if (selectedBlueprint) {
                selectBlueprint(selectedBlueprint);
            }
        });
    });

    // Add change event for dropdown
    blueprintDropdown.addEventListener('change', (event) => {
        const selectedId = event.target.value;
        const selectedBlueprint = blueprints.find((bp) => bp.id === selectedId);
        if (selectedBlueprint) {
            selectBlueprint(selectedBlueprint);
        }
    });
}

/**
 * Updates the UI and metadata when a blueprint is selected.
 * @param {Object} blueprint - The selected blueprint.
 */
function selectBlueprint(blueprint) {
    const blueprintMetadataElement = document.getElementById('blueprintMetadata');
    const blueprintDialogElement = document.getElementById('blueprintDialog');
    const persistentMessageElement = document.getElementById('firstUserMessage');

    blueprintName = blueprint.title;
    blueprintMetadata = blueprint.description;

    // Update UI
    blueprintMetadataElement.innerHTML = `<h2>${blueprintName}</h2>`;
    persistentMessageElement.innerHTML = `<h2>${blueprintName}</h2><p>${blueprintMetadata}</p>`;

    // appendRawMessage(
    //     'assistant',
    //     {
    //         content: `Blueprint loaded: ${blueprintName}`,
    //     },
    //     'Assistant'
    // );

    // Hide the blueprint dialog
    blueprintDialogElement?.classList.add('hidden');
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
document.addEventListener('DOMContentLoaded', function () {
    const chatPane = document.getElementById('chatPane');
    const scrollIndicator = document.getElementById('scrollIndicator');
    const autoScrollToggle = document.getElementById('autoScrollToggle');
    let autoScrollEnabled = true;

    // Initialize auto-scroll toggle
    if (autoScrollToggle) {
        autoScrollToggle.checked = autoScrollEnabled; // Default state
        autoScrollToggle.addEventListener('change', function () {
            autoScrollEnabled = this.checked;
            showToast(`Auto scroll ${autoScrollEnabled ? 'enabled' : 'disabled'}`, 'info');
        });
    }

    // Handle new messages
    function handleNewMessage() {
        if (autoScrollEnabled && chatPane) {
            chatPane.scrollTop = chatPane.scrollHeight; // Scroll to bottom
        }
    }

    // Show or hide scroll indicator
    function updateScrollIndicator() {
        if (chatPane.scrollHeight - chatPane.scrollTop > chatPane.clientHeight + 50) {
            scrollIndicator.classList.remove('hidden');
            scrollIndicator.classList.add('visible');
        } else {
            scrollIndicator.classList.add('hidden');
            scrollIndicator.classList.remove('visible');
        }
    }

    // Scroll to bottom on click
    if (scrollIndicator) {
        scrollIndicator.addEventListener('click', function () {
            chatPane.scrollTop = chatPane.scrollHeight;
        });
    }

    // Add scroll listener to chat pane
    if (chatPane) {
        chatPane.addEventListener('scroll', updateScrollIndicator);
    }

    // Simulate message addition
    setInterval(() => {
        // Example: Simulate adding a message
        const message = document.createElement('div');
        message.textContent = `Message at ${new Date().toLocaleTimeString()}`;
        // TODO fix
        // chatPane.appendChild(message);
        handleNewMessage();
    }, 5000); // Simulates a new message every 5 seconds
});
