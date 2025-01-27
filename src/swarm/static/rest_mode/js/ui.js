import { initializeSidebar } from './sidebar.js';
import { initializeApplication } from './events.js';
import { initializeTheme } from './theme.js';
import { renderQuickPrompts } from './messages.js';
import { showToast } from './toast.js';

/**
 * Shows the splash page during initialization.
 */
function showSplashPage() {
    const splashScreen = document.getElementById('splashScreen');
    const appContainer = document.getElementById('appContainer');

    if (splashScreen) {
        splashScreen.style.display = 'flex';
        appContainer.style.display = 'none';
    }
}

/**
 * Hides the splash page and reveals the app.
 */
function hideSplashPage() {
    const splashScreen = document.getElementById('splashScreen');
    const appContainer = document.getElementById('appContainer');

    if (splashScreen) {
        splashScreen.style.display = 'none';
        appContainer.style.display = 'flex';
    }
}

/**
 * Sets up the chat history pane, including toggle visibility.
 */
function setupChatHistoryPane() {
    const chatHistoryPane = document.getElementById('chatHistoryPane');
    const chatHistoryToggleButton = document.getElementById('chatHistoryToggleButton');

    if (!chatHistoryPane || !chatHistoryToggleButton) {
        console.warn("Missing elements for chat history pane.");
        return;
    }

    // Toggle visibility on button click
    chatHistoryToggleButton.addEventListener('click', () => {
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
    showSplashPage(); // Show the splash page on load
    renderQuickPrompts(); // Render quick prompts on load

    // Integrate other initialization logic
    initializeSidebar();
    initializeApplication();
    initializeTheme();
    setupChatHistoryPane();
    setupSettingsToggleButton();
    setupResizableSidebars();

    // Hide the splash screen after initialization
    setTimeout(hideSplashPage, 2000); // Example delay for effect
}

document.addEventListener('DOMContentLoaded', initializeUI);
