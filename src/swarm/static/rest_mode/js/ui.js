import { initializeSidebar } from './sidebar.js';
import { initializeApplication } from './events.js';
import { initializeTheme } from './theme.js';
import { showToast } from './toast.js';

/**
 * Initializes all UI components and event listeners.
 * Should be called once during application startup.
 */
export function initializeUI() {
    initializeSidebar();
    initializeApplication();
    initializeTheme();
    setupChatHistoryPane();
}

/**
 * Sets up the chat history sidebar functionality, including minimize/maximize behavior.
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
