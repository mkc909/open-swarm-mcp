import { showToast } from './toast.js';

/**
 * Handles user logout.
 */
export function handleLogout() {
    showToast("🚪 You have been logged out.", "info");
    window.location.href = "/login";
}
