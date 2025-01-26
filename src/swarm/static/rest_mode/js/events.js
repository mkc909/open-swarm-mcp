import { toggleSidebar } from './sidebar.js';
import {
    handleChatHistoryClick,
    handleDeleteChat,
    handleUpload,
    handleVoiceRecord,
    fetchBlueprintMetadata,
} from './chatHandlers.js';
import { handleSubmit } from './chatLogic.js';
import { toggleDebugPane, handleTechSupport } from './debug.js';
import { showToast } from './toast.js';
import { handleLogout } from './auth.js';

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
        item.addEventListener('click', () => handleChatHistoryClick(item));

        const trashCan = item.querySelector('.trash-can');
        if (trashCan) {
            trashCan.addEventListener('click', (e) => {
                e.stopPropagation();
                handleDeleteChat(item);
            });
        }
    });
}

/**
 * Attaches event listeners to main application buttons and elements.
 */
function setupGlobalEventListeners() {
    // Sidebar toggles
    document.getElementById("leftSidebarHideBtn")?.addEventListener('click', () => toggleSidebar('left', false));
    document.getElementById("leftSidebarRevealBtn")?.addEventListener('click', () => toggleSidebar('left', true));
    document.getElementById("optionsSidebarHideBtn")?.addEventListener('click', () => toggleSidebar('options', false));
    document.getElementById("optionsSidebarRevealBtn")?.addEventListener('click', () => toggleSidebar('options', true));

    // Top buttons
    document.getElementById("searchButton")?.addEventListener('click', handleSearch);
    document.getElementById("newChatButton")?.addEventListener('click', handleNewChat);

    // Functional buttons
    document.getElementById("logoutButton")?.addEventListener('click', handleLogout);
    document.getElementById("uploadButton")?.addEventListener('click', handleUpload);
    document.getElementById("voiceRecordButton")?.addEventListener('click', handleVoiceRecord);
    document.getElementById("submitButton")?.addEventListener("click", handleSubmit);

    // User input submission with Enter key
    const userInput = document.getElementById("userInput");
    userInput?.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
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
export function setupEventListeners() {
    setupGlobalEventListeners();
    setupChatHistoryListeners();
}

/**
 * Initialize the application.
 */
export function initializeApplication() {
    console.log('[DEBUG] Initializing application...');
    fetchBlueprintMetadata(); // Fetch blueprint metadata and display it
    setupEventListeners();    // Set up event listeners
    console.log('[DEBUG] Application initialized.');
}
