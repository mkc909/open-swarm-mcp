        // Initialize chat history
        let chatHistory = [];

        const messageHistory = document.getElementById("messageHistory");
        const rawMessagesContent = document.getElementById("rawMessagesContent");
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        const rawToggle = document.getElementById("rawToggle");
        const rawMessagesPane = document.getElementById("rawMessagesPane");
        const debugToggle = document.getElementById("debugToggle");
        const debugPane = document.getElementById("debugPane");
        const debugContent = document.getElementById("debugContent");

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
        window.renderMessage = function(role, message, sender = "Unknown", metadata = {}) {
            console.log("renderMessage called with:", { role, message, sender, metadata });

            const container = document.createElement("div");
            container.className = `message ${role}`;

            const header = document.createElement("h4");
            header.textContent = sender;
            header.className = "sender-header";
            container.appendChild(header);

            const content = document.createElement("p");
            content.textContent = message?.content || "No content provided.";
            container.appendChild(content);

            const messageHistory = document.getElementById("messageHistory");
            if (!messageHistory) {
                console.error("messageHistory element not found!");
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

        // Assign a default sender if missing
        const finalSender = sender || (role === "tool" ? "Tool" : "Unknown");

        // Correctly map tool_call_id and tool_name based on metadata structure
        const toolCallId = metadata.id || metadata.tool_call_id || null;
        const toolName = (metadata.function && metadata.function.name) ? metadata.function.name : metadata.tool_name || null;

        const rawData = {
            role: role,
            sender: finalSender, // Include sender in rawData
            tool_call_id: toolCallId,
            tool_name: toolName,
            content: content.content
        };

        // Display raw JSON in a <pre> block for better readability
        const pre = document.createElement("pre");
        pre.textContent = JSON.stringify(rawData, null, 2);
        rawMessage.appendChild(pre);

        rawMessagesContent.appendChild(rawMessage);
        rawMessagesContent.scrollTop = rawMessagesContent.scrollHeight;

        console.log("Appended Raw Message:", rawData);
    }

    /**
     * Renders debug information in the Debug pane.
     * @param {string} role - The role of the sender.
     * @param {object} content - The message content.
     * @param {string} sender - The display name of the sender.
     * @param {object} metadata - The metadata associated with the message.
     */
    window.renderDebugInfo = function (role, content, sender, metadata) {
        const debugMessage = document.createElement("div");
        debugMessage.className = "debug-message";

        const roleSpan = document.createElement("span");
        if (role === "user") {
            roleSpan.className = "debug-role-user";
            roleSpan.textContent = "User";
        } else if (role === "assistant") {
            roleSpan.className = "debug-role-assistant";
            roleSpan.textContent = "Assistant";
        } else if (role === "tool") {
            roleSpan.className = "debug-role-tool";
            roleSpan.textContent = "Tool";
        } else {
            roleSpan.textContent = role;
        }

        // Assign a default sender if missing
        const finalSender = sender || (role === "tool" ? "Tool" : "Unknown");

        // Parse metadata
        const parsedMetadata = parseMetadata(metadata);

        // Format boolean fields with colors
        const refusalFormatted = formatBoolean(parsedMetadata.refusal);
        const audioFormatted = parsedMetadata.audio !== null ? (parsedMetadata.audio ? formatBoolean(true) : formatBoolean(false)) : "N/A";
        const functionCallFormatted = parsedMetadata.function_call || "None";
        const toolCallsFormatted = parsedMetadata.tool_calls ? JSON.stringify(parsedMetadata.tool_calls, null, 2) : "None";

        debugMessage.innerHTML = `<strong>Role:</strong> ${roleSpan.outerHTML}<br/>
                                    <strong>Sender:</strong> ${finalSender}<br/>
                                    <strong>Refusal:</strong> ${refusalFormatted}<br/>
                                    <strong>Audio:</strong> ${audioFormatted}<br/>
                                    <strong>Function Call:</strong> ${functionCallFormatted}<br/>
                                    <strong>Tool Calls:</strong> ${toolCallsFormatted}<br/>`;

        debugContent.appendChild(debugMessage);
        debugContent.scrollTop = debugContent.scrollHeight;

        console.log(`Rendered debug info for message - Role: ${role}, Sender: ${finalSender}`);
    }

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
     * Toggles the visibility of the Raw Messages pane.
     */
    window.toggleRawMessages = function() {
        if (rawToggle.checked) {
            rawMessagesPane.style.display = "block";
        } else {
            rawMessagesPane.style.display = "none";
            rawMessagesContent.innerHTML = ""; // Clear raw messages when hidden
        }
    }

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
     * Sends the entire chat history to the server and displays the assistant's response.
     * @param {string|null} messageText - Optional text to send instead of user input.
     */
    async function handleSubmit(messageText = null) {
        const userInput = document.getElementById("userInput");
        const userMessageContent = messageText ? messageText : userInput.value.trim();
        if (!userMessageContent) return;

        // Clear the input field if not sending a predefined message
        if (!messageText) {
            userInput.value = "";
        }

        // Create user message object
        const userMessage = {
            role: "user",
            content: userMessageContent,
            sender: "User",
            metadata: {}
        };

        // Add user's message to chat history
        chatHistory.push(userMessage);

        // Render the user's message
        renderMessage(userMessage.role, { content: userMessage.content }, userMessage.sender, userMessage.metadata);
        appendRawMessage(userMessage.role, { content: userMessage.content }, userMessage.sender, userMessage.metadata);

        if (debugToggle.checked) {
            renderDebugInfo(userMessage.role, { content: userMessage.content }, userMessage.sender, userMessage.metadata);
        }

        try {
            // Extract blueprint ID from URL
            const urlPath = window.location.pathname;
            const blueprintId = urlPath.split("/").filter(Boolean).pop();

            console.log("Submitting model ID:", blueprintId); // Log the model ID

            if (!blueprintId) {
                console.error("Error: Blueprint ID is missing.");
                alert("Unable to identify the blueprint. Please check the URL.");
                return;
            }

            // Send the entire chat history to /v1/chat/completions
            const response = await fetch("/v1/chat/completions", {
                method: "POST",
                headers: { 
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken, // Include CSRF token
                },
                body: JSON.stringify({
                    model: blueprintId, // Use the extracted blueprint ID
                    messages: chatHistory.map(msg => ({
                        role: msg.role,
                        content: msg.content,
                        sender: msg.sender,
                        tool_calls: msg.metadata.tool_calls || undefined // Include tool_calls if present
                    })),
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            const data = await response.json();
            console.log("Chat completions response:", data); // Log the response

            if (data && data.choices && data.choices.length > 0) {
                const assistantResponse = data.choices[0].message;
                const assistantMessage = assistantResponse?.content || 'No response.';
                const assistantSender = assistantResponse?.sender || 'Assistant'; // Default to 'Assistant' if sender is missing
                const toolCalls = assistantResponse?.tool_calls || [];

                // Create assistant message object
                const assistantMsgObject = {
                    role: "assistant",
                    content: assistantMessage,
                    sender: assistantSender,
                    metadata: assistantResponse
                };

                // Add assistant's message to chat history
                chatHistory.push(assistantMsgObject);

                // Render assistant's message
                renderMessage(assistantMsgObject.role, { content: assistantMsgObject.content }, assistantMsgObject.sender, assistantMsgObject.metadata);
                appendRawMessage(assistantMsgObject.role, { content: assistantMsgObject.content }, assistantMsgObject.sender, assistantMsgObject.metadata);

                if (debugToggle.checked && assistantMsgObject.metadata) {
                    renderDebugInfo(assistantMsgObject.role, { content: assistantMsgObject.content }, assistantMsgObject.sender, assistantMsgObject.metadata);
                }

                // Render tool calls if any
                toolCalls.forEach(toolCall => {
                    const toolMessageContent = toolCall.content || "";
                    const toolCallId = toolCall.id || toolCall.tool_call_id || null;
                    const toolName = (toolCall.function && toolCall.function.name) ? toolCall.function.name : toolCall.tool_name || "Unknown Tool";

                    console.log(`Processing tool call - ID: ${toolCallId}, Name: ${toolName}, Content: ${toolMessageContent}`);

                    // Create tool message object
                    const toolMsgObject = {
                        role: "tool",
                        content: toolMessageContent,
                        sender: `Tool: ${toolName}`,
                        metadata: toolCall
                    };

                    // Add tool message to chat history
                    chatHistory.push(toolMsgObject);

                    // Render tool message
                    renderMessage(toolMsgObject.role, { content: toolMsgObject.content }, toolMsgObject.sender, toolMsgObject.metadata);
                    appendRawMessage(toolMsgObject.role, { content: toolMsgObject.content }, toolMsgObject.sender, toolMsgObject.metadata);

                    if (debugToggle.checked && toolMsgObject.metadata) {
                        renderDebugInfo(toolMsgObject.role, { content: toolMsgObject.content }, toolMsgObject.sender, toolMsgObject.metadata);
                    }
                });
            } else {
                // Handle cases where no response is received
                const noResponseMessage = {
                    role: "assistant",
                    content: "No response received.",
                    sender: "Assistant",
                    metadata: {}
                };
                chatHistory.push(noResponseMessage);
                renderMessage(noResponseMessage.role, { content: noResponseMessage.content }, noResponseMessage.sender, noResponseMessage.metadata);
                appendRawMessage(noResponseMessage.role, { content: noResponseMessage.content }, noResponseMessage.sender, noResponseMessage.metadata);
            }
        } catch (error) {
            console.error("Error submitting chat completion:", error);
            const errorMessage = {
                role: "assistant",
                content: "Error occurred. Please try again.",
                sender: "Assistant",
                metadata: {}
            };
            chatHistory.push(errorMessage);
            renderMessage(errorMessage.role, { content: errorMessage.content }, errorMessage.sender, errorMessage.metadata);
            appendRawMessage(errorMessage.role, { content: errorMessage.content }, errorMessage.sender, errorMessage.metadata);
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

document.addEventListener("DOMContentLoaded", () => {
    console.log("DOM fully loaded");

    // Fetch blueprint metadata on page load
    fetchBlueprintMetadata();

    // Test the renderMessage function
    renderMessage(welcomeMessage.role, { content: welcomeMessage.content }, welcomeMessage.sender, welcomeMessage.metadata);
});
