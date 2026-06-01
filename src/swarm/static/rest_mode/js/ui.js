import { initializeSidebar } from './sidebar.js';
import { initializeApplication } from './events.js';
import { initializeChatLogic } from './chatLogic.js';
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
    const buttonsToToggle = [
        'settingsButton-main',
        'searchButton-main',
        'newChatButton-main',
    ].map(id => document.getElementById(id));

    if (!chatHistoryPane || !chatHistoryToggleButton) {
        console.warn("Missing elements for chat history pane.");
        return;
    }

    // Toggle visibility on button clicks
    const chatHistoryToggleButtonVisible = document.getElementById('chatHistoryToggleButtonVisible');
    
    // Toggle button in sidebar
    chatHistoryToggleButton.addEventListener('click', () => {
        chatHistoryPane.classList.add('hidden');
        chatHistoryToggleButtonVisible.style.display = 'block';

        buttonsToToggle.forEach(button => {
            if (button) {
                button.style.display = 'block';
            }
        });

        showToast("Chat history minimized.", "info");
 
    });

    // New toggle button in main pane
    if (chatHistoryToggleButtonVisible) {
        chatHistoryToggleButtonVisible.addEventListener('click', () => {
            chatHistoryPane.classList.remove('hidden');
            chatHistoryToggleButtonVisible.style.display = 'none';
            showToast("Chat history expanded.", "info");

            buttonsToToggle.forEach(button => {
                if (button) {
                    button.style.display = 'none';
                }
            });
        });
    }

}

/**
 * Sets up the settings toggle button functionality.
 */
import { toggleSidebar } from './sidebar.js';

function setupSettingsToggleButton() {
    const settingsToggleButton = document.getElementById('settingsToggleButton');
    const settingsButtonMain = document.getElementById('settingsButton-main');

    if (settingsToggleButton) {
        settingsToggleButton.addEventListener('click', () => {
            toggleSidebar('options');
        });
    } else {
        console.warn('Warning: Settings toggle button not found.');
    }

    if (settingsButtonMain) {
        settingsButtonMain.addEventListener('click', () => {
            toggleSidebar('options');
        });
    } else {
         console.warn('Warning: Settings button main not found.');
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
    const loadingIndicator = document.getElementById("loadingIndicator");
    if (loadingIndicator) {
        loadingIndicator.style.display = 'flex';
    }
}

/**
 * Hides the loading indicator.
 */
export function hideLoadingIndicator() {
    const loadingIndicator = document.getElementById("loadingIndicator");
    if (loadingIndicator) {
        loadingIndicator.style.display = 'none';
        loadingIndicator.innerHTML = '';
    }
}


/**
 * Attaches sliding toolbar behavior to messages and adjusts container height.
 * @param {HTMLElement} messageElement - The message element to attach the toolbar logic.
 * @param {Object} options - Configuration for the toolbar behavior.
 * @param {number} options.toolbarHeight - The height of the toolbar when visible (default: 50).
 */
export function enableSlidingToolbar(
    messageElement,
    { toolbarHeight = 50 } = {}
) {
    const toolbar = messageElement.querySelector('.message-toolbar');
    if (!toolbar) return;

    // Apply initial styles
    toolbar.style.height = '0px';
    toolbar.style.opacity = '0';
    toolbar.style.transition = 'height 0.3s ease, opacity 0.3s ease';

    messageElement.style.transition = 'height 0.3s ease';

    messageElement.addEventListener('mouseenter', () => {
        toolbar.style.height = `${toolbarHeight}px`;
        toolbar.style.opacity = '1';

        // Adjust message height to accommodate the toolbar
        messageElement.style.height = `${messageElement.scrollHeight + toolbarHeight}px`;
    });

    messageElement.addEventListener('mouseleave', () => {
        toolbar.style.height = '0px';
        toolbar.style.opacity = '0';

        // Reset message height when toolbar is hidden
        messageElement.style.height = '';
    });
}

// TODO find home for this dropdown black text workaround...
document.addEventListener('DOMContentLoaded', function() {
    const blueprintDropdown = document.getElementById('blueprintDropdown');

    // Function to style all options
    function styleOptions() {
        const options = blueprintDropdown?.options;
        if (options) {
            for (let i = 0; i < options.length; i++) {
                options[i].style.color = 'black';
            }
        }
    }

    // Style options initially
    styleOptions();

    if (blueprintDropdown) {
        // Style options whenever the dropdown is opened
        blueprintDropdown.addEventListener('mousedown', function() {
            styleOptions();
        });
    
        // Style options whenever the dropdown is changed
        blueprintDropdown.addEventListener('change', function() {
            styleOptions();
        });
    }
});


/**
 * Initializes all UI components and event listeners.
 */
export function initializeUI() {
    if (window.isUIInitialized) {
        console.warn("UI is already initialized.");
        return;
    }

    showSplashPage(); // Show the splash page on load
    renderQuickPrompts(); // Render quick prompts on load

    // Integrate other initialization logic
    initializeSidebar();
    setupChatHistoryPane();
    initializeChatLogic();
    // setupSettingsToggleButton();
    setupResizableSidebars();
    initializeTheme();

    // Hide the splash screen after initialization
    setTimeout(hideSplashPage, 2000); // Example delay for effect

    window.isUIInitialized = true;
}


