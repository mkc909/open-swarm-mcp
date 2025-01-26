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
 * Toggles the visibility of the left sidebar.
 */
function toggleLeftSidebar() {
    const chatHistoryPane = document.getElementById('chatHistoryPane');
    const leftSidebarHideBtn = document.getElementById('leftSidebarHideBtn');
    const leftSidebarRevealBtn = document.getElementById('leftSidebarRevealBtn');

    if (!chatHistoryPane || !leftSidebarHideBtn || !leftSidebarRevealBtn) {
        console.warn('Elements for toggling left sidebar are missing.');
        return;
    }

    const isHidden = chatHistoryPane.classList.toggle('hidden');
    leftSidebarHideBtn.classList.toggle('hidden', isHidden);
    leftSidebarRevealBtn.classList.toggle('hidden', !isHidden);

    showToast(isHidden ? "Chat history minimized." : "Chat history expanded.", "info");
}

/**
 * Toggles the visibility of the right sidebar.
 */
function toggleRightSidebar() {
    const optionsPane = document.getElementById('optionsPane');
    const optionsSidebarHideBtn = document.getElementById('optionsSidebarHideBtn');
    const optionsSidebarRevealBtn = document.getElementById('optionsSidebarRevealBtn');

    if (!optionsPane || !optionsSidebarHideBtn || !optionsSidebarRevealBtn) {
        console.warn('Elements for toggling right sidebar are missing.');
        return;
    }

    const isHidden = optionsPane.classList.toggle('hidden');
    optionsSidebarHideBtn.classList.toggle('hidden', isHidden);
    optionsSidebarRevealBtn.classList.toggle('hidden', !isHidden);

    showToast(isHidden ? "Settings pane minimized." : "Settings pane expanded.", "info");
}

/**
 * Sets up resizable sidebars with draggable dividers.
 */
function setupResizableSidebars() {
    const leftDivider = document.getElementById("divider-left");
    const rightDivider = document.getElementById("divider-right");
    const chatHistoryPane = document.querySelector(".chat-history-pane");
    const optionsPane = document.querySelector(".options-pane");

    const handleMouseMove = (e, targetPane, isLeft) => {
        const newWidth = isLeft
            ? e.clientX - chatHistoryPane.getBoundingClientRect().left
            : optionsPane.getBoundingClientRect().right - e.clientX;
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

    if (leftDivider) setupResizer(leftDivider, chatHistoryPane, true);
    if (rightDivider) setupResizer(rightDivider, optionsPane, false);
}

/**
 * Initializes the sidebar logic.
 */
export function initializeSidebar() {
    toggleLeftSidebar();
    toggleRightSidebar();
    setupResizableSidebars();
}
