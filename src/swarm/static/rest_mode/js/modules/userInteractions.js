// src/swarm/static/rest_mode/js/modules/userInteractions.js

import { showToast } from '../toast.js';
import { debugLog } from './debugLogger.js';

/**
 * Handles user logout.
 */
export function handleLogout() {
    showToast('🚪 You have been logged out.', 'info');
    debugLog('User initiated logout.');
    window.location.href = '/login';
}

/**
 * Handles file upload.
 */
export function handleUpload() {
    showToast('➕ Upload feature is under development.', 'info');
    debugLog('User attempted to upload a file.');
}

/**
 * Handles voice recording.
 */
export function handleVoiceRecord() {
    showToast('🎤 Voice recording is under development.', 'info');
    debugLog('User attempted to record voice.');
}
