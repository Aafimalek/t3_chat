'use client';

import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Paperclip, Search, Sparkles, Code, BookOpen, Globe, ArrowUp, ChevronDown, Loader2 } from 'lucide-react';
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

interface ChatAreaProps {
    isSidebarOpen: boolean;
    toggleSidebar: () => void;
}

export function ChatArea({ isSidebarOpen, toggleSidebar }: ChatAreaProps) {
    const [inputValue, setInputValue] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const {
        messages,
        isLoading,
        error,
        sendChatMessage,
        selectedModel,
        setSelectedModel,
        models
    } = useChat();

    // Auto-scroll to bottom when messages change
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSend = async () => {
        if (!inputValue.trim() || isLoading) return;
        const message = inputValue;
        setInputValue('');
        await sendChatMessage(message);
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
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
                        <Button variant="ghost" size="icon" onClick={toggleSidebar} className="text-muted-foreground hover:text-foreground">
                            <PanelLeftOpen size={20} />
                        </Button>
                    )}
                </div>
                <div className="flex items-center gap-2">
                    <div className="flex items-center gap-2 bg-muted/50 rounded-full px-3 py-1.5 border border-border/50">
                        <span className="text-xs font-medium text-muted-foreground mr-1">Theme</span>
                        <ThemeToggle />
                    </div>
                </div>
            </header>

            {/* Messages Area or Empty State */}
            <main className="flex-1 flex flex-col items-center justify-center p-4 md:p-8 overflow-hidden">
                {showEmptyState ? (
                    <div className="flex flex-col items-center max-w-3xl w-full text-center space-y-8 animate-in fade-in zoom-in duration-500">
                        <h1 className="text-3xl font-semibold tracking-tight text-foreground">
                            How can I help you?
                        </h1>

                        {/* Quick Actions */}
                        <div className="flex flex-wrap items-center justify-center gap-2">
                            <Button variant="outline" className="rounded-full gap-2 border-border/50 bg-background/50 backdrop-blur-sm hover:bg-muted/80">
                                <Sparkles size={16} className="text-purple-500" />
                                Create
                            </Button>
                            <Button variant="outline" className="rounded-full gap-2 border-border/50 bg-background/50 backdrop-blur-sm hover:bg-muted/80">
                                <Globe size={16} className="text-blue-500" />
                                Explore
                            </Button>
                            <Button variant="outline" className="rounded-full gap-2 border-border/50 bg-background/50 backdrop-blur-sm hover:bg-muted/80">
                                <Code size={16} className="text-green-500" />
                                Code
                            </Button>
                            <Button variant="outline" className="rounded-full gap-2 border-border/50 bg-background/50 backdrop-blur-sm hover:bg-muted/80">
                                <BookOpen size={16} className="text-orange-500" />
                                Learn
                            </Button>
                        </div>
                    </div>
                ) : (
                    <ScrollArea className="flex-1 w-full max-w-3xl">
                        <div className="flex flex-col gap-6 py-8 pt-16">
                            {messages.map((message, index) => (
                                <div
                                    key={index}
                                    className={cn(
                                        "flex gap-4 animate-in fade-in slide-in-from-bottom-2 duration-300",
                                        message.role === 'user' ? 'justify-end' : 'justify-start'
                                    )}
                                >
                                    <div
                                        className={cn(
                                            "max-w-[85%] rounded-2xl px-4 py-3",
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
                                            <div className="prose prose-sm dark:prose-invert max-w-none">
                                                <ReactMarkdown
                                                    components={{
                                                        // Custom styling for markdown elements
                                                        p: ({ children }) => (
                                                            <p className="text-sm leading-relaxed mb-2 last:mb-0">{children}</p>
                                                        ),
                                                        strong: ({ children }) => (
                                                            <strong className="font-semibold text-foreground">{children}</strong>
                                                        ),
                                                        em: ({ children }) => (
                                                            <em className="italic">{children}</em>
                                                        ),
                                                        code: ({ children, className }) => {
                                                            const isInline = !className;
                                                            return isInline ? (
                                                                <code className="bg-muted px-1.5 py-0.5 rounded text-xs font-mono text-pink-500">
                                                                    {children}
                                                                </code>
                                                            ) : (
                                                                <code className={className}>{children}</code>
                                                            );
                                                        },
                                                        pre: ({ children }) => (
                                                            <pre className="bg-muted/80 rounded-lg p-3 overflow-x-auto text-xs my-2">
                                                                {children}
                                                            </pre>
                                                        ),
                                                        ul: ({ children }) => (
                                                            <ul className="list-disc list-inside space-y-1 text-sm my-2">{children}</ul>
                                                        ),
                                                        ol: ({ children }) => (
                                                            <ol className="list-decimal list-inside space-y-1 text-sm my-2">{children}</ol>
                                                        ),
                                                        li: ({ children }) => (
                                                            <li className="text-sm">{children}</li>
                                                        ),
                                                        h1: ({ children }) => (
                                                            <h1 className="text-lg font-bold mb-2">{children}</h1>
                                                        ),
                                                        h2: ({ children }) => (
                                                            <h2 className="text-base font-bold mb-2">{children}</h2>
                                                        ),
                                                        h3: ({ children }) => (
                                                            <h3 className="text-sm font-bold mb-1">{children}</h3>
                                                        ),
                                                        blockquote: ({ children }) => (
                                                            <blockquote className="border-l-2 border-pink-500 pl-3 my-2 italic text-muted-foreground">
                                                                {children}
                                                            </blockquote>
                                                        ),
                                                        a: ({ href, children }) => (
                                                            <a
                                                                href={href}
                                                                className="text-pink-500 hover:text-pink-400 underline"
                                                                target="_blank"
                                                                rel="noopener noreferrer"
                                                            >
                                                                {children}
                                                            </a>
                                                        ),
                                                    }}
                                                >
                                                    {message.content}
                                                </ReactMarkdown>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}

                            {isLoading && (
                                <div className="flex gap-4 animate-in fade-in duration-300">
                                    <div className="bg-muted/50 rounded-2xl px-4 py-3 border border-border/50">
                                        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                                    </div>
                                </div>
                            )}

                            {error && (
                                <div className="flex justify-center">
                                    <div className="bg-destructive/10 text-destructive rounded-lg px-4 py-2 text-sm">
                                        {error}
                                    </div>
                                </div>
                            )}

                            <div ref={messagesEndRef} />
                        </div>
                    </ScrollArea>
                )}
            </main>

            {/* Input Area */}
            <div className="w-full flex justify-center p-4 pb-6 md:pb-10">
                <div className="w-full max-w-3xl relative">
                    <div className="absolute top-0 transform -translate-y-full w-full flex justify-center pb-2">
                        <p className="text-xs text-muted-foreground/60 text-center">
                            Make sure you agree to our <span className="underline cursor-pointer hover:text-foreground">Terms</span> and <span className="underline cursor-pointer hover:text-foreground">Privacy Policy</span>
                        </p>
                    </div>
                    <div className="relative rounded-2xl bg-muted/30 border border-border/50 focus-within:ring-1 focus-within:ring-ring focus-within:bg-muted/50 transition-all shadow-sm overflow-hidden">
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
                                            className="h-auto flex items-center gap-1.5 text-xs font-medium text-muted-foreground bg-background/50 px-2 py-1 rounded-md border border-border/50 hover:bg-background/80"
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

                                <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full text-muted-foreground hover:bg-background/80">
                                    <Search size={16} />
                                </Button>
                                <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full text-muted-foreground hover:bg-background/80">
                                    <Paperclip size={16} />
                                </Button>
                            </div>
                            <Button
                                size="icon"
                                className="h-8 w-8 rounded-lg bg-pink-600 hover:bg-pink-700 text-white shadow-md disabled:opacity-50"
                                onClick={handleSend}
                                disabled={isLoading || !inputValue.trim()}
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
        </div>
    );
}
