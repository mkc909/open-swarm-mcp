document.addEventListener("DOMContentLoaded", () => {
    // Add event listener for HTMX after swap events to handle dropdown updates
    document.addEventListener("htmx:afterSwap", (event) => {
        const targetId = event.target.id;

        // Check if the swap target is the blueprint dropdown
        if (targetId === "blueprintDropdown") {
            // Attach click listeners to dynamically created dropdown items
            event.target.querySelectorAll(".dropdown-item").forEach((item) => {
                item.addEventListener("click", () => {
                    // Retrieve blueprint name and conversation ID
                    const blueprintName = item.getAttribute("data-blueprint-name");
                    const conversationId = "new"; // Use 'new' or dynamically assign a conversation ID

                    // Redirect to the chat view for the selected blueprint
                    if (blueprintName) {
                        window.location.href = `/django_chat/${blueprintName}/${conversationId}/`;
                    }
                });
            });
        }
    });
});
