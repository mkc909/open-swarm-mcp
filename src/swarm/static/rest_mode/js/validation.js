// validation.js - Handles input validation

import { showToast } from './toast.js'; // Import the toast notification function

/**
 * Validates a single message object.
 * @param {object} message - The message object to validate.
 * @returns {string|null} - Returns an error message string if invalid, otherwise null.
 */
function validateMessage(message) {
    if (!message || typeof message !== 'object') {
        showToast("Invalid message format.", "error");
        return "Invalid message format.";
    }

    const { role, content } = message;

    if (!role || typeof role !== 'string') {
        showToast("Message role is missing or invalid.", "error");
        return "Message role is missing or invalid.";
    }

    if (!content || typeof content !== 'string') {
        showToast("Message content is missing or invalid.", "error");
        return "Message content is missing or invalid.";
    }

    // Additional validations can be added here

    return null;
}

/**
 * Validates the entire chat history.
 * @param {Array} chatHistory - The array of message objects.
 * @returns {string|null} - Returns an error message string if invalid, otherwise null.
 */
function validateChatHistory(chatHistory) {
    if (!Array.isArray(chatHistory)) {
        showToast("Chat history is invalid.", "error");
        return "Chat history is invalid.";
    }

    for (let message of chatHistory) {
        const error = validateMessage(message);
        if (error) {
            return error;
        }
    }

    return null;
}

export {
    validateMessage,
    validateChatHistory
}
