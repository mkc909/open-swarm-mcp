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
        chatHistoryPane.classList.toggle('hidden');
        const isVisible = !chatHistoryPane.classList.contains('hidden');
        showToast(isVisible ? "Chat history expanded." : "Chat history minimized.", "info");
    });
}

/**
 * Sets up the settings toggle button functionality.
 */
function setupSettingsToggleButton() {
    const settingsToggleButton = document.getElementById('settingsToggleButton');
    const optionsPane = document.getElementById('optionsPane');

    if (settingsToggleButton && optionsPane) {
        settingsToggleButton.addEventListener('click', () => {
            optionsPane.classList.toggle('hidden');
            const isVisible = !optionsPane.classList.contains('hidden');
            showToast(isVisible ? "Settings pane expanded." : "Settings pane hidden.", "info");
        });
    } else {
        console.warn('Warning: Settings toggle button or options pane not found.');
    }
}

/**
 * Sets up resizable sidebars.
 */
function setupResizableSidebars() {
    const leftDivider = document.getElementById("divider-left");
    const rightDivider = document.getElementById("divider-right");
    const chatHistoryPane = document.getElementById("chatHistoryPane");
    const optionsPane = document.getElementById("optionsPane");

    const resize = (divider, targetPane, isLeft) => {
        divider.addEventListener("mousedown", (e) => {
            e.preventDefault();

            const handleMouseMove = (event) => {
                const newWidth = isLeft
                    ? event.clientX - chatHistoryPane.getBoundingClientRect().left
                    : optionsPane.getBoundingClientRect().right - event.clientX;

                // Apply constraints
                if (newWidth >= 150 && newWidth <= 500) {
                    targetPane.style.width = `${newWidth}px`;
                }
            };

            const stopResize = () => {
                document.removeEventListener("mousemove", handleMouseMove);
                document.removeEventListener("mouseup", stopResize);
            };

            document.addEventListener("mousemove", handleMouseMove);
            document.addEventListener("mouseup", stopResize);
        });
    };

    if (leftDivider) resize(leftDivider, chatHistoryPane, true);
    if (rightDivider) resize(rightDivider, optionsPane, false);
}

/**
 * Displays the loading indicator.
 */
export function showLoadingIndicator() {
    if (loadingIndicator) {
        loadingIndicator.style.display = 'flex';
    }
}

/**
 * Hides the loading indicator.
 */
export function hideLoadingIndicator() {
    if (loadingIndicator) {
        loadingIndicator.style.display = 'none';
        loadingIndicator.innerHTML = '';
    }
}

/**
 * Initializes all UI components and event listeners.
 */
export function initializeUI() {
    initializeSidebar();
    initializeApplication();
    initializeTheme();
    replaceAllSVGs();
    setupChatHistoryPane();
    setupSettingsToggleButton();
    setupResizableSidebars(); // Integrated here
}

document.addEventListener('DOMContentLoaded', initializeUI);
