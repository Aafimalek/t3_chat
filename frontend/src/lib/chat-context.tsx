'use client';

import { createContext, useContext, useState, useCallback, ReactNode, useEffect, useRef } from 'react';
import { useUser } from '@clerk/nextjs';
import {
    Message,
    ModelInfo,
    ConversationSummary,
    sendMessage,
    streamMessage,
    getModels,
    getConversations,
    getConversation,
    deleteConversation as apiDeleteConversation,
    uploadRagDocument,
    getRagDocumentCount,
    ToolMetadata,
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
    isAuthenticated: boolean;

    // Tool settings
    searchEnabled: boolean;
    setSearchEnabled: (enabled: boolean) => void;
    documentCount: number;
    lastToolMetadata: ToolMetadata | null;

    // Actions
    sendChatMessage: (content: string) => Promise<void>;
    startNewChat: () => void;
    selectConversation: (id: string) => Promise<void>;
    deleteConversation: (id: string) => Promise<void>;
    setSelectedModel: (modelId: string) => void;
    refreshConversations: () => Promise<void>;
    uploadDocument: (file: File) => Promise<string | null>;
    refreshDocumentCount: () => Promise<void>;
}

const ChatContext = createContext<ChatContextType | null>(null);

// ============================================================================
// Provider
// ============================================================================

interface ChatProviderProps {
    children: ReactNode;
}

