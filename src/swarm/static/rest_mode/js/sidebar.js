import { showToast } from './toast.js';

/* Existing toggleSidebar function */
export function toggleSidebar(sidebar, shouldShow) {
    const container = document.querySelector('.container');
    const leftSidebarRevealBtn = document.getElementById("leftSidebarRevealBtn");
    const leftSidebarHideBtn = document.getElementById("leftSidebarHideBtn");
    const optionsSidebarRevealBtn = document.getElementById("optionsSidebarRevealBtn");
    const optionsSidebarHideBtn = document.getElementById("optionsSidebarHideBtn");

    if (!container) return;

    if (sidebar === 'left') {
        const chatHistoryPane = document.getElementById('chatHistoryPane');
        if (shouldShow) {
            chatHistoryPane.style.display = 'block';
            leftSidebarRevealBtn.style.display = 'none';
            leftSidebarHideBtn.style.display = 'flex';
            leftSidebarRevealBtn.innerHTML = '←'; /* Arrow icon */
            showToast("📜 Chat History sidebar shown.", "info");
        } else {
            chatHistoryPane.style.display = 'none';
            leftSidebarHideBtn.style.display = 'none';
            leftSidebarRevealBtn.style.display = 'flex';
            leftSidebarRevealBtn.innerHTML = '→'; /* Arrow icon */
            showToast("📜 Chat History sidebar hidden.", "info");
        }
    } else if (sidebar === 'options') {
        const optionsPane = document.getElementById('optionsPane');
        optionsPane.classList.toggle('hidden');
        const isVisible = !optionsPane.classList.contains('hidden');
        optionsSidebarRevealBtn.style.display = isVisible ? 'none' : 'flex';
        optionsSidebarHideBtn.style.display = isVisible ? 'flex' : 'none';
        optionsSidebarRevealBtn.innerHTML = isVisible ? '→' : '←'; /* Arrow icon */
        showToast(isVisible ? "⚙️ Settings sidebar shown." : "⚙️ Settings sidebar hidden.", "info");
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
