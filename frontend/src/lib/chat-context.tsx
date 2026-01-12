'use client';

import { createContext, useContext, useState, useCallback, ReactNode, useEffect } from 'react';
import {
    Message,
    ModelInfo,
    ConversationSummary,
    sendMessage,
    getModels,
    getConversations,
    getConversation,
    deleteConversation as apiDeleteConversation,
} from '@/lib/api';

// ============================================================================
// Types
// ============================================================================

interface ChatContextType {
    // Messages
    messages: Message[];
    isLoading: boolean;
    error: string | null;

    // Conversation
    conversationId: string | null;
    conversations: ConversationSummary[];

    // Model
    selectedModel: string;
    models: ModelInfo[];

    // User
    userId: string;

    // Actions
    sendChatMessage: (content: string) => Promise<void>;
    startNewChat: () => void;
    selectConversation: (id: string) => Promise<void>;
    deleteConversation: (id: string) => Promise<void>;
    setSelectedModel: (modelId: string) => void;
    refreshConversations: () => Promise<void>;
}

const ChatContext = createContext<ChatContextType | null>(null);

// ============================================================================
// Provider
// ============================================================================

interface ChatProviderProps {
    children: ReactNode;
}

export function ChatProvider({ children }: ChatProviderProps) {
    // State
    const [messages, setMessages] = useState<Message[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [conversationId, setConversationId] = useState<string | null>(null);
    const [conversations, setConversations] = useState<ConversationSummary[]>([]);
    const [selectedModel, setSelectedModel] = useState('llama-3.3-70b-versatile');
    const [models, setModels] = useState<ModelInfo[]>([]);

    // For now, use a simple user ID. In production, this would come from auth.
    const userId = 'default-user';

    // Load models on mount
    useEffect(() => {
        getModels()
            .then(setModels)
            .catch(console.error);
    }, []);

    // Load conversations on mount
    useEffect(() => {
        refreshConversations();
    }, []);

    const refreshConversations = useCallback(async () => {
        try {
            const convos = await getConversations(userId);
            setConversations(convos);
        } catch (err) {
            console.error('Failed to load conversations:', err);
        }
    }, [userId]);

    const sendChatMessage = useCallback(async (content: string) => {
        if (!content.trim()) return;

        setIsLoading(true);
        setError(null);

        // Add user message immediately
        const userMessage: Message = {
            role: 'user',
            content,
            timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, userMessage]);

        try {
            const response = await sendMessage({
                message: content,
                user_id: userId,
                conversation_id: conversationId || undefined,
                model_name: selectedModel,
            });

            // Add assistant message
            const assistantMessage: Message = {
                role: 'assistant',
                content: response.response,
                timestamp: new Date().toISOString(),
            };
            setMessages(prev => [...prev, assistantMessage]);

            // Update conversation ID if this was a new conversation
            if (!conversationId) {
                setConversationId(response.conversation_id);
                // Refresh conversations list
                refreshConversations();
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to send message');
            // Remove the user message on error
            setMessages(prev => prev.slice(0, -1));
        } finally {
            setIsLoading(false);
        }
    }, [conversationId, selectedModel, userId, refreshConversations]);

    const startNewChat = useCallback(() => {
        setMessages([]);
        setConversationId(null);
        setError(null);
    }, []);

    const selectConversation = useCallback(async (id: string) => {
        try {
            setIsLoading(true);
            const conversation = await getConversation(id, userId);
            setMessages(conversation.messages);
            setConversationId(id);
            setSelectedModel(conversation.model_name);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load conversation');
        } finally {
            setIsLoading(false);
        }
    }, [userId]);

    const deleteConversation = useCallback(async (id: string) => {
        try {
            await apiDeleteConversation(id, userId);
            setConversations(prev => prev.filter(c => c.id !== id));
            // If we deleted the current conversation, start a new chat
            if (id === conversationId) {
                startNewChat();
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to delete conversation');
        }
    }, [conversationId, startNewChat, userId]);

    const value: ChatContextType = {
        messages,
        isLoading,
        error,
        conversationId,
        conversations,
        selectedModel,
        models,
        userId,
        sendChatMessage,
        startNewChat,
        selectConversation,
        deleteConversation,
        setSelectedModel,
        refreshConversations,
    };

    return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

// ============================================================================
// Hook
// ============================================================================

export function useChat() {
    const context = useContext(ChatContext);
    if (!context) {
        throw new Error('useChat must be used within a ChatProvider');
    }
    return context;
}
