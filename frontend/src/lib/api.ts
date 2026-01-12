/**
 * API client for T3.chat backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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
 */
export async function* streamMessage(
    request: ChatRequest
): AsyncGenerator<string, void, unknown> {
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

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = line.slice(6);
                if (data && data !== '[DONE]') {
                    yield data;
                }
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
