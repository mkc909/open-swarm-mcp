import { toggleSidebar } from './sidebar.js';
import {
    handleChatHistoryClick,
    handleDeleteChat,
    handleUpload,
    handleVoiceRecord,
    handleSubmit,
    renderFirstUserMessage
} from './chatLogic.js';
import { toggleDebugPane, handleTechSupport } from './debug.js';
import { initializeTheme } from './theme.js';
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

    // Top buttons
    const searchButton = document.getElementById("searchButton");
    const newChatButton = document.getElementById("newChatButton");

    searchButton?.addEventListener('click', () => handleSearch());
    newChatButton?.addEventListener('click', () => handleNewChat());

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

    // Enter key for submitting messages
    const userInput = document.getElementById("userInput");
    userInput?.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            handleSubmit();
        }
    });

    // Debug pane toggle
    document.getElementById("debugButton")?.addEventListener('click', () => toggleDebugPane());

    // Tech Support button inside Debug pane
    document.getElementById("techSupportButtonInsideDebug")?.addEventListener('click', () => handleTechSupport());

    // Dark Mode Toggle Button
    const darkModeToggleButton = document.getElementById('darkModeToggleButton');
    darkModeToggleButton?.addEventListener('click', () => {
        // Handled in theme.js
    });
}

/**
 * Initialize the application.
 */
export function initializeApplication() {
    renderFirstUserMessage();
    setupEventListeners();
}
