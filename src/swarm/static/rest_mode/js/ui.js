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
    setupSidebar();
}

/**
 * Sets up the sidebar functionality, including minimize/maximize behavior.
 */
function setupSidebar() {
    const chatSidebar = document.getElementById('chatSidebar');
    const minimizeButton = document.getElementById('minimizeSidebarButton'); // Ensure this button exists in the HTML

    if (!chatSidebar) {
        console.warn("Warning: 'chatSidebar' element not found.");
        return;
    }

    if (!minimizeButton) {
        console.warn("Warning: 'minimizeSidebarButton' element not found.");
        return;
    }

    // Toggle sidebar minimized class on button click
    minimizeButton.addEventListener('click', () => {
        chatSidebar.classList.toggle('minimized');
        const isMinimized = chatSidebar.classList.contains('minimized');
        showToast(isMinimized ? "Sidebar minimized." : "Sidebar restored.", "info");
    });
}