export function ChatProvider({ children }: ChatProviderProps) {
    // Clerk authentication
    const { user, isLoaded, isSignedIn } = useUser();

    // State
    const [messages, setMessages] = useState<Message[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [conversationId, setConversationId] = useState<string | null>(null);
    const [conversations, setConversations] = useState<ConversationSummary[]>([]);
    const [selectedModel, setSelectedModel] = useState('llama-3.3-70b-versatile');
    const [models, setModels] = useState<ModelInfo[]>([]);

    // Tool state
    const [searchEnabled, setSearchEnabled] = useState(false);
    const [documentCount, setDocumentCount] = useState(0);
    const [lastToolMetadata, setLastToolMetadata] = useState<ToolMetadata | null>(null);

    // Track the current conversation ID in a ref for immediate access in callbacks
    // This solves the closure issue where state updates don't reflect immediately
    const conversationIdRef = useRef<string | null>(null);

    // Get user ID from Clerk or use a default for non-authenticated users
    const userId = user?.id || 'anonymous-user';
    const isAuthenticated = isSignedIn ?? false;
    
    // Keep ref in sync with state
    useEffect(() => {
        conversationIdRef.current = conversationId;
    }, [conversationId]);

    // Load models on mount
    useEffect(() => {
        getModels()
            .then(setModels)
            .catch(console.error);
    }, []);

    // Load conversations when user changes
    useEffect(() => {
        if (isLoaded) {
            refreshConversations();
        }
    }, [isLoaded, userId]);

    const refreshConversations = useCallback(async () => {
        try {
            const convos = await getConversations(userId);
            setConversations(convos);
        } catch (err) {
            console.error('Failed to load conversations:', err);
        }
    }, [userId]);

    const refreshDocumentCount = useCallback(async () => {
        if (!conversationId) {
            setDocumentCount(0);
            return;
        }
        try {
            const count = await getRagDocumentCount(conversationId, userId);
            setDocumentCount(count);
        } catch (err) {
            console.error('Failed to get document count:', err);
            setDocumentCount(0);
        }
    }, [conversationId, userId]);

    const uploadDocument = useCallback(async (file: File): Promise<string | null> => {
        try {
            // Use ref to get current conversation ID
            const currentConversationId = conversationIdRef.current;
            const result = await uploadRagDocument(file, userId, currentConversationId || undefined);
            // If this was a new conversation, update the conversation ID
            if (!currentConversationId && result.conversation_id) {
                setConversationId(result.conversation_id);
                conversationIdRef.current = result.conversation_id;
            }
            // Refresh document count
            setDocumentCount(prev => prev + 1);
            return result.conversation_id;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to upload document');
            return null;
        }
    }, [userId]);

    const sendChatMessage = useCallback(async (content: string) => {
        if (!content.trim()) return;

        setIsLoading(true);
        setError(null);
        setLastToolMetadata(null);

        // Add user message immediately
        const userMessage: Message = {
            role: 'user',
            content,
            timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, userMessage]);

        // Add empty assistant message for streaming
        const assistantMessage: Message = {
            role: 'assistant',
            content: '',
            timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, assistantMessage]);

        try {
            let fullResponse = '';

            // Determine tool mode based on search toggle
            const toolMode = searchEnabled ? 'search' : 'auto';

            // Use the ref for conversation ID to get the most current value
            // This fixes the issue where subsequent messages in a new chat
            // would use stale null value from closure
            const currentConversationId = conversationIdRef.current;

            // Debug logging
            console.log('[sendChatMessage] Sending message with:', {
                currentConversationId,
                conversationIdRefValue: conversationIdRef.current,
                conversationIdState: conversationId,
                toolMode,
                searchEnabled,
            });

            // Use streaming API
            for await (const chunk of streamMessage({
                message: content,
                user_id: userId,
                conversation_id: currentConversationId || undefined,
                model_name: selectedModel,
                tool_mode: toolMode,
                use_rag: documentCount > 0,
            })) {
                // Check if this is metadata object (from 'done' event)
                // Must check for object type AND that it has conversation_id property
                if (chunk !== null && typeof chunk === 'object' && 'conversation_id' in chunk) {
                    const doneData = chunk as { conversation_id: string; model_used: string; tool_metadata?: ToolMetadata };
                    
                    console.log('[sendChatMessage] Received done event:', {
                        receivedConversationId: doneData.conversation_id,
                        currentRefValue: conversationIdRef.current,
                        willUpdate: !conversationIdRef.current,
                        toolMetadata: doneData.tool_metadata,
                    });
                    
                    // ALWAYS update conversation ID from response if we don't have one
                    // This ensures subsequent messages use the correct conversation
                    if (!conversationIdRef.current && doneData.conversation_id) {
                        console.log('[sendChatMessage] Setting conversation ID to:', doneData.conversation_id);
                        setConversationId(doneData.conversation_id);
                        conversationIdRef.current = doneData.conversation_id;
                        console.log('[sendChatMessage] conversationIdRef.current is now:', conversationIdRef.current);
                    }
                    
                    // Store tool metadata if present
                    if (doneData.tool_metadata) {
                        setLastToolMetadata(doneData.tool_metadata);
                    }
                } else if (typeof chunk === 'string') {
                    // Regular content chunk
                    fullResponse += chunk;

                    // Update the last message with accumulated content
                    setMessages(prev => {
                        const updated = [...prev];
                        if (updated.length > 0) {
                            updated[updated.length - 1] = {
                                ...updated[updated.length - 1],
                                content: fullResponse,
                            };
                        }
                        return updated;
                    });
                }
            }
            
            console.log('[sendChatMessage] Stream completed. Final conversationIdRef.current:', conversationIdRef.current);
            
            // Debug: log the final state
            console.log('[sendChatMessage] Final state check:', {
                conversationIdRef: conversationIdRef.current,
                conversationIdState: conversationId,
                fullResponseLength: fullResponse.length,
            });

            // Always refresh conversations list to update message count in sidebar
            await refreshConversations();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to send message');
            // Remove the last two messages on error (user + empty assistant)
            setMessages(prev => prev.slice(0, -2));
        } finally {
            setIsLoading(false);
        }
    }, [selectedModel, userId, refreshConversations, searchEnabled, documentCount]);

    const startNewChat = useCallback(() => {
        setMessages([]);
        setConversationId(null);
        conversationIdRef.current = null;
        setError(null);
        setDocumentCount(0);
        setLastToolMetadata(null);
        setSearchEnabled(false);
    }, []);

    const selectConversation = useCallback(async (id: string) => {
        try {
            setIsLoading(true);
            const conversation = await getConversation(id, userId);
            setMessages(conversation.messages);
            setConversationId(id);
            conversationIdRef.current = id;
            setSelectedModel(conversation.model_name);
            // Reset tool state and fetch document count for this conversation
            setSearchEnabled(false);
            setLastToolMetadata(null);
            // Fetch document count for the conversation
            const count = await getRagDocumentCount(id, userId);
            setDocumentCount(count);
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
        isAuthenticated,
        searchEnabled,
        setSearchEnabled,
        documentCount,
        lastToolMetadata,
        sendChatMessage,
        startNewChat,
        selectConversation,
        deleteConversation,
        setSelectedModel,
        refreshConversations,
        uploadDocument,
        refreshDocumentCount,
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
