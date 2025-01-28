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

        // Update the toggle button icon based on visibility
        const toggleIcon = chatHistoryToggleButton.querySelector('img');
        if (isHidden) {
            toggleIcon.src = window.STATIC_URLS.layoutSidebarLeftExpand; // Expanded icon
            toggleIcon.alt = "Expand Chat History Pane";
            showToast("📜 Chat History sidebar hidden.", "info");
        } else {
            toggleIcon.src = window.STATIC_URLS.layoutSidebarLeftCollapse; // Collapsed icon
            toggleIcon.alt = "Collapse Chat History Pane";
            showToast("📜 Chat History sidebar shown.", "info");
        }
    } else if (sidebar === 'options') {
        const optionsPane = document.getElementById('optionsPane');
        const optionsToggleButton = document.getElementById('optionsSidebarToggleButton'); // Ensure an ID

        if (!optionsPane || !optionsToggleButton) {
            console.warn('Options Pane or Toggle Button is missing.');
            return;
        }

        const isHidden = optionsPane.classList.toggle('hidden');

        // Update the toggle button icon based on visibility
        const toggleIcon = optionsToggleButton.querySelector('img');
        if (isHidden) {
            toggleIcon.src = window.STATIC_URLS.layoutSidebarRightExpand; // Expanded icon
            toggleIcon.alt = "Expand Options Pane";
            showToast("⚙️ Settings sidebar hidden.", "info");
        } else {
            toggleIcon.src = window.STATIC_URLS.layoutSidebarRightCollapse; // Collapsed icon
            toggleIcon.alt = "Collapse Options Pane";
            showToast("⚙️ Settings sidebar shown.", "info");
        }
    }
}

/**
 * Sets up resizable sidebars with draggable dividers.
 */
function setupResizableSidebars() {
    const leftDivider = document.getElementById("divider-left");
    const rightDivider = document.getElementById("divider-right");
    const chatHistoryPane = document.getElementById('chatHistoryPane');
    const optionsPane = document.getElementById('optionsPane');

    if (!leftDivider || !rightDivider || !chatHistoryPane || !optionsPane) {
        console.warn('One or more elements for resizable sidebars are missing.');
        return;
    }

    const handleMouseMove = (e, targetPane, isLeft) => {
        const newWidth = isLeft
            ? e.clientX - chatHistoryPane.getBoundingClientRect().left
            : window.innerWidth - e.clientX - optionsPane.getBoundingClientRect().left;
        if (newWidth > 100 && newWidth < 500) {
            targetPane.style.width = `${newWidth}px`;
        }
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
    setupResizer(rightDivider, optionsPane, false);
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
        optionsToggleButton.addEventListener('click', () => toggleSidebar('options'));
    } else {
        console.warn('Options Toggle Button is missing.');
    }

    // Setup resizable sidebars
    setupResizableSidebars();
}
