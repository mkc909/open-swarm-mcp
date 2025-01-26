const DEBUG_MODE = true; // Toggle debug logging

import { showToast } from './toast.js';

export let llmConfig = {};

/**
 * Logs debug messages if debug mode is enabled.
 * @param {string} message - The message to log.
 * @param {any} data - Additional data to include in the log.
 */
export function debugLog(message, data = null) {
    if (DEBUG_MODE) {
        console.log(`[DEBUG] ${message}`, data);
    }
}

/**
 * Fetch and load LLM configuration.
 */
export async function loadLLMConfig() {
    debugLog("Attempting to load LLM configuration...");
    try {
        const response = await fetch('/static/config/swarm_config.json');
        debugLog("Received response from LLM config fetch.", { status: response.status });

        if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
        const config = await response.json();
        debugLog("LLM configuration loaded successfully.", config);

        llmConfig = config.llm || {};
        updateSettingsPane(llmConfig);
    } catch (error) {
        console.error("Error loading LLM config:", error);

        llmConfig = {
            default: {
                provider: "openai",
                model: "gpt-4o",
                base_url: "https://api.openai.com/v1",
                api_key: "",
                temperature: 0.3,
            },
        }; // Default fallback

        showToast("⚠️ LLM settings could not be loaded. Using defaults.", "warning");
        updateSettingsPane(llmConfig);
    }
}

/**
 * Updates the settings pane with LLM configuration.
 */
function updateSettingsPane(config) {
    debugLog("Updating settings pane with LLM configuration...", config);

    const settingsPane = document.getElementById('settingsPane');
    if (!settingsPane) {
        console.warn("[DEBUG] Settings pane not found in the DOM.");
        return;
    }

    settingsPane.innerHTML = `
        <h3>LLM Configuration</h3>
        <div>
            <label for="llmSummary">Summary:</label>
            <select id="llmSummary">
                ${Object.keys(config).map(llm => `<option value="${llm}">${config[llm].model}</option>`).join('')}
            </select>
        </div>
        <div>
            <label for="llmReason">Reason:</label>
            <select id="llmReason">
                ${Object.keys(config).map(llm => `<option value="${llm}">${config[llm].model}</option>`).join('')}
            </select>
        </div>
        <div>
            <label for="llmDefault">Default:</label>
            <select id="llmDefault">
                ${Object.keys(config).map(llm => `<option value="${llm}">${config[llm].model}</option>`).join('')}
            </select>
        </div>
    `;
    debugLog("Settings pane updated successfully.");
}
    
document.addEventListener('DOMContentLoaded', function() {
    // Mobile UI Toggle Handlers
    const mobileUIToggle = document.getElementById('mobileUIToggle');
    if (mobileUIToggle) {
        mobileUIToggle.addEventListener('change', function() {
            const isEnabled = this.checked;
            // Handle Mobile UI toggle
            if (isEnabled) {
                showToast("Mobile UI enabled", "success");
                // Additional logic to enable Mobile UI features
            } else {
                showToast("Mobile UI disabled", "info");
                // Additional logic to disable Mobile UI features
            }
        });
    }

    const alwaysVisibleButtonsToggle = document.getElementById('alwaysVisibleButtonsToggle');
    if (alwaysVisibleButtonsToggle) {
        alwaysVisibleButtonsToggle.addEventListener('change', function() {
            const isEnabled = this.checked;
            // Handle Always Visible Buttons toggle
            if (isEnabled) {
                showToast("Always Visible Buttons enabled", "success");
                // Logic to show always visible buttons
            } else {
                showToast("Always Visible Buttons disabled", "info");
                // Logic to hide always visible buttons
            }
        });
    }

    const swipeLeftSettingsToggle = document.getElementById('swipeLeftSettingsToggle');
    if (swipeLeftSettingsToggle) {
        swipeLeftSettingsToggle.addEventListener('change', function() {
            const isEnabled = this.checked;
            // Handle Swipe left for Settings toggle
            if (isEnabled) {
                showToast("Swipe left for Settings enabled", "success");
                // Logic to enable swipe left for settings
            } else {
                showToast("Swipe left for Settings disabled", "info");
                // Logic to disable swipe left for settings
            }
        });
    }

    const swipeRightChatHistoryToggle = document.getElementById('swipeRightChatHistoryToggle');
    if (swipeRightChatHistoryToggle) {
        swipeRightChatHistoryToggle.addEventListener('change', function() {
            const isEnabled = this.checked;
            // Handle Swipe right for Chat History toggle
            if (isEnabled) {
                showToast("Swipe right for Chat History enabled", "success");
                // Logic to enable swipe right for chat history
            } else {
                showToast("Swipe right for Chat History disabled", "info");
                // Logic to disable swipe right for chat history
            }
        });
    }

    const swipeDownControlsToggle = document.getElementById('swipeDownControlsToggle');
    if (swipeDownControlsToggle) {
        swipeDownControlsToggle.addEventListener('change', function() {
            const isEnabled = this.checked;
            // Handle Swipe down for Controls toggle
            if (isEnabled) {
                showToast("Swipe down for Controls enabled", "success");
                // Logic to enable swipe down for controls
            } else {
                showToast("Swipe down for Controls disabled", "info");
                // Logic to disable swipe down for controls
            }
        });
    }
});

    // Mobile UI Toggle Handlers
    document.getElementById('mobileUIToggle').addEventListener('change', function() {
        const isEnabled = this.checked;
        // Handle Mobile UI toggle
        if (isEnabled) {
            showToast("Mobile UI enabled", "success");
            // Additional logic to enable Mobile UI features
        } else {
            showToast("Mobile UI disabled", "info");
            // Additional logic to disable Mobile UI features
        }
    });
    
    document.getElementById('alwaysVisibleButtonsToggle').addEventListener('change', function() {
        const isEnabled = this.checked;
        // Handle Always Visible Buttons toggle
        if (isEnabled) {
            showToast("Always Visible Buttons enabled", "success");
            // Logic to show always visible buttons
        } else {
            showToast("Always Visible Buttons disabled", "info");
            // Logic to hide always visible buttons
        }
    });
    
    document.getElementById('swipeLeftSettingsToggle').addEventListener('change', function() {
        const isEnabled = this.checked;
        // Handle Swipe left for Settings toggle
        if (isEnabled) {
            showToast("Swipe left for Settings enabled", "success");
            // Logic to enable swipe left for settings
        } else {
            showToast("Swipe left for Settings disabled", "info");
            // Logic to disable swipe left for settings
        }
    });
    
    document.getElementById('swipeRightChatHistoryToggle').addEventListener('change', function() {
        const isEnabled = this.checked;
        // Handle Swipe right for Chat History toggle
        if (isEnabled) {
            showToast("Swipe right for Chat History enabled", "success");
            // Logic to enable swipe right for chat history
        } else {
            showToast("Swipe right for Chat History disabled", "info");
            // Logic to disable swipe right for chat history
        }
    });
    
    document.getElementById('swipeDownControlsToggle').addEventListener('change', function() {
        const isEnabled = this.checked;
        // Handle Swipe down for Controls toggle
        if (isEnabled) {
            showToast("Swipe down for Controls enabled", "success");
            // Logic to enable swipe down for controls
        } else {
            showToast("Swipe down for Controls disabled", "info");
            // Logic to disable swipe down for controls
        }
    });
