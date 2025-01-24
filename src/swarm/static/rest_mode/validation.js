// validation.js - Validates messages and chat history for correct structure

// Validate a single tool call
function validateToolCall(toolCall) {
    if (typeof toolCall.id !== "string" || toolCall.id.trim() === "") {
        return "Tool call ID must be a non-empty string.";
    }
    if (
        !toolCall.function ||
        typeof toolCall.function.name !== "string" ||
        toolCall.function.name.trim() === ""
    ) {
        return "Function name in tool call must be a non-empty string.";
    }
    if (typeof toolCall.function.arguments !== "string") {
        return "Function arguments in tool call must be a string.";
    }
    if (toolCall.type && toolCall.type !== "function") {
        return "Tool call type, if provided, must be 'function'.";
    }
    return null; // No errors
}

// Validate a single message
function validateMessage(message) {
    if (!["user", "assistant", "tool"].includes(message.role)) {
        return `Invalid role: ${message.role}. Must be 'user', 'assistant', or 'tool'.`;
    }
    if (typeof message.content !== "string" || message.content.trim() === "") {
        return "Content must be a non-empty string.";
    }

    if (message.tool_calls) {
        if (!Array.isArray(message.tool_calls)) {
            return "Tool calls must be an array.";
        }
        for (const toolCall of message.tool_calls) {
            const error = validateToolCall(toolCall);
            if (error) return error; // Return the first error found
        }
    }

    return null; // No errors
}

// Validate the entire chat history
function validateChatHistory(chatHistory) {
    if (!Array.isArray(chatHistory)) {
        return "Chat history must be an array.";
    }

    for (let i = 0; i < chatHistory.length; i++) {
        const error = validateMessage(chatHistory[i]);
        if (error) return `Message ${i}: ${error}`;
    }

    return null; // No errors
}

// Export validation functions
export { validateMessage, validateChatHistory };
