import { showToast } from './toast.js';

/**
 * Toggles the visibility of a sidebar.
 * @param {string} sidebar - 'left' for Chat History or 'options' for Settings.
 * @param {boolean} shouldShow - true to show the sidebar, false to hide.
 */
export function toggleSidebar(sidebar, shouldShow) {
    const container = document.querySelector('.container');
    const leftSidebarHideBtn = document.getElementById("leftSidebarHideBtn");
    const leftSidebarRevealBtn = document.getElementById("leftSidebarRevealBtn");
    const optionsSidebarHideBtn = document.getElementById("optionsSidebarHideBtn");
    const optionsSidebarRevealBtn = document.getElementById("optionsSidebarRevealBtn");

    if (!container) return;

    if (sidebar === 'left') {
        const chatHistoryPane = document.getElementById('chatHistoryPane');
        if (shouldShow) {
            chatHistoryPane.style.display = 'block';
            leftSidebarRevealBtn.style.display = 'none';
            leftSidebarHideBtn.style.display = 'flex';
            showToast("📜 Chat History sidebar shown.", "info");
        } else {
            chatHistoryPane.style.display = 'none';
            leftSidebarHideBtn.style.display = 'none';
            leftSidebarRevealBtn.style.display = 'flex';
            showToast("📜 Chat History sidebar hidden.", "info");
        }
    } else if (sidebar === 'options') {
        const optionsPane = document.getElementById('optionsPane');
        if (shouldShow) {
            optionsPane.style.display = 'block';
            optionsSidebarRevealBtn.style.display = 'none';
            optionsSidebarHideBtn.style.display = 'flex';
            showToast("⚙️ Settings sidebar shown.", "info");
        } else {
            optionsPane.style.display = 'none';
            optionsSidebarHideBtn.style.display = 'none';
            optionsSidebarRevealBtn.style.display = 'flex';
            showToast("⚙️ Settings sidebar hidden.", "info");
        }
    }
}

/**
 * Makes a sidebar resizable by dragging a divider.
 * @param {HTMLElement} divider - The divider element to drag.
 */
export function makeResizable(divider) {
    let isResizing = false;

    divider.addEventListener('mousedown', function(e) {
        e.preventDefault();
        isResizing = true;
        document.addEventListener('mousemove', resizeSidebar);
        document.addEventListener('mouseup', stopResizing);
    });

    function resizeSidebar(e) {
        if (!isResizing) return;
        const container = document.querySelector('.container');
        const chatHistoryPane = document.getElementById('chatHistoryPane');
        const optionsPane = document.getElementById('optionsPane');

        if (!container || !chatHistoryPane || !optionsPane) return;

        const containerRect = container.getBoundingClientRect();
        const newLeftWidth = e.clientX - containerRect.left - divider.offsetWidth / 2;
        const newRightWidth = containerRect.right - e.clientX - divider.offsetWidth / 2;

        // Set minimum and maximum widths
        const minWidth = 150; // Minimum sidebar width
        const maxLeftWidth = containerRect.width - 300; // Maximum left sidebar width
        const maxRightWidth = containerRect.width - 300; // Maximum right sidebar width

        if (newLeftWidth >= minWidth && newLeftWidth <= maxLeftWidth) {
            chatHistoryPane.style.flex = '0 0 ' + newLeftWidth + 'px';
        }
        if (newRightWidth >= minWidth && newRightWidth <= maxRightWidth) {
            optionsPane.style.flex = '0 0 ' + newRightWidth + 'px';
        }
    }

    function stopResizing() {
        isResizing = false;
        document.removeEventListener('mousemove', resizeSidebar);
        document.removeEventListener('mouseup', stopResizing);
    }
}

/**
 * Initializes sidebar-related event listeners.
 * Should be called once during application initialization.
 */
export function initializeSidebar() {
    const resizableDivider = document.getElementById('resizableDivider');
    if (resizableDivider) {
        makeResizable(resizableDivider);
    }
}
