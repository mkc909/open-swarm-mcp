// src/swarm/static/rest_mode/js/modules/apiService.js

import { showToast } from '../toast.js';
import { debugLog } from './debugLogger.js';

/**
 * Handles all API interactions.
 */

/**
 * Fetches blueprint metadata from the server.
 * @returns {Promise<Array>} - Returns a promise that resolves to the list of blueprints.
 */
export async function fetchBlueprintMetadata() {
    try {
        const response = await fetch('/v1/models/');
        if (!response.ok) throw new Error('Failed to fetch metadata.');

        const data = await response.json();
        showToast('Retrieved blueprint metadata.', 'info');
        return data.data || [];
    } catch (error) {
        debugLog('Error fetching blueprint metadata:', error);
        showToast('❌ Could not retrieve blueprint metadata.', 'error');
        return [];
    }
}

/**
 * Submits a user message to the server and retrieves the assistant's response.
 * @param {string} modelName - The model to use for generating responses.
 * @param {Array} messages - The chat history messages.
 * @param {Object} contextVariables - Context variables for the chat.
 * @returns {Promise<Object>} - Returns a promise that resolves to the server's response.
 */
export async function submitMessage(modelName, messages, contextVariables) {
    try {
        const response = await fetch('/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '',
            },
            body: JSON.stringify({
                model: modelName,
                messages: messages,
                context_variables: contextVariables,
            }),
        });

        if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);

        const data = await response.json();
        return data;
    } catch (error) {
        debugLog('Error submitting message:', error);
        showToast('⚠️ Error submitting message. Please try again.', 'error');
        throw error;
    }
}

/**
 * Deletes a chat by its ID.
 * @param {string} chatId - The ID of the chat to delete.
 * @returns {Promise<boolean>} - Returns true if deletion was successful.
 */
export async function deleteChat(chatId) {
    try {
        const response = await fetch(`/v1/chat/delete/${chatId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '',
            },
        });

        if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
        return true;
    } catch (error) {
        debugLog('Error deleting chat:', error);
        showToast('❌ Error deleting chat. Please try again.', 'error');
        return false;
    }
}
