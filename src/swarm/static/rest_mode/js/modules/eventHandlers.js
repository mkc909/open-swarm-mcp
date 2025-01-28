// src/swarm/static/rest_mode/js/modules/eventHandlers.js

import { handleLogout } from '../auth.js';
import { toggleDebugPane, handleTechSupport } from '../debug.js';
import { toggleSidebar } from '../sidebar.js';

import { handleChatHistoryClick } from './chatHistory.js';
import { deleteChat } from './apiService.js';
import { handleUpload, handleVoiceRecord } from './userInteractions.js';
import { fetchBlueprintMetadata } from './apiService.js';
import { handleSubmit } from './messageProcessor.js';
import { showToast } from '../toast.js';
import { debugLog } from './debugLogger.js';

/**
 * Handles "Search" button click.
 */
function handleSearch() {
    showToast("🔍 Search feature is under development.", "info");
}

/**
 * Handles "New Chat" button click.
 */
function handleNewChat() {
    showToast("📝 Starting a new chat...", "info");
    // Implement new chat functionality as needed
}

/**
 * Attaches event listeners to chat history items.
 */
function setupChatHistoryListeners() {
    const chatHistoryItems = document.querySelectorAll('.chat-history-pane li');
    chatHistoryItems.forEach((item) => {
        item.removeEventListener('click', () => handleChatHistoryClick(item));
        item.addEventListener('click', () => handleChatHistoryClick(item));

        const trashCan = item.querySelector('.trash-can');
        if (trashCan) {
            trashCan.addEventListener('click', (e) => {
                e.stopPropagation();
                deleteChat(item);
            });
        }
    });
}

/**
 * Attaches event listeners to main application buttons and elements.
 */
function setupGlobalEventListeners() {
    // Sidebar toggles
    document.getElementById("settingsToggleButton")?.removeEventListener('click', () => toggleSidebar('options', true));
    document.getElementById("settingsToggleButton")?.addEventListener('click', () => toggleSidebar('options', true));
    document.getElementById("optionsSidebarHideBtn")?.addEventListener('click', () => toggleSidebar('options', false));
    // Removed event listeners for chatHistoryToggleButton and leftSidebarHideBtn

    // Top buttons
    // document.getElementById("searchButton")?.addEventListener('click', handleSearch);
    document.getElementById("newChatButton")?.addEventListener('click', handleNewChat);

    // Functional buttons
    document.getElementById("logoutButton")?.addEventListener('click', handleLogout);
    document.getElementById("uploadButton")?.addEventListener('click', handleUpload);
    document.getElementById("voiceRecordButton")?.addEventListener('click', handleVoiceRecord);
    document.getElementById("submitButton")?.addEventListener("click", handleSubmit); // Attached here

    // User input submission with Enter key
    const userInput = document.getElementById("userInput");
    userInput?.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            handleSubmit();
        }
    });

    // Debug pane toggles
    document.getElementById("debugButton")?.addEventListener('click', toggleDebugPane);
    document.getElementById("techSupportButtonInsideDebug")?.addEventListener('click', handleTechSupport);
}

/**
 * Sets up all event listeners for the application.
 */
let eventListenersInitialized = false;

export function setupEventListeners() {
    if (eventListenersInitialized) {
        debugLog('Event listeners are already initialized.');
        return;
    }

    setupGlobalEventListeners();
    setupChatHistoryListeners();
    debugLog('All event listeners have been set up.');
    eventListenersInitialized = true;
}

/**
 * Initialize the application.
 */
export function initializeApplication() {
    debugLog('[DEBUG] Initializing application...');
    fetchBlueprintMetadata(); // Fetch blueprint metadata and display it
    setupEventListeners();    // Set up event listeners
    debugLog('[DEBUG] Application initialized.');
}
