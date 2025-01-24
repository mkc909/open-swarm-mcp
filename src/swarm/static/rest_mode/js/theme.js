/**
 * theme.js - Handles theme switching (color, layout, dark/light mode)
 */

/**
 * Initializes theme settings based on user preferences or defaults.
 */
export function initializeTheme() {
    const colorSelect = document.getElementById('colorSelect');
    const layoutSelect = document.getElementById('layoutSelect');
    const darkModeToggle = document.getElementById('darkModeToggle');

    // Load saved preferences from localStorage
    const savedColor = localStorage.getItem('selectedColor') || 'pastel';
    const savedLayout = localStorage.getItem('selectedLayout') || 'messenger-layout';
    const savedDarkMode = localStorage.getItem('darkMode') === 'true';

    // Apply saved preferences
    applyColorTheme(savedColor);
    applyLayoutTheme(savedLayout);
    setDarkMode(savedDarkMode);
    darkModeToggle.checked = savedDarkMode;

    // Event listeners for theme changes
    colorSelect.addEventListener('change', (e) => {
        applyColorTheme(e.target.value);
        localStorage.setItem('selectedColor', e.target.value);
    });

    layoutSelect.addEventListener('change', (e) => {
        applyLayoutTheme(e.target.value);
        localStorage.setItem('selectedLayout', e.target.value);
    });

    darkModeToggle.addEventListener('change', (e) => {
        const isDarkMode = e.target.checked;
        setDarkMode(isDarkMode);
        localStorage.setItem('darkMode', isDarkMode);
    });
}

/**
 * Applies the selected color theme by updating the stylesheet link.
 * @param {string} theme - The selected color theme ('pastel', 'tropical', 'corporate').
 */
function applyColorTheme(theme) {
    const colorThemeLink = document.getElementById('colorThemeLink');
    if (!colorThemeLink) return;
    colorThemeLink.href = `/static/rest_mode/css/colors/${theme}.css`;
}

/**
 * Applies the selected layout theme by updating the stylesheet link.
 * @param {string} layout - The selected layout theme ('messenger-layout', 'mobile-layout', 'minimalist-layout').
 */
function applyLayoutTheme(layout) {
    const layoutThemeLink = document.getElementById('layoutThemeLink');
    if (!layoutThemeLink) return;
    layoutThemeLink.href = `/static/rest_mode/css/layouts/${layout}.css`;

    // Update data attribute for layout
    const container = document.querySelector('.container');
    if (container) {
        container.setAttribute('data-theme-layout', layout);
    }
}

/**
 * Sets the dark mode by toggling a data attribute on the container.
 * @param {boolean} isDarkMode - Whether dark mode is enabled.
 */
export function setDarkMode(isDarkMode) {
    const container = document.querySelector('.container');
    if (!container) return;
    container.setAttribute('data-theme-dark', isDarkMode);
}
