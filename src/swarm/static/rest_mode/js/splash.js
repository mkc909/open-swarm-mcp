// splash.js - Manages the Splash Screen

/**
 * Initializes the splash screen. Fades out after loading finishes and removes it from the DOM.
 */
export function initializeSplashScreen() {
    window.addEventListener('load', () => {
        const splashScreen = document.getElementById('splashScreen');
        const splashText = document.getElementById('splashText');

        // List of possible splash texts
        const splashTexts = [
            "Welcome to Open-Swarm Chat!",
            "Connecting to the AI...",
            "Preparing your AI experience...",
            "Loading AI capabilities..."
        ];

        // Set a random splash text
        if (splashTexts.length > 0 && splashText) {
            const randomIndex = Math.floor(Math.random() * splashTexts.length);
            splashText.textContent = splashTexts[randomIndex];
        }

        // Simulate AI connection establishment
        // Replace this with actual AI connection logic if available
        simulateAIConnection()
            .then(() => {
                // After AI is connected, fade out the splash screen
                if (splashScreen) {
                    splashScreen.classList.add('fade-out');
                }
            })
            .catch(() => {
                // Handle connection errors
                if (splashText) {
                    splashText.textContent = "Failed to connect to the AI.";
                }
                // Fade out after showing error
                setTimeout(() => {
                    if (splashScreen) {
                        splashScreen.classList.add('fade-out');
                    }
                }, 3000);
            });

        // Remove the splash screen from the DOM after the fade-out transition
        if (splashScreen) {
            splashScreen.addEventListener('transitionend', () => {
                if (splashScreen && splashScreen.parentNode) {
                    splashScreen.parentNode.removeChild(splashScreen);
                }
            });
        }
    });
}

/**
 * Simulates AI connection establishment.
 * Replace this function with actual connection logic.
 */
function simulateAIConnection() {
    return new Promise((resolve, reject) => {
        // Simulate a successful connection after 2 seconds
        setTimeout(() => {
            resolve();
        }, 2000);
    });
}
