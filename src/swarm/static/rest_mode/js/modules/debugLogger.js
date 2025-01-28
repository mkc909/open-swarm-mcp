// src/swarm/static/rest_mode/js/modules/debugLogger.js

const DEBUG_MODE = true;

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
