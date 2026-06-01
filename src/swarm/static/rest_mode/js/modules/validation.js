// src/swarm/static/rest_mode/js/modules/validation.js

import { showToast } from '../toast.js';
import { debugLog } from './debugLogger.js';

/**
 * Validates the user message.
 * @param {Object} message - The message object to validate.
 * @returns {string|null} - Error message if invalid, or null if valid.
 */
export function validateMessage(message) {
    if (!message.content || message.content.trim() === '') {
        showToast('❌ Message cannot be empty.', 'error');
        debugLog('Validation failed: Message is empty.');
        return 'Message cannot be empty.';
    }
    if (message.content.length > 5000) {
        showToast('❌ Message too long. Please limit to 5000 characters.', 'error');
        debugLog('Validation failed: Message too long.');
        return 'Message too long.';
    }
    return null; // Valid message
}
