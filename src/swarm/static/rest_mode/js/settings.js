const DEBUG_MODE = true;

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
        const response = await fetch('/config/swarm_config.json');
        debugLog("Received response from LLM config fetch.", { status: response.status });

        if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
        const config = await response.json();
        debugLog("LLM configuration loaded successfully.", config);

        llmConfig = config.llm || {};
        updateLLMSettingsPane(llmConfig);
    } catch (error) {
        console.error("Error loading LLM config:", error);

        showToast("⚠️ LLM settings could not be loaded. Please check the server.", "warning");
    }
}

/**
 * Updates the settings pane with LLM configuration.
 * @param {Object} config - The LLM configuration object.
 */
function updateLLMSettingsPane(config) {
    debugLog("Updating LLM settings pane...", config);

    const llmContainer = document.getElementById('llmConfiguration');
    if (!llmContainer) {
        console.warn("[DEBUG] LLM configuration container not found in the DOM.");
        return;
    }

    // Render LLM configuration dynamically
    llmContainer.innerHTML = Object.entries(config)
        .map(([mode, details]) => {
            const fields = Object.entries(details)
                .map(([key, value]) => `
                    <div class="llm-field">
                        <label>${key}:</label>
                        <input type="text" value="${value}" readonly>
                    </div>
                `)
                .join('');

            return `
                <div class="llm-mode">
                    <h4>${mode.charAt(0).toUpperCase() + mode.slice(1)} Mode</h4>
                    ${fields}
                </div>
            `;
        })
        .join('');

    showToast("LLM configuration loaded successfully.", "success");
    debugLog("LLM settings pane updated.");
}

/**
 * Initialize settings logic.
 */
document.addEventListener('DOMContentLoaded', () => {
    debugLog("Settings page initialized.");

    // Load LLM configuration
    loadLLMConfig();
});
