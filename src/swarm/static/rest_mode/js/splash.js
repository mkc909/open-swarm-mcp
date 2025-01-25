// splash.js - Manages the Splash Screen

/**
 * Initializes the splash screen. Fades out after loading finishes and removes it from the DOM.
 */
export function initializeSplashScreen() {
    console.log("[DEBUG] Initializing splash screen.");

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
            console.log(`[DEBUG] Set splash text: ${splashText.textContent}`);
        }

        // Simulate AI connection establishment
        simulateAIConnection()
            .then(() => {
                // After AI is connected, fade out the splash screen
                if (splashScreen) {
                    console.log("[DEBUG] AI connection established. Fading out splash screen.");
                    splashScreen.classList.add('fade-out');
                }
            })
            .catch(() => {
                // Handle connection errors
                if (splashText) {
                    splashText.textContent = "Failed to connect to the AI.";
                    console.warn("[DEBUG] AI connection failed. Displaying error message.");
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
                    console.log("[DEBUG] Splash screen removed from the DOM.");
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
    console.log("[DEBUG] Simulating AI connection...");
    return new Promise((resolve, reject) => {
        // Simulate a successful connection after 2 seconds
        setTimeout(() => {
            resolve();
            console.log("[DEBUG] AI connection simulation resolved.");
        }, 2000);
    });
}
