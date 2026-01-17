'use client';

import React, { useState, useRef, useEffect } from 'react';
import { MarkdownRenderer } from './MarkdownRenderer';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Paperclip, Search, Sparkles, Code, BookOpen, Globe, ArrowUp, ChevronDown, Loader2, ArrowDown } from 'lucide-react';
import { ThemeToggle } from './ThemeToggle';
import { PanelLeftOpen } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useChat } from '@/lib/chat-context';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ScrollArea } from '@/components/ui/scroll-area';
import { LoginPromptModal } from './LoginPromptModal';

interface ChatAreaProps {
    isSidebarOpen: boolean;
    toggleSidebar: () => void;
}

export function ChatArea({ isSidebarOpen, toggleSidebar }: ChatAreaProps) {
    const [inputValue, setInputValue] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const scrollViewportRef = useRef<HTMLDivElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [showScrollButton, setShowScrollButton] = useState(false);
    const [shouldAutoScroll, setShouldAutoScroll] = useState(true);
    const [showLoginModal, setShowLoginModal] = useState(false);
    const [isUploading, setIsUploading] = useState(false);

    const {
        messages,
        isLoading,
        error,
        sendChatMessage,
        selectedModel,
        setSelectedModel,
        models,
        isAuthenticated,
        searchEnabled,
        setSearchEnabled,
        documentCount,
        uploadDocument,
        lastToolMetadata,
        conversationId,
    } = useChat();

    // Smart auto-scroll logic
    const scrollToBottom = (instant = false) => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({
                behavior: instant ? 'auto' : 'smooth',
                block: 'end'
            });
            setShowScrollButton(false);
            setShouldAutoScroll(true);
        }
    };

    // Handle user scroll events
    const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
        const target = e.currentTarget;
        const { scrollTop, scrollHeight, clientHeight } = target;

        // Calculate distance from bottom
        const distanceFromBottom = scrollHeight - scrollTop - clientHeight;

        // If user scrolls up significantly (e.g., > 100px), disable auto-scroll
        if (distanceFromBottom > 100) {
            setShouldAutoScroll(false);
            setShowScrollButton(true);
        } else {
            // If user scrolls near bottom, re-enable auto-scroll
            setShouldAutoScroll(true);
            setShowScrollButton(false);
        }
    };

    // Auto-scroll when messages change or loading state changes
    useEffect(() => {
        if (shouldAutoScroll) {
            // Use instant scroll during loading for better performance with streaming
            scrollToBottom(isLoading);
        }
    }, [messages, isLoading, shouldAutoScroll]);

    const handleSend = async () => {
        if (!inputValue.trim() || isLoading) return;

        // Check authentication before sending
        if (!isAuthenticated) {
            setShowLoginModal(true);
            return;
        }

        const message = inputValue;
        setInputValue('');

        // Force scroll to bottom when sending
        setShouldAutoScroll(true);
        // Small timeout to ensure state update processes before scroll (optional but safe)
        setTimeout(() => scrollToBottom(false), 10);

        await sendChatMessage(message);
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        // Check authentication
        if (!isAuthenticated) {
            setShowLoginModal(true);
            return;
        }

        // Validate file type
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            alert('Only PDF files are supported');
            return;
        }

        setIsUploading(true);
        try {
            await uploadDocument(file);
        } catch (err) {
            console.error('Upload failed:', err);
        } finally {
            setIsUploading(false);
            // Reset input
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }
        }
    };

    const handleSearchToggle = () => {
        if (!isAuthenticated) {
            setShowLoginModal(true);
            return;
        }
        setSearchEnabled(!searchEnabled);
    };

    const selectedModelInfo = models.find(m => m.id === selectedModel);

    // Empty state when no messages
    const showEmptyState = messages.length === 0;

    return (
        <div className="flex flex-col h-full w-full relative bg-background text-foreground transition-colors duration-300">
            {/* Top Bar */}
            <header className="absolute top-0 left-0 right-0 p-4 flex items-center justify-between z-10">
                <div className="flex items-center gap-2">
                    {!isSidebarOpen && (
                        <Button variant="ghost" size="icon" onClick={toggleSidebar} className="text-muted-foreground hover:text-foreground hover:scale-110 boring:hover:scale-100 transition-all duration-200 boring:transition-none">
                            <PanelLeftOpen size={20} />
                        </Button>
                    )}
                </div>
                <div className="flex items-center gap-2">
                    <div className="flex items-center gap-2 bg-background/60 backdrop-blur-md px-3 py-1.5 border border-border/30 shadow-lg shadow-black/5 dark:shadow-black/20 transition-all duration-200 boring:transition-none hover:shadow-xl boring:hover:shadow-none hover:scale-105 boring:hover:scale-100">
                        <span className="text-xs font-medium text-muted-foreground mr-1">Theme</span>
                        <ThemeToggle />
                    </div>
                </div>
            </header>

            {/* Messages Area or Empty State */}
            <main className="flex-1 flex flex-col items-center justify-center p-4 md:p-8 overflow-hidden relative">
                {showEmptyState ? (
                    <div className="flex flex-col items-center max-w-3xl w-full text-center space-y-8 animate-in fade-in zoom-in duration-500">
                        <h1 className="text-3xl font-semibold tracking-tight text-foreground">
                            How can I help you?
                        </h1>

                        {/* Quick Actions */}
                        <div className="flex flex-wrap items-center justify-center gap-3">
                            <Button variant="outline" className="gap-2 border-border/30 bg-background/60 backdrop-blur-md shadow-lg shadow-purple-500/10 boring:shadow-none hover:shadow-purple-500/30 boring:hover:shadow-none hover:bg-muted/80 hover:scale-110 boring:hover:scale-100 transition-all duration-200 boring:transition-none">
                                <Sparkles size={16} className="text-purple-500 boring:text-muted-foreground" />
                                Create
                            </Button>
                            <Button variant="outline" className="gap-2 border-border/30 bg-background/60 backdrop-blur-md shadow-lg shadow-blue-500/10 boring:shadow-none hover:shadow-blue-500/30 boring:hover:shadow-none hover:bg-muted/80 hover:scale-110 boring:hover:scale-100 transition-all duration-200 boring:transition-none">
                                <Globe size={16} className="text-blue-500 boring:text-muted-foreground" />
                                Explore
                            </Button>
                            <Button variant="outline" className="gap-2 border-border/30 bg-background/60 backdrop-blur-md shadow-lg shadow-green-500/10 boring:shadow-none hover:shadow-green-500/30 boring:hover:shadow-none hover:bg-muted/80 hover:scale-110 boring:hover:scale-100 transition-all duration-200 boring:transition-none">
                                <Code size={16} className="text-green-500 boring:text-muted-foreground" />
                                Code
                            </Button>
                            <Button variant="outline" className="gap-2 border-border/30 bg-background/60 backdrop-blur-md shadow-lg shadow-orange-500/10 boring:shadow-none hover:shadow-orange-500/30 boring:hover:shadow-none hover:bg-muted/80 hover:scale-110 boring:hover:scale-100 transition-all duration-200 boring:transition-none">
                                <BookOpen size={16} className="text-orange-500 boring:text-muted-foreground" />
                                Learn
                            </Button>
                        </div>
                    </div>
                ) : (
                    <div className="flex-1 w-full max-w-3xl relative h-full">
                        <ScrollArea
                            className="h-full w-full"
                            viewportRef={scrollViewportRef}
                            onScroll={handleScroll}
                        >
                            <div className="flex flex-col gap-6 py-8 pt-16 px-4">
                                {messages.map((message, index) => (
                                    <div key={index}>
                                        {/* Show tool indicator for assistant messages */}
                                        {message.role === 'assistant' && index === messages.length - 1 && lastToolMetadata && (lastToolMetadata.search_used || lastToolMetadata.rag_used) && (
                                            <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2 animate-in fade-in duration-300">
                                                {lastToolMetadata.search_used && (
                                                    <span className="flex items-center gap-1 bg-blue-500/10 text-blue-500 px-2 py-0.5">
                                                        <Search size={12} />
                                                        Web search used
                                                    </span>
                                                )}
                                                {lastToolMetadata.rag_used && (
                                                    <span className="flex items-center gap-1 bg-green-500/10 text-green-500 px-2 py-0.5">
                                                        <Paperclip size={12} />
                                                        {lastToolMetadata.rag_chunks} doc chunk(s) used
                                                    </span>
                                                )}
                                            </div>
                                        )}
                                        <div
                                            className={cn(
                                                "flex gap-4 animate-in fade-in slide-in-from-bottom-2 duration-300",
                                                message.role === 'user' ? 'justify-end' : 'justify-start'
                                            )}
                                        >
                                            <div
                                                className={cn(
                                                    "max-w-[85%] px-4 py-3",
                                                    message.role === 'user'
                                                        ? 'bg-pink-600 text-white'
                                                        : 'bg-muted/50 text-foreground border border-border/50'
                                                )}
                                            >
                                                {message.role === 'user' ? (
                                                    <p className="text-sm whitespace-pre-wrap leading-relaxed">
                                                        {message.content}
                                                    </p>
                                                ) : (
                                                    <MarkdownRenderer
                                                        content={message.content}
                                                    />
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ))}

                                {isLoading && (
                                    <div className="flex gap-4 animate-in fade-in duration-300">
                                        <div className="bg-muted/50 px-4 py-3 border border-border/50">
                                            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                                        </div>
                                    </div>
                                )}

                                {error && (
                                    <div className="flex justify-center">
                                        <div className="bg-destructive/10 text-destructive px-4 py-2 text-sm">
                                            {error}
                                        </div>
                                    </div>
                                )}

                                <div ref={messagesEndRef} />
                            </div>
                        </ScrollArea>

                        {/* Scroll to bottom button */}
                        {showScrollButton && (
                            <Button
                                size="icon"
                                className="absolute bottom-4 right-8 h-8 w-8 bg-background/80 backdrop-blur-md border border-border shadow-lg animate-in fade-in zoom-in duration-200 hover:bg-muted hover:scale-110 boring:hover:scale-100 transition-all boring:transition-none"
                                onClick={() => scrollToBottom(false)}
                            >
                                <ArrowDown size={16} />
                            </Button>
                        )}
                    </div>
                )
                }
            </main>

            {/* Input Area */}
            <div className="w-full flex justify-center p-4 pb-6 md:pb-10">
                <div className="w-full max-w-3xl">
                    <div className="relative bg-background/70 backdrop-blur-xl border border-border/30 focus-within:ring-2 focus-within:ring-ring/50 focus-within:bg-background/80 focus-within:shadow-xl focus-within:shadow-primary/10 transition-all duration-300 shadow-lg shadow-black/5 dark:shadow-black/30 overflow-hidden">
                        <Textarea
                            ref={textareaRef}
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Type your message here..."
                            className="min-h-[60px] md:min-h-[80px] w-full resize-none border-none bg-transparent shadow-none p-4 focus-visible:ring-0 text-md"
                            disabled={isLoading}
                        />

                        <div className="flex items-center justify-between p-2 pl-4">
                            <div className="flex items-center gap-2">
                                {/* Model Selector */}
                                <DropdownMenu>
                                    <DropdownMenuTrigger asChild>
                                        <Button
                                            variant="ghost"
                                            className="h-auto flex items-center gap-1.5 text-xs font-medium text-muted-foreground bg-background/50 px-2 py-1 border border-border/50 hover:bg-background/80"
                                        >
                                            <span className="max-w-[120px] truncate">
                                                {selectedModelInfo?.name || selectedModel}
                                            </span>
                                            <ChevronDown size={14} />
                                        </Button>
                                    </DropdownMenuTrigger>
                                    <DropdownMenuContent align="start" className="w-64">
                                        {models.map((model) => (
                                            <DropdownMenuItem
                                                key={model.id}
                                                onClick={() => setSelectedModel(model.id)}
                                                className={cn(
                                                    "flex flex-col items-start gap-0.5 py-2",
                                                    model.id === selectedModel && "bg-accent"
                                                )}
                                            >
                                                <span className="font-medium">{model.name}</span>
                                                <span className="text-xs text-muted-foreground">
                                                    {model.description}
                                                </span>
                                            </DropdownMenuItem>
                                        ))}
                                    </DropdownMenuContent>
                                </DropdownMenu>

                                {/* Search Toggle */}
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className={cn(
                                        "h-8 w-8 transition-all duration-200 boring:transition-none",
                                        searchEnabled
                                            ? "bg-blue-500/20 boring:bg-muted text-blue-500 boring:text-muted-foreground hover:bg-blue-500/30 boring:hover:bg-muted hover:scale-110 boring:hover:scale-100"
                                            : "text-muted-foreground hover:bg-background/80 hover:scale-110 boring:hover:scale-100"
                                    )}
                                    onClick={handleSearchToggle}
                                    title={searchEnabled ? "Search enabled (click to disable)" : "Enable web search"}
                                >
                                    <Search size={16} />
                                </Button>

                                {/* File Upload */}
                                <div className="relative">
                                    <input
                                        type="file"
                                        ref={fileInputRef}
                                        onChange={handleFileUpload}
                                        accept=".pdf"
                                        className="hidden"
                                    />
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        className={cn(
                                            "h-8 w-8 transition-all duration-200 boring:transition-none",
                                            documentCount > 0
                                                ? "text-green-500 boring:text-muted-foreground hover:bg-green-500/20 boring:hover:bg-muted hover:scale-110 boring:hover:scale-100"
                                                : "text-muted-foreground hover:bg-background/80 hover:scale-110 boring:hover:scale-100"
                                        )}
                                        onClick={() => fileInputRef.current?.click()}
                                        disabled={isUploading}
                                        title={documentCount > 0 ? `${documentCount} document(s) uploaded` : "Upload PDF"}
                                    >
                                        {isUploading ? (
                                            <Loader2 size={16} className="animate-spin" />
                                        ) : (
                                            <Paperclip size={16} />
                                        )}
                                    </Button>
                                    {documentCount > 0 && (
                                        <span className="absolute -top-1 -right-1 h-4 w-4 text-[10px] font-bold bg-green-500 text-white flex items-center justify-center">
                                            {documentCount}
                                        </span>
                                    )}
                                </div>
                            </div>
                            <Button
                                size="icon"
                                className="h-8 w-8 bg-teal-600 dark:bg-pink-600 boring:bg-neutral-600 hover:bg-teal-700 dark:hover:bg-pink-700 boring:hover:bg-neutral-700 text-white shadow-md disabled:opacity-50 hover:scale-110 boring:hover:scale-100 hover:shadow-lg boring:hover:shadow-none transition-all duration-200"
                                onClick={handleSend}
                                disabled={isLoading || !inputValue.trim() || !isAuthenticated}
                                title={!isAuthenticated ? "Sign in to send messages" : "Send message"}
                            >
                                {isLoading ? (
                                    <Loader2 size={16} className="animate-spin" />
                                ) : (
                                    <ArrowUp size={16} />
                                )}
                            </Button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Login Prompt Modal */}
            <LoginPromptModal
                isOpen={showLoginModal}
                onClose={() => setShowLoginModal(false)}
            />
        </div>
    );
}
