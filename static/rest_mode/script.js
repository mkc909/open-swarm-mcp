        // Initialize chat history and context variables
        let chatHistory = [];
        let contextVariables = { active_agent_name: null };

        const messageHistory = document.getElementById("messageHistory");
        const rawMessagesContent = document.getElementById("rawMessagesContent");
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        const rawToggle = document.getElementById("rawToggle");
        const rawMessagesPane = document.getElementById("rawMessagesPane");
        const debugToggle = document.getElementById("debugToggle");
        const debugPane = document.getElementById("debugPane");
        const debugContent = document.getElementById("debugContent");

        /**
         * Renders the active agent in the debug pane.
         */
        function renderActiveAgentInDebug() {
            const activeAgent = contextVariables.active_agent_name || "Unknown";
            const activeAgentElement = document.createElement("div");
            activeAgentElement.className = "debug-active-agent";
            activeAgentElement.innerHTML = `<strong>Active Agent:</strong> ${activeAgent}`;
            debugContent.appendChild(activeAgentElement);
            debugContent.scrollTop = debugContent.scrollHeight;
        }

        /**
         * Generates a unique tool_call_id.
         * @returns {string} - A unique identifier for tool calls.
         */
        window.generateToolCallId = function() {
            return 'call_' + Math.random().toString(36).substr(2, 9);
        }

        /**
         * Fetches and displays blueprint metadata based on the URL path.
         */
        window.fetchBlueprintMetadata = async function() {
            try {
                // Extract blueprint ID from the URL path
                const urlPath = window.location.pathname;
                const blueprintId = urlPath.split("/").filter(Boolean).pop(); // Get the last segment of the path

                console.log("Extracted blueprintId:", blueprintId); // Log the extracted ID

                if (!blueprintId) {
                    document.getElementById("blueprintMetadata").innerHTML = `
                        <h2>Error</h2>
                        <p>Blueprint ID is missing from the URL.</p>
                    `;
                    return;
                }

                // Fetch all models from /v1/models
                const response = await fetch("/v1/models");
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                const data = await response.json();

                console.log("Fetched data:", data); // Log the response data

                if (data && data.data && data.data.length > 0) {
                    // Find the matching blueprint by ID
                    const blueprint = data.data.find(bp => bp.id === blueprintId);
                    console.log("Matched blueprint:", blueprint); // Log the matched blueprint

                    if (blueprint) {
                        document.getElementById("blueprintMetadata").innerHTML = `
                            <h2>${blueprint.title || "Blueprint Title"}</h2>
                            <p>${blueprint.description || "No description available."}</p>
                        `;
                    } else {
                        document.getElementById("blueprintMetadata").innerHTML = `
                            <h2>Error</h2>
                            <p>No matching blueprint found for ID: ${blueprintId}.</p>
                        `;
                    }
                } else {
                    document.getElementById("blueprintMetadata").innerHTML = `
                        <h2>Error</h2>
                        <p>Unable to fetch blueprint metadata.</p>
                    `;
                }
            } catch (error) {
                console.error("Error fetching blueprint metadata:", error);
                document.getElementById("blueprintMetadata").innerHTML = `
                    <h2>Error</h2>
                    <p>Unable to fetch blueprint metadata.</p>
                `;
            }
        }

        /**
         * Renders a single message in the chat interface.
         * @param {string} role - The role of the sender ('user', 'assistant', or 'tool').
         * @param {object} message - The message content.
         * @param {string} sender - The display name of the sender.
         * @param {object|null} metadata - Optional debug information.
         */
        window.renderMessage = function (role, message, sender = null, metadata = {}) {
            console.log("Rendering message:", { role, message, sender, metadata });
        
            const container = document.createElement("div");
            container.className = `message ${role}`;
        
            // Determine the sender (default to Assistant for non-user roles)
            const finalSender = sender || (role === "user" ? "User" : "Assistant");
            const header = document.createElement("h4");
            header.textContent = finalSender;
            header.className = "sender-header";
            container.appendChild(header);
        
            // Handle content rendering with newlines as <br>
            const content = document.createElement("p");
            content.innerHTML = (message?.content || "No content provided.").replace(/\n/g, "<br>");
            container.appendChild(content);
        
            const messageHistory = document.getElementById("messageHistory");
            if (!messageHistory) {
                console.error("Message history element not found!");
                return;
            }
        
            messageHistory.appendChild(container);
            messageHistory.scrollTop = messageHistory.scrollHeight;
        
            console.log("Message rendered successfully");
        };
                                                
    /**
     * Appends raw message data to the Raw Messages pane.
     * @param {string} role - The role of the sender.
     * @param {object} content - The message content.
     * @param {string} sender - The display name of the sender.
     * @param {object} metadata - The metadata associated with the message.
     */
    window.appendRawMessage = function(role, content, sender, metadata) {
        const rawMessage = document.createElement("div");
        rawMessage.className = "raw-message";
    
        const rawData = {
            role: role,
            sender: sender || "Unknown",
            content: content.content || "No content provided.",
            metadata: metadata // Retain full metadata for backend processing
        };
    
        const pre = document.createElement("pre");
        pre.textContent = JSON.stringify(rawData, null, 2);
        rawMessage.appendChild(pre);
    
        const rawMessagesContent = document.getElementById("rawMessagesContent");
        if (!rawMessagesContent) {
            console.error("Raw messages content element not found!");
            return;
        }
    
        rawMessagesContent.appendChild(rawMessage);
        rawMessagesContent.scrollTop = rawMessagesContent.scrollHeight;
    
        console.log("Appended Raw Message:", rawData);
    };
                
    /**
     * Renders debug information in the Debug pane.
     * @param {string} role - The role of the sender.
     * @param {object} content - The message content.
     * @param {string} sender - The display name of the sender.
     * @param {object} metadata - The metadata associated with the message.
     */
    window.renderDebugInfo = function (role, content, sender, metadata) {
        debugContent.innerHTML = ""; // Clear the debug pane before adding new debug info

        const debugMessage = document.createElement("div");
        debugMessage.className = "debug-message";

        const roleSpan = document.createElement("span");
        roleSpan.className = role === "user" ? "debug-role-user" : "debug-role-assistant";
        roleSpan.textContent = role;

        const finalSender = sender || "Unknown";

        const metadataContent = metadata ? JSON.stringify(metadata, null, 2) : "None";
        debugMessage.innerHTML = `<strong>Role:</strong> ${roleSpan.outerHTML}<br/>
                                    <strong>Sender:</strong> ${finalSender}<br/>
                                    <strong>Content:</strong> ${content.content || "No content"}<br/>
                                    <strong>Metadata:</strong><pre>${metadataContent}</pre>`;

        debugContent.appendChild(debugMessage);

        // Render the active agent as part of debug info
        renderActiveAgentInDebug();
        console.log(`Rendered debug info for message - Role: ${role}, Sender: ${finalSender}`);
    };

    /**
     * Parses the metadata object to extract relevant fields.
     * @param {object} metadata - The metadata associated with the message.
     * @returns {object} - Parsed metadata with specific fields.
     */
    window.parseMetadata = function (metadata) {
        return {
            refusal: metadata.refusal || null,
            role: metadata.role || null,
            audio: metadata.audio || null,
            function_call: metadata.function_call || null,
            tool_calls: metadata.tool_calls || null,
            sender: metadata.sender || null
        };
    }

    /**
     * Formats boolean values with colored text.
     * @param {boolean|null} value - The boolean value to format.
     * @returns {string} - HTML string with colored boolean.
     */
    window.formatBoolean = function(value) {
        if (value === true) {
            return `<span class="debug-boolean-true">True</span>`;
        } else if (value === false) {
            return `<span class="debug-boolean-false">False</span>`;
        } else {
            return "N/A";
        }
    }

    /**
     * Toggles the visibility of the Raw Messages pane and logs raw messages to the console if enabled.
     */
    window.toggleRawMessages = function() {
        if (rawToggle.checked) {
            rawMessagesPane.style.display = "block";

            // Log all raw messages in chatHistory to the console
            console.log("Raw Messages Pane Toggled On. Printing all raw messages:");
            chatHistory.forEach((msg, index) => {
                console.log(`Message #${index + 1}:`, msg);
            });
        } else {
            rawMessagesPane.style.display = "none";
            rawMessagesContent.innerHTML = ""; // Clear raw messages when hidden
        }
    };

    /**
     * Toggles the visibility of the Debug pane.
     */
    window.toggleDebugPane = function() {
        if (debugToggle.checked) {
            debugPane.style.display = "block";
        } else {
            debugPane.style.display = "none";
            debugContent.innerHTML = ""; // Clear debug content when hidden
        }
    }

    /**
     * Handles the submission of a user message.
     * Sends the entire chat history and context variables to the server.
     * @param {string|null} messageText - Optional text to send instead of user input.
     */
    async function handleSubmit(messageText = null) {
        const userInput = document.getElementById("userInput");
        const userMessageContent = messageText ? messageText : userInput.value.trim();

        if (!userMessageContent) return;

        // Clear the input field
        if (!messageText) userInput.value = "";

        const userMessage = {
            role: "user",
            content: userMessageContent,
            sender: "User",
            metadata: {},
        };

        // Append the user's message to the chat history
        chatHistory.push(userMessage);

        // Render the message in the UI
        renderMessage(userMessage.role, { content: userMessage.content }, userMessage.sender, userMessage.metadata);
        appendRawMessage(userMessage.role, { content: userMessage.content }, userMessage.sender, userMessage.metadata);

        try {

            // Extract the model name from the current URL
            const urlPath = window.location.pathname;
            const modelName = urlPath.split("/").filter(Boolean).pop(); // Get the last segment of the URL

            console.log("Submitting message to model:", modelName);

            const response = await fetch("/v1/chat/completions", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken,
                },
                body: JSON.stringify({
                    model: modelName, // Dynamically pass the model name
                    messages: chatHistory, // Send the full chat history
                    context_variables: contextVariables, // Include context variables
                }),
            });

            if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);

            const data = await response.json();
            processAssistantResponse(data.choices, data.context_variables); // Pass updated context variables
        } catch (error) {
            console.error("Error submitting message:", error);
        }
    }

    /**
     * Processes the assistant's response and updates context variables.
     * @param {Array} choices - The choices from the assistant's response.
     * @param {object} updatedContextVariables - Updated context variables from the server.
     */
    function processAssistantResponse(choices, updatedContextVariables) {
        if (!choices || !Array.isArray(choices)) {
            console.error("Invalid choices array:", choices);
            return;
        }

        // Update the local context variables
        contextVariables = { ...contextVariables, ...updatedContextVariables };

        console.log("Processing assistant response with choices:", choices);

        choices.forEach(choice => {
            const rawMessage = { ...choice.message }; // Store the raw message
            chatHistory.push(rawMessage);

            const role = rawMessage.role || "assistant";
            const content = rawMessage.content ?? "No content"; // Ensure fallback
            const sender = rawMessage.sender || (role === "user" ? "User" : "Assistant");
            const metadata = { ...rawMessage };

            console.log("Rendering message with:", { role, content, sender, metadata });

            // Render and log messages
            renderMessage(role, { content }, sender, metadata);
            appendRawMessage(role, { content }, sender, metadata);

            if (debugToggle && debugToggle.checked) {
                renderDebugInfo(role, { content }, sender, metadata);
            }
        });

        console.log("Assistant response processed successfully.");
    }              

    function processToolCall(toolCall) {
        let content = toolCall.content || "No content.";
        const toolCallId = toolCall.id || toolCall.tool_call_id || "N/A";
        const toolName = toolCall.function?.name || toolCall.tool_name || "Unknown Tool";
    
        // Parse content safely
        try {
            if (typeof content === "string") {
                content = JSON.parse(content); // Parse only if it's a string
            }
        } catch (error) {
            console.error(`Failed to parse tool call content: ${content}`, error);
        }
    
        console.log(`Processing tool call - ID: ${toolCallId}, Name: ${toolName}, Content:`, content);
    
        const toolMessage = {
            role: "tool",
            content: JSON.stringify(content, null, 2), // Render as a readable JSON string
            sender: `Tool: ${toolName}`,
            metadata: toolCall // Pass the entire toolCall object as metadata
        };
    
        chatHistory.push(toolMessage);
        renderMessage(toolMessage.role, { content: toolMessage.content }, toolMessage.sender, toolMessage.metadata);
        appendRawMessage(toolMessage.role, { content: toolMessage.content }, toolMessage.sender, toolMessage.metadata);
    
        if (debugToggle.checked) {
            renderDebugInfo(toolMessage.role, { content: toolMessage.content }, toolMessage.sender, toolMessage.metadata);
        }
    }
    
    /**
     * Handles user decision on tool calls (Approve or Deny).
     * Sends the decision to the backend for processing.
     * @param {string} decision - 'approved' or 'denied'.
     * @param {object} toolMessage - The tool call message object.
     */
    window.handleToolCallDecision = async function(decision, toolMessage) {
        console.log(`User has ${decision} the tool call: ${toolMessage.tool_name}(${toolMessage.content})`);

        // Create user decision message object
        const decisionMessage = {
            role: "user",
            content: decision,
            sender: "User",
            metadata: {}
        };

        // Add user's decision to chat history
        chatHistory.push(decisionMessage);

        // Render user's decision message
        renderMessage(decisionMessage.role, { content: decisionMessage.content }, decisionMessage.sender, decisionMessage.metadata);
        appendRawMessage(decisionMessage.role, { content: decisionMessage.content }, decisionMessage.sender, decisionMessage.metadata);

        if (debugToggle.checked) {
            renderDebugInfo(decisionMessage.role, { content: decisionMessage.content }, decisionMessage.sender, decisionMessage.metadata);
        }

        try {
            // Send the tool call decision to /v1/tool_call_decision
            const response = await fetch("/v1/chat/completions", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken, // Include CSRF token
                },
                body: JSON.stringify({
                    decision: decision, // 'approved' or 'denied'
                    tool_call_id: toolMessage.tool_call_id || toolMessage.id || null, // Include tool_call_id if available
                    function_name: toolMessage.tool_name || (toolMessage.function && toolMessage.function.name) || null,
                    arguments: toolMessage.function && toolMessage.function.arguments ? JSON.parse(toolMessage.function.arguments) : {},
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            const data = await response.json();
            console.log("Tool call decision response:", data);

            if (data.status === "success") {
                // Create assistant message object for success
                const successMessage = {
                    role: "assistant",
                    content: data.result || "Tool function executed successfully.",
                    sender: "Assistant",
                    metadata: {}
                };

                // Add to chat history
                chatHistory.push(successMessage);

                // Render assistant's success message
                renderMessage(successMessage.role, { content: successMessage.content }, successMessage.sender, successMessage.metadata);
                appendRawMessage(successMessage.role, { content: successMessage.content }, successMessage.sender, successMessage.metadata);

                if (debugToggle.checked) {
                    renderDebugInfo(successMessage.role, { content: successMessage.content }, successMessage.sender, successMessage.metadata);
                }
            } else if (data.status === "denied") {
                // Create assistant message object for denial
                const deniedMessage = {
                    role: "assistant",
                    content: data.message || "Tool call was denied.",
                    sender: "Assistant",
                    metadata: {}
                };

                // Add to chat history
                chatHistory.push(deniedMessage);

                // Render assistant's denial message
                renderMessage(deniedMessage.role, { content: deniedMessage.content }, deniedMessage.sender, deniedMessage.metadata);
                appendRawMessage(deniedMessage.role, { content: deniedMessage.content }, deniedMessage.sender, deniedMessage.metadata);

                if (debugToggle.checked) {
                    renderDebugInfo(deniedMessage.role, { content: deniedMessage.content }, deniedMessage.sender, deniedMessage.metadata);
                }
            } else {
                // Handle other statuses
                const errorMsg = {
                    role: "assistant",
                    content: data.message || "An error occurred.",
                    sender: "Assistant",
                    metadata: {}
                };

                chatHistory.push(errorMsg);
                renderMessage(errorMsg.role, { content: errorMsg.content }, errorMsg.sender, errorMsg.metadata);
                appendRawMessage(errorMsg.role, { content: errorMsg.content }, errorMsg.sender, errorMsg.metadata);

                if (debugToggle.checked) {
                    renderDebugInfo(errorMsg.role, { content: errorMsg.content }, errorMsg.sender, errorMsg.metadata);
                }
            }
        } catch (error) {
            console.error("Error sending tool call decision:", error);
            const errorMessage = {
                role: "assistant",
                content: "There was an error processing your decision. Please try again.",
                sender: "Assistant",
                metadata: {}
            };
            chatHistory.push(errorMessage);
            renderMessage(errorMessage.role, { content: errorMessage.content }, errorMessage.sender, errorMessage.metadata);
            appendRawMessage(errorMessage.role, { content: errorMessage.content }, errorMessage.sender, errorMessage.metadata);
        }
    }

    /**
     * Handles the 'Enter' key press to submit the form.
     * @param {KeyboardEvent} event
     */
    window.handleKeyPress = function(event) {
        if (event.key === "Enter") {
            event.preventDefault(); // Prevent form submission if inside a form
            handleSubmit();
        }
    }

const welcomeMessage = {
    role: "assistant",
    content: "Welcome to Open Swarm!",
    sender: "Assistant",
    metadata: {}
};

let rawHistory = [];

document.addEventListener("DOMContentLoaded", () => {
    console.log("DOM fully loaded");

    // Fetch blueprint metadata on page load
    fetchBlueprintMetadata();

    // Test the renderMessage function
    renderMessage(welcomeMessage.role, { content: welcomeMessage.content }, welcomeMessage.sender, welcomeMessage.metadata);
});
