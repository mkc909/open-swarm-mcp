/**
 * theme.js - Handles theme switching (style, layout, dark/light mode)
 */

/**
 * Initializes theme settings based on user preferences or defaults.
 */
export function initializeTheme() {
    const colorSelect = document.getElementById('colorSelect');
    const layoutSelect = document.getElementById('layoutSelect');
    const darkModeToggle = document.getElementById('darkModeToggle'); // Updated ID

    // Log warnings for missing elements
    if (!colorSelect) console.warn("Warning: Element 'colorSelect' not found.");
    if (!layoutSelect) console.warn("Warning: Element 'layoutSelect' not found.");
    if (!darkModeToggle) console.warn("Warning: Element 'darkModeToggle' not found.");

    // Load saved preferences from localStorage
    const savedColor = localStorage.getItem('selectedColor') || 'pastel';
    const savedLayout = localStorage.getItem('selectedLayout') || 'messenger-layout';
    const savedDarkMode = localStorage.getItem('darkMode') === 'true';

    // Apply saved preferences
    applyColorTheme(savedColor);
    applyLayoutTheme(savedLayout);
    setDarkMode(savedDarkMode);

    // Attach event listeners only if the elements exist
    if (colorSelect) {
        colorSelect.addEventListener('change', (e) => {
            applyColorTheme(e.target.value);
            localStorage.setItem('selectedColor', e.target.value);
        });
    }

    if (layoutSelect) {
        layoutSelect.addEventListener('change', (e) => {
            applyLayoutTheme(e.target.value);
            localStorage.setItem('selectedLayout', e.target.value);
        });
    }

    if (darkModeToggle) {
        darkModeToggle.addEventListener('change', (e) => {
            const isDarkMode = e.target.checked;
            setDarkMode(isDarkMode);
            localStorage.setItem('darkMode', isDarkMode);
        });
    }
}

/**
 * Applies the selected color theme by updating the stylesheet link.
 * @param {string} theme - The selected style theme ('pastel', 'tropical', 'corporate').
 */
function applyColorTheme(theme) {
    const colorThemeLink = document.getElementById('colorThemeLink');
    if (colorThemeLink) {
        colorThemeLink.href = `/static/rest_mode/css/colors/${theme}.css`;
    }
}

/**
 * Applies the selected layout theme by toggling layout-specific classes.
 * @param {string} layout - The selected layout theme ('messenger-layout', 'mobile-layout', 'minimalist-layout').
 */
function applyLayoutTheme(layout) {
    const container = document.querySelector('.container');
    if (container) {
        container.setAttribute('data-theme-layout', layout);
    }
}

/**
 * Sets the dark mode by toggling a data attribute on the container.
 * @param {boolean} isDarkMode - Whether dark mode is enabled.
 */
function setDarkMode(isDarkMode) {
    const container = document.querySelector('.container');
    if (container) {
        container.setAttribute('data-theme-dark', isDarkMode);
    }
}
