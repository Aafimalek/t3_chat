'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import {
    Plus,
    PanelLeftClose,
    LogIn,
    Search,
    Trash2,
    LogOut,
    Settings,
} from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { useChat } from '@/lib/chat-context';
import { SignInButton, SignOutButton, useUser } from '@clerk/nextjs';
import { SettingsModal } from './SettingsModal';

interface SidebarProps {
    isOpen: boolean;
    toggleSidebar: () => void;
}

export function Sidebar({ isOpen, toggleSidebar }: SidebarProps) {
    const { user, isSignedIn, isLoaded } = useUser();
    const {
        conversations,
        conversationId,
        selectConversation,
        deleteConversation,
        startNewChat,
        isLoading,
        userId,
    } = useChat();

    const [settingsOpen, setSettingsOpen] = useState(false);

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
        <>
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
                            T3_chat
                        </h1>
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={toggleSidebar}
                            className="text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground hover:scale-110 boring:hover:scale-100 transition-all duration-200 boring:transition-none"
                        >
                            <PanelLeftClose size={20} />
                        </Button>
                    </div>

                    <Button
                        className="w-full justify-start gap-2 bg-teal-600 dark:bg-pink-600 boring:bg-neutral-600 hover:bg-teal-700 dark:hover:bg-pink-700 boring:hover:bg-neutral-700 text-white shadow-lg shadow-teal-900/20 dark:shadow-pink-900/20 boring:shadow-none hover:shadow-teal-900/40 dark:hover:shadow-pink-900/40 boring:hover:shadow-none hover:scale-105 boring:hover:scale-100 transition-all duration-200"
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
                                                "grid grid-cols-[1fr_auto] items-center py-2 px-3 w-full text-left font-normal cursor-pointer group transition-all duration-200 boring:transition-none gap-2 hover:scale-[1.02] boring:hover:scale-100",
                                                conv.id === conversationId
                                                    ? "bg-sidebar-accent text-sidebar-accent-foreground"
                                                    : "text-sidebar-foreground hover:bg-sidebar-accent/50",
                                                isLoading && "opacity-50 pointer-events-none"
                                            )}
                                            onClick={() => selectConversation(conv.id)}
                                        >
                                            <div className="flex flex-col gap-0.5 overflow-hidden min-w-0">
                                                <span className="truncate text-sm font-medium">{conv.title}</span>
                                                <span className="text-xs text-muted-foreground/60 truncate">
                                                    {conv.message_count} messages
                                                </span>
                                            </div>
                                            <button
                                                className="h-8 w-8 flex items-center justify-center bg-destructive/5 hover:bg-destructive/15 hover:text-destructive transition-all duration-200 boring:transition-none border border-destructive/20 hover:border-destructive/40 text-destructive/70 hover:scale-110 boring:hover:scale-100"
                                                onClick={(e) => handleDeleteConversation(e, conv.id)}
                                                title="Delete conversation"
                                                aria-label="Delete conversation"
                                            >
                                                <Trash2 size={16} />
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

                {/* Footer with User Profile */}
                <div className="p-4 mt-auto border-t border-sidebar-border space-y-2">
                    {isLoaded && (
                        isSignedIn ? (
                            <>
                                {/* Settings Button */}
                                <Button
                                    variant="ghost"
                                    className="w-full justify-start gap-2 text-sidebar-foreground hover:bg-sidebar-accent hover:scale-105 boring:hover:scale-100 transition-all duration-200 boring:transition-none"
                                    onClick={() => setSettingsOpen(true)}
                                >
                                    <Settings size={18} />
                                    Settings
                                </Button>

                                <div className="flex items-center gap-3 p-2 bg-sidebar-accent/30 transition-all duration-200 boring:transition-none hover:bg-sidebar-accent/50">
                                    <Avatar className="h-8 w-8">
                                        <AvatarImage src={user?.imageUrl} alt={user?.fullName || ''} />
                                        <AvatarFallback className="bg-teal-600 dark:bg-pink-600 boring:bg-neutral-600 text-white text-xs">
                                            {user?.firstName?.[0] || user?.emailAddresses?.[0]?.emailAddress?.[0]?.toUpperCase() || '?'}
                                        </AvatarFallback>
                                    </Avatar>
                                    <div className="flex-1 overflow-hidden">
                                        <p className="text-sm font-medium truncate text-sidebar-foreground">
                                            {user?.fullName || user?.firstName || 'User'}
                                        </p>
                                        <p className="text-xs text-muted-foreground truncate">
                                            {user?.emailAddresses?.[0]?.emailAddress}
                                        </p>
                                    </div>
                                    <SignOutButton>
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            className="h-8 w-8 text-muted-foreground hover:text-foreground hover:scale-110 boring:hover:scale-100 transition-all duration-200 boring:transition-none"
                                        >
                                            <LogOut size={16} />
                                        </Button>
                                    </SignOutButton>
                                </div>
                            </>
                        ) : (
                            <SignInButton mode="modal">
                                <Button variant="ghost" className="w-full justify-start gap-2 text-sidebar-foreground hover:bg-sidebar-accent hover:scale-105 boring:hover:scale-100 transition-all duration-200 boring:transition-none">
                                    <LogIn size={18} />
                                    Login
                                </Button>
                            </SignInButton>
                        )
                    )}
                </div>
            </div>

            {/* Settings Modal */}
            <SettingsModal
                isOpen={settingsOpen}
                onClose={() => setSettingsOpen(false)}
                userId={userId}
            />
        </>
    );
}
