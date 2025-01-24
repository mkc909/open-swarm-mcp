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
}
