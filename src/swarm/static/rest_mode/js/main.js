// main.js - Main application entry point

import { initializeSplashScreen } from './splash.js';
import { initializeUI } from './ui.js';
import { debugLog } from './settings.js';

document.addEventListener('DOMContentLoaded', () => {
    debugLog("DOM Content Loaded. Initializing application...");

    try {
        initializeSplashScreen();
        debugLog("Splash screen initialization complete.");

        initializeUI();
        debugLog("UI initialization complete.");
    } catch (error) {
        debugLog(`Initialization failed: ${error.message}`, "error");
    }
});
