const DEBUG_MODE = true;

/**
 * Logs debug messages if debug mode is enabled.
 * @param {string} message - The message to log.
 * @param {any} data - Additional data to include in the log.
 */
function debugLog(message, data = null) {
    if (DEBUG_MODE) {
        console.log(`[DEBUG] ${message}`, data);
    }
}

/**
 * Fetches the list of blueprints (models) from the server.
 * @returns {Promise<Array>} - A promise resolving to the list of blueprints.
 */
export async function fetchBlueprints() {
    debugLog("Fetching blueprints from /v1/models/...");
    try {
        const response = await fetch('/v1/models/');
        if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);

        const data = await response.json();
        debugLog("Blueprints fetched successfully.", data);
        return data.data || [];
    } catch (error) {
        console.error("Error fetching blueprints:", error);
        throw error;
    }
}
