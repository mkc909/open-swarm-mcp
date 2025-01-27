const DEBUG_MODE = true;

import { showToast } from './toast.js';

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
 * Handle Dark Mode Toggle.
 */
function handleDarkModeToggle() {
    const darkModeToggle = document.getElementById('darkModeToggle');

    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', () => {
            const isDarkMode = darkModeToggle.dataset.state === 'on';

            // Toggle dark mode class on the <body> element
            document.body.classList.toggle('dark-mode', !isDarkMode);

            // Update the toggle state and icon
            darkModeToggle.dataset.state = isDarkMode ? 'off' : 'on';
            darkModeToggle.querySelector('img').src = isDarkMode
                ? '/static/rest_mode/svg/toggle_off.svg'
                : '/static/rest_mode/svg/toggle_on.svg';

            showToast(`Dark Mode ${isDarkMode ? 'disabled' : 'enabled'}`, isDarkMode ? 'info' : 'success');

            // Reapply the active color theme with the new dark mode setting
            applyTheme();
        });
    }
}

/**
 * Handle Theme and Layout Selection.
 */
function handleThemeAndLayoutSelection() {
    const colorSelect = document.getElementById('colorSelect');
    const layoutSelect = document.getElementById('layoutSelect');

    if (colorSelect) {
        colorSelect.addEventListener('change', applyTheme);
    }

    if (layoutSelect) {
        layoutSelect.addEventListener('change', applyTheme);
    }
}

/**
 * Apply the selected theme and layout.
 */
function applyTheme() {
    const colorSelect = document.getElementById('colorSelect');
    const layoutSelect = document.getElementById('layoutSelect');
    const darkModeEnabled = document.body.classList.contains('dark-mode');

    const selectedColor = colorSelect ? colorSelect.value : 'pastel';
    const selectedLayout = layoutSelect ? layoutSelect.value : 'messenger-layout';

    // Update the theme stylesheet
    const themeStylesheet = document.getElementById('themeStylesheet');
    if (themeStylesheet) {
        themeStylesheet.href = `/static/rest_mode/css/themes/${selectedColor}${darkModeEnabled ? '-dark' : ''}.css`;
    }

    // Update the layout stylesheet
    const layoutStylesheet = document.getElementById('layoutStylesheet');
    if (layoutStylesheet) {
        layoutStylesheet.href = `/static/rest_mode/css/layouts/${selectedLayout}.css`;
    }

    showToast(`Applied ${selectedColor} theme and ${selectedLayout} layout`, 'success');
}

/**
 * Initialize Settings.
 */
document.addEventListener('DOMContentLoaded', () => {
    debugLog("Settings page initialized.");

    handleDarkModeToggle();
    handleThemeAndLayoutSelection();

    // Apply the initial theme and layout
    applyTheme();
});
