import { initializeUI } from './ui.js';
import { initializeSplashScreen } from './splash.js';

/**
 * Entry point for initializing the application.
 */
document.addEventListener('DOMContentLoaded', () => {
    initializeUI();
    initializeSplashScreen();
});
