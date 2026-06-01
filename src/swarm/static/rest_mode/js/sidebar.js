// src/swarm/static/rest_mode/js/sidebar.js

import { showToast } from './toast.js';

/* Existing toggleSidebar function */
export function toggleSidebar(sidebar) {
    if (sidebar === 'left') {
        const chatHistoryPane = document.getElementById('chatHistoryPane');
        const chatHistoryToggleButton = document.getElementById('chatHistoryToggleButton');

        if (!chatHistoryPane || !chatHistoryToggleButton) {
            console.warn('Chat History Pane or Toggle Button is missing.');
            return;
        }

        // Toggle the 'hidden' class
        const isHidden = chatHistoryPane.classList.toggle('hidden');


    } 
}

/**
 * Sets up resizable sidebars with draggable dividers.
 */
function setupResizableSidebars() {
    const leftDivider = document.getElementById("divider-left");
    const rightDivider = document.getElementById("divider-right");

    if (!leftDivider || !chatHistoryPane) {
        console.warn('One or more elements for resizable sidebars are missing.');
        return;
    }

    const handleMouseMove = (e, targetPane, isLeft) => {
        const newWidth = isLeft
            ? e.clientX 
            : window.innerWidth - e.clientX;
        // if (newWidth > 100 && newWidth < 750) {
        //     targetPane.style.width = `${newWidth}px`;
        // }
    };

    const setupResizer = (divider, targetPane, isLeft) => {
        divider.addEventListener("mousedown", (e) => {
            e.preventDefault();
            const onMouseMove = (event) =>
                handleMouseMove(event, targetPane, isLeft);
            document.addEventListener("mousemove", onMouseMove);
            document.addEventListener("mouseup", () => {
                document.removeEventListener("mousemove", onMouseMove);
            });
        });
    };

    setupResizer(leftDivider, chatHistoryPane, true);
}

/**
 * Initializes the sidebar logic.
 */
export function initializeSidebar() {
    // Attach event listeners to toggle buttons
    const chatHistoryToggleButton = document.getElementById('chatHistoryToggleButton');
    const optionsToggleButton = document.getElementById('optionsSidebarToggleButton'); // Ensure an ID exists

    if (chatHistoryToggleButton) {
        chatHistoryToggleButton.addEventListener('click', () => toggleSidebar('left'));
    } else {
        console.warn('Chat History Toggle Button is missing.');
    }

    if (optionsToggleButton) {
// Add event listener for closing the dialog when clicking outside
document.addEventListener('click', function(event) {
    if (event.target === settingsDialog) {
        settingsDialog.classList.add('hidden');
    }
});

// Add event listener for closing the dialog when pressing Escape
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape' && !settingsDialog.classList.contains('hidden')) {
        settingsDialog.classList.add('hidden');
    }
});
        optionsToggleButton.addEventListener('click', () => toggleSidebar('options'));
    } else {
        console.warn('Options Toggle Button is missing.');
    }

    // Setup resizable sidebars
    setupResizableSidebars();
}
