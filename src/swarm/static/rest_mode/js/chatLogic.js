// src/swarm/static/rest_mode/js/chatLogic.js

/**
 * Centralizes chat logic by utilizing modular services.
 */

import { initializeBlueprints } from './modules/blueprintManager.js';
import { setupEventListeners } from './modules/eventHandlers.js';
import { debugLog } from './modules/debugLogger.js';
import { chatHistory, contextVariables } from './modules/state.js';

/**
 * Initializes the chat logic by setting up blueprints and event listeners.
 */
export async function initializeChatLogic() {
    debugLog('Initializing chat logic.');

    // Initialize blueprint management
    await initializeBlueprints();

    // Assuming you have a default model name or retrieve it from the UI
    const modelName = 'default_model'; // Replace with actual logic

    // Attach event listeners
    // Removed setupEventListeners call

    debugLog('Chat logic initialized.');
}

// Initialize chat logic on DOMContentLoaded
// document.addEventListener('DOMContentLoaded', initializeChatLogic);
