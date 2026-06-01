/** 
 * theme.js - Handles theme switching (style, layout, dark/light mode)
 */

import { showToast } from './toast.js';

/**
 * Initializes theme settings based on user preferences or defaults.
 */
export function initializeTheme() {
    const colorSelect = document.getElementById('colorSelect');
    const layoutSelect = document.getElementById('layoutSelect');
    const darkModeToggle = document.getElementById('darkModeToggle');

    // Default values
    const defaultSettings = {
        colorTheme: 'corporate',
        layoutTheme: 'messenger-layout',
        darkMode: true,
    };

    // Load saved preferences from localStorage or use defaults
    const savedColor = localStorage.getItem('selectedColor') || defaultSettings.colorTheme;
    const savedLayout = localStorage.getItem('selectedLayout') || defaultSettings.layoutTheme;
    const savedDarkMode = localStorage.getItem('darkMode') === 'true' || defaultSettings.darkMode;

    // Apply preferences
    applyColorTheme(savedColor);
    applyLayoutTheme(savedLayout);
    setDarkMode(savedDarkMode);

    // Sync UI elements with preferences
    if (colorSelect) colorSelect.value = savedColor;
    if (layoutSelect) layoutSelect.value = savedLayout;
    if (darkModeToggle) darkModeToggle.checked = savedDarkMode;

    // Attach event listeners
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
 * Applies the selected color theme by adding a data attribute and ensuring all theme-related styles are updated.
 * @param {string} theme - The selected style theme ('pastel', 'tropical', 'corporate').
 */
function applyColorTheme(theme) {
    const rootElement = document.documentElement; // Use <html> element
    rootElement.setAttribute('data-theme', theme);

    // Apply variables for custom elements and dynamic parts of the UI
    document.querySelectorAll('.dynamic-theme-element').forEach((element) => {
        const bgColor = getComputedStyle(rootElement).getPropertyValue('--bg-container').trim();
        const textColor = getComputedStyle(rootElement).getPropertyValue('--text-primary').trim();

        element.style.backgroundColor = bgColor;
        element.style.color = textColor;
    });

    // Update SVG icon colors dynamically
    document.querySelectorAll('.icon-svg').forEach((icon) => {
        icon.style.fill = getComputedStyle(rootElement).getPropertyValue('--icon-color');
    });

    showToast(`Theme applied: ${theme.charAt(0).toUpperCase() + theme.slice(1)}`);
}

/**
 * Applies the selected layout theme by adding a data attribute.
 * @param {string} layout - The selected layout theme ('messenger-layout', 'mobile-layout', 'minimalist-layout').
 */
function applyLayoutTheme(layout) {
    const rootElement = document.documentElement; // Use <html> element
    rootElement.setAttribute('data-theme-layout', layout);
}

/**
 * Sets the dark mode by adding a data attribute and ensuring global variables are updated.
 * @param {boolean} isDarkMode - Whether dark mode is enabled.
 */
function setDarkMode(isDarkMode) {
    const rootElement = document.documentElement; // Use <html> element
    rootElement.setAttribute('data-theme-dark', isDarkMode ? 'true' : 'false');

    // Optionally, adjust custom styles for dark mode
    document.querySelectorAll('.dynamic-theme-element').forEach((element) => {
        const bgColor = getComputedStyle(rootElement).getPropertyValue('--bg-container').trim();
        const textColor = getComputedStyle(rootElement).getPropertyValue('--text-primary').trim();

        element.style.backgroundColor = bgColor;
        element.style.color = textColor;
    });
}
