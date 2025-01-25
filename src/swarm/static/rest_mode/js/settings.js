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
