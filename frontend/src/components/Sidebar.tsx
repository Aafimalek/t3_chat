'use client';

import React from 'react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import {
    Plus,
    PanelLeftClose,
    LogIn,
    Search,
    Trash2,
} from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import { useChat } from '@/lib/chat-context';

interface SidebarProps {
    isOpen: boolean;
    toggleSidebar: () => void;
}

export function Sidebar({ isOpen, toggleSidebar }: SidebarProps) {
    const {
        conversations,
        conversationId,
        selectConversation,
        deleteConversation,
        startNewChat,
        isLoading
    } = useChat();

    // Group conversations by date
    const groupedConversations = React.useMemo(() => {
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);
        const weekAgo = new Date(today);
        weekAgo.setDate(weekAgo.getDate() - 7);

        const groups: { [key: string]: typeof conversations } = {
            'Today': [],
            'Yesterday': [],
            'Previous 7 Days': [],
            'Older': [],
        };

        conversations.forEach(conv => {
            const date = new Date(conv.updated_at);
            if (date.toDateString() === today.toDateString()) {
                groups['Today'].push(conv);
            } else if (date.toDateString() === yesterday.toDateString()) {
                groups['Yesterday'].push(conv);
            } else if (date > weekAgo) {
                groups['Previous 7 Days'].push(conv);
            } else {
                groups['Older'].push(conv);
            }
        });

        return groups;
    }, [conversations]);

    const handleDeleteConversation = (e: React.MouseEvent, convId: string) => {
        e.stopPropagation();
        deleteConversation(convId);
    };

    return (
        <div
            className={cn(
                'relative flex flex-col h-full bg-sidebar border-r border-sidebar-border transition-all duration-300 ease-in-out flex-shrink-0',
                isOpen ? 'w-64' : 'w-[0px] border-none overflow-hidden'
            )}
        >
            {/* Header */}
            <div className="flex flex-col gap-2 p-4">
                <div className="flex items-center justify-between">
                    <h1 className="text-xl font-bold font-sans tracking-tight text-sidebar-foreground">
                        T3.chat
                    </h1>
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={toggleSidebar}
                        className="text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                    >
                        <PanelLeftClose size={20} />
                    </Button>
                </div>

                <Button
                    className="w-full justify-start gap-2 bg-pink-600 hover:bg-pink-700 text-white shadow-lg shadow-pink-900/20"
                    size="lg"
                    onClick={startNewChat}
                >
                    <Plus size={18} />
                    <span className="font-semibold">New Chat</span>
                </Button>
            </div>

            {/* Search */}
            <div className="px-4 pb-2">
                <div className="relative">
                    <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground pointer-events-none" />
                    <Input
                        placeholder="Search your threads..."
                        className="pl-8 bg-sidebar-accent/50 border-sidebar-border focus-visible:ring-1 focus-visible:ring-sidebar-ring"
                    />
                </div>
            </div>


            {/* History List */}
            <ScrollArea className="flex-1 px-2">
                <div className="flex flex-col gap-1 p-2">
                    {Object.entries(groupedConversations).map(([group, convos]) => (
                        convos.length > 0 && (
                            <div key={group} className="mb-2">
                                <p className="text-xs text-muted-foreground/60 px-2 py-1 uppercase tracking-wide">
                                    {group}
                                </p>
                                {convos.map((conv) => (
                                    <div
                                        key={conv.id}
                                        className={cn(
                                            "flex items-center justify-between h-auto py-3 px-3 w-full text-left font-normal rounded-md cursor-pointer group transition-colors",
                                            conv.id === conversationId
                                                ? "bg-sidebar-accent text-sidebar-accent-foreground"
                                                : "text-sidebar-foreground hover:bg-sidebar-accent/50",
                                            isLoading && "opacity-50 pointer-events-none"
                                        )}
                                        onClick={() => selectConversation(conv.id)}
                                    >
                                        <div className="flex flex-col gap-0.5 overflow-hidden flex-1">
                                            <span className="truncate text-sm font-medium">{conv.title}</span>
                                            <span className="text-xs text-muted-foreground/60">
                                                {conv.message_count} messages
                                            </span>
                                        </div>
                                        <button
                                            className="h-6 w-6 flex items-center justify-center rounded opacity-0 group-hover:opacity-100 hover:bg-destructive/20 hover:text-destructive transition-opacity"
                                            onClick={(e) => handleDeleteConversation(e, conv.id)}
                                        >
                                            <Trash2 size={14} />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )
                    ))}

                    {conversations.length === 0 && (
                        <p className="text-sm text-muted-foreground text-center py-8">
                            No conversations yet. Start a new chat!
                        </p>
                    )}
                </div>
            </ScrollArea>

            {/* Footer */}
            <div className="p-4 mt-auto border-t border-sidebar-border">
                <Button variant="ghost" className="w-full justify-start gap-2 text-sidebar-foreground hover:bg-sidebar-accent">
                    <LogIn size={18} />
                    Login
                </Button>
            </div>
        </div>
    );
}
