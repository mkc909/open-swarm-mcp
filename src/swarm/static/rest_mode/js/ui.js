import { initializeSidebar } from './sidebar.js';
import { initializeApplication } from './events.js';
import { initializeTheme } from './theme.js';
import { showToast } from './toast.js';

/**
 * Replaces placeholder emojis with corresponding SVG icons.
 */
function replaceEmojisWithSVGs() {
    const replacements = [
        { emoji: "➕", svgPath: "/static/rest_mode/svg/plus.svg", selector: "#uploadButton" },
        { emoji: "🎤", svgPath: "/static/rest_mode/svg/voice.svg", selector: "#voiceRecordButton" },
        { emoji: "⚙️", svgPath: "/static/rest_mode/svg/settings.svg", selector: "#settingsToggleButton" },
    ];

    replacements.forEach(({ emoji, svgPath, selector }) => {
        const button = document.querySelector(selector);
        if (button) {
            button.innerHTML = `
                <img src="${svgPath}" alt="${emoji}" class="icon-svg" />
            `;
        }
    });
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
    replaceEmojisWithSVGs();
    setupSettingsToggleButton();
}

/**
 * Sets up the chat history pane functionality, including minimize/maximize behavior.
 */
function setupChatHistoryPane() {
    const chatHistoryPane = document.getElementById('chatHistoryPane');
    const minimizeButton = document.getElementById('leftSidebarHideBtn'); // Ensure this button exists in the HTML

    if (!chatHistoryPane) {
        console.warn("Warning: 'chatHistoryPane' element not found.");
        return;
    }

    if (!minimizeButton) {
        console.warn("Warning: 'leftSidebarHideBtn' element not found.");
        return;
    }

    // Toggle chat history pane minimized class on button click
    minimizeButton.addEventListener('click', () => {
        chatHistoryPane.classList.toggle('minimized');
        const isMinimized = chatHistoryPane.classList.contains('minimized');
        showToast(isMinimized ? "Chat history minimized." : "Chat history restored.", "info");
    });
}
