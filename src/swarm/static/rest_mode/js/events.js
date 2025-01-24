import { toggleSidebar } from './sidebar.js';
import {
    handleChatHistoryClick,
    handleDeleteChat,
    handleLogout,
    handleUpload,
    handleVoiceRecord,
    handleSubmit,
    renderFirstUserMessage
} from './chatLogic.js';
import { toggleDebugPane, handleTechSupport } from './debug.js';

/**
 * Sets up all event listeners for the application.
 */
export function setupEventListeners() {
    // Sidebar toggles
    const leftSidebarHideBtn = document.getElementById("leftSidebarHideBtn");
    const leftSidebarRevealBtn = document.getElementById("leftSidebarRevealBtn");
    const optionsSidebarHideBtn = document.getElementById("optionsSidebarHideBtn");
    const optionsSidebarRevealBtn = document.getElementById("optionsSidebarRevealBtn");

    leftSidebarHideBtn?.addEventListener('click', () => toggleSidebar('left', false));
    leftSidebarRevealBtn?.addEventListener('click', () => toggleSidebar('left', true));
    optionsSidebarHideBtn?.addEventListener('click', () => toggleSidebar('options', false));
    optionsSidebarRevealBtn?.addEventListener('click', () => toggleSidebar('options', true));

    // Chat history items
    const chatHistoryItems = document.querySelectorAll('.chat-history-pane li');
    chatHistoryItems.forEach(item => {
        item.addEventListener('click', () => handleChatHistoryClick(item));
        const trashCan = item.querySelector('.trash-can');
        if (trashCan) {
            trashCan.addEventListener('click', (e) => {
                e.stopPropagation();
                handleDeleteChat(item);
            });
        }
    });

    // Buttons
    document.getElementById("logoutButton")?.addEventListener('click', () => handleLogout());
    document.getElementById("uploadButton")?.addEventListener('click', () => handleUpload());
    document.getElementById("voiceRecordButton")?.addEventListener('click', () => handleVoiceRecord());
    document.getElementById("submitButton")?.addEventListener("click", () => handleSubmit());

    // Enter key
    const userInput = document.getElementById("userInput");
    userInput?.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            handleSubmit();
        }
    });

    // Debug
    document.getElementById("debugButton")?.addEventListener('click', () => toggleDebugPane());
    document.getElementById("techSupportButtonInsideDebug")?.addEventListener('click', () => handleTechSupport());
}

/**
 * Initialize the app’s logic: first user message, event listeners, etc.
 */
export function initializeApplication() {
    renderFirstUserMessage();
    setupEventListeners();
}
