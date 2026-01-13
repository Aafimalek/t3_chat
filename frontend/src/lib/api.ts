/**
 * API client for T3.chat backend
 */

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');

// ============================================================================
// Types
// ============================================================================

export interface Message {
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp?: string;
}

export interface ChatRequest {
    message: string;
    user_id: string;
    conversation_id?: string;
    model_name?: string;
}

export interface ChatResponse {
    response: string;
    conversation_id: string;
    model_used: string;
}

export interface Conversation {
    id: string;
    user_id: string;
    title: string;
    model_name: string;
    messages: Message[];
    created_at: string;
    updated_at: string;
}

export interface ConversationSummary {
    id: string;
    title: string;
    model_name: string;
    created_at: string;
    updated_at: string;
    message_count: number;
}

export interface ModelInfo {
    id: string;
    name: string;
    description: string;
    context_length: number;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Send a chat message and get a response
 */
export async function sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
    });

    if (!response.ok) {
        throw new Error(`Chat request failed: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Send a chat message and stream the response
 * Yields content chunks and a final metadata object with conversation_id
 */
export async function* streamMessage(
    request: ChatRequest
): AsyncGenerator<string | { conversation_id: string; model_used: string }, void, unknown> {
    const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
    });

    if (!response.ok) {
        throw new Error(`Stream request failed: ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error('No response body');

    const decoder = new TextDecoder();
    let buffer = '';

    // SSE State
    let currentEvent = 'message';
    let dataBuffer: string[] = [];

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        // Keep the last partial line in the buffer
        buffer = lines.pop() || '';

        for (const rawLine of lines) {
            // Remove carriage return if present (common in SSE over HTTP/Windows)
            const line = rawLine.endsWith('\r') ? rawLine.slice(0, -1) : rawLine;

            // Trim the line to check for emptiness (standard SSE allows \r)
            const trimmedLine = line.trim();

            if (trimmedLine === '') {
                // Empty line triggers event dispatch
                if (dataBuffer.length > 0) {
                    const fullData = dataBuffer.join('\n');

                    if (currentEvent === 'message') {
                        yield fullData;
                    } else if (currentEvent === 'done') {
                        try {
                            const meta = JSON.parse(fullData);
                            yield meta;
                        } catch {
                            // Ignore parse errors
                        }
                    }

                    // Reset buffers
                    dataBuffer = [];
                    currentEvent = 'message'; // Default event type
                }
                continue;
            }

            if (line.startsWith('event: ')) {
                currentEvent = line.slice(7).trim();
            } else if (line.startsWith('data:')) {
                // Strict SSE Spec implementation:
                // 1. Remove "data:" prefix (5 chars)
                let data = line.slice(5);
                // 2. If first char is space, remove it (and only one)
                if (data.startsWith(' ')) {
                    data = data.slice(1);
                }
                dataBuffer.push(data);
            }
        }
    }
}

/**
 * Get all available models
 */
export async function getModels(): Promise<ModelInfo[]> {
    const response = await fetch(`${API_BASE_URL}/api/models`);
    if (!response.ok) {
        throw new Error(`Failed to fetch models: ${response.statusText}`);
    }
    return response.json();
}

/**
 * Get user's conversations
 */
export async function getConversations(userId: string): Promise<ConversationSummary[]> {
    const response = await fetch(
        `${API_BASE_URL}/api/conversations?user_id=${encodeURIComponent(userId)}`
    );
    if (!response.ok) {
        throw new Error(`Failed to fetch conversations: ${response.statusText}`);
    }
    return response.json();
}

/**
 * Get a specific conversation with messages
 */
export async function getConversation(
    conversationId: string,
    userId: string
): Promise<Conversation> {
    const response = await fetch(
        `${API_BASE_URL}/api/conversations/${conversationId}?user_id=${encodeURIComponent(userId)}`
    );
    if (!response.ok) {
        throw new Error(`Failed to fetch conversation: ${response.statusText}`);
    }
    return response.json();
}

/**
 * Delete a conversation
 */
export async function deleteConversation(
    conversationId: string,
    userId: string
): Promise<void> {
    const response = await fetch(
        `${API_BASE_URL}/api/conversations/${conversationId}?user_id=${encodeURIComponent(userId)}`,
        { method: 'DELETE' }
    );
    if (!response.ok) {
        throw new Error(`Failed to delete conversation: ${response.statusText}`);
    }
}

/**
 * Update conversation title
 */
export async function updateConversationTitle(
    conversationId: string,
    userId: string,
    title: string
): Promise<Conversation> {
    const response = await fetch(
        `${API_BASE_URL}/api/conversations/${conversationId}?user_id=${encodeURIComponent(userId)}`,
        {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title }),
        }
    );
    if (!response.ok) {
        throw new Error(`Failed to update conversation: ${response.statusText}`);
    }
    return response.json();
}

// ============================================================================
// About You & Memory Types
// ============================================================================

export interface AboutYou {
    nickname: string;
    occupation: string;
    about: string;
    memory_enabled: boolean;
}

export interface MemoryItem {
    key: string;
    type: string;
    content: string;
    created_at: string;
}

// ============================================================================
// About You & Memory Functions
// ============================================================================

/**
 * Get user's About You settings
 */
export async function getAboutYou(userId: string): Promise<AboutYou> {
    const response = await fetch(
        `${API_BASE_URL}/api/users/${encodeURIComponent(userId)}/about`
    );
    if (!response.ok) {
        throw new Error(`Failed to fetch about you: ${response.statusText}`);
    }
    return response.json();
}

/**
 * Update user's About You settings
 */
export async function updateAboutYou(userId: string, about: AboutYou): Promise<AboutYou> {
    const response = await fetch(
        `${API_BASE_URL}/api/users/${encodeURIComponent(userId)}/about`,
        {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(about),
        }
    );
    if (!response.ok) {
        throw new Error(`Failed to update about you: ${response.statusText}`);
    }
    return response.json();
}

/**
 * Get user's memories
 */
export async function getMemories(userId: string): Promise<MemoryItem[]> {
    const response = await fetch(
        `${API_BASE_URL}/api/users/${encodeURIComponent(userId)}/memories`
    );
    if (!response.ok) {
        throw new Error(`Failed to fetch memories: ${response.statusText}`);
    }
    return response.json();
}

/**
 * Delete a specific memory
 */
export async function deleteMemory(userId: string, memoryKey: string): Promise<void> {
    const response = await fetch(
        `${API_BASE_URL}/api/users/${encodeURIComponent(userId)}/memories/${encodeURIComponent(memoryKey)}`,
        { method: 'DELETE' }
    );
    if (!response.ok) {
        throw new Error(`Failed to delete memory: ${response.statusText}`);
    }
}

/**
 * Clear all memories
 */
export async function clearMemories(userId: string): Promise<void> {
    const response = await fetch(
        `${API_BASE_URL}/api/users/${encodeURIComponent(userId)}/memories`,
        { method: 'DELETE' }
    );
    if (!response.ok) {
        throw new Error(`Failed to clear memories: ${response.statusText}`);
    }
}

