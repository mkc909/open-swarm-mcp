import { initializeSidebar } from './sidebar.js';
import { initializeApplication } from './events.js';
import { initializeTheme } from './theme.js';
import { showToast } from './toast.js';

/**
 * Automatically replaces placeholders with all SVG icons.
 */
function replaceAllSVGs() {
    const placeholders = {
        "#uploadButton": "plus.svg",
        "#voiceRecordButton": "voice.svg",
        "#settingsToggleButton": "settings.svg",
        "#chatHistoryToggleButton": "chat_history.svg",
        "#newChatButton": "new_chat.svg",
        "#searchButton": "search.svg",
        "#logoutButton": "logout.svg",
        "#undoButton": "undo.svg",
        "#saveButton": "save.svg",
        "#thumbsUpButton": "thumbs_up.svg",
        "#thumbsDownButton": "thumbs_down.svg",
        "#trashButton": "trash.svg",
        "#attachButton": "attach.svg",
        "#visibleToggleButton": "visible.svg",
        "#notVisibleToggleButton": "not_visible.svg",
        "#runCodeButton": "run_code.svg",
        "#stopButton": "stop.svg",
        "#avatarButton": "avatar.svg",
        "#speakerButton": "speaker.svg",
    };

    Object.entries(placeholders).forEach(([selector, svgFile]) => {
        const element = document.querySelector(selector);
        if (element) {
            element.innerHTML = `
                <img src="/static/rest_mode/svg/${svgFile}" alt="${svgFile.replace('.svg', '')}" class="icon-svg" />
            `;
        } else {
            console.warn(`Element not found for selector: ${selector}`);
        }
    });
}

/**
 * Sets up a loading spinner for dynamic content.
 * @param {string} containerId - The ID of the container for the spinner.
 * @param {boolean} show - Whether to show or hide the spinner.
 */
export function toggleLoadingSpinner(containerId, show) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.warn(`Container not found for spinner: ${containerId}`);
        return;
    }

    if (show) {
        container.innerHTML = `
            <img src="/static/rest_mode/svg/animated_spinner.svg" alt="Loading..." class="spinner" />
        `;
    } else {
        container.innerHTML = ''; // Clear spinner
    }
}

/**
 * Sets up the chat history pane, including toggle visibility.
 */
function setupChatHistoryPane() {
    const chatHistoryPane = document.getElementById('chatHistoryPane');
    const minimizeButton = document.getElementById('leftSidebarHideBtn');

    if (!chatHistoryPane || !minimizeButton) {
        console.warn("Missing elements for chat history pane.");
        return;
    }

    minimizeButton.addEventListener('click', () => {
        const isVisible = chatHistoryPane.style.display !== 'none';
        chatHistoryPane.style.display = isVisible ? 'none' : 'block';
        showToast(isVisible ? "Chat history minimized." : "Chat history expanded.", "info");
    });

    chatHistoryPane.style.display = 'block'; // Ensure visible by default
}

/**
 * Initializes the settings toggle button functionality.
 */
function setupSettingsToggleButton() {
    const settingsToggleButton = document.getElementById('settingsToggleButton');
    const optionsPane = document.getElementById('optionsPane');

    if (settingsToggleButton && optionsPane) {
        settingsToggleButton.addEventListener('click', () => {
            const isVisible = optionsPane.style.display !== 'none';
            optionsPane.style.display = isVisible ? 'none' : 'block';
            showToast(isVisible ? "Settings pane hidden." : "Settings pane expanded.", "info");
        });
    } else {
        console.warn('Warning: Settings toggle button or options pane not found.');
    }
}

/**
 * Initializes all UI components and event listeners.
 */
export function initializeUI() {
    initializeSidebar();
    initializeApplication();
    initializeTheme();
    replaceAllSVGs(); // Replace all SVGs dynamically
    setupChatHistoryPane();
    setupSettingsToggleButton();
}

document.addEventListener('DOMContentLoaded', initializeUI);
