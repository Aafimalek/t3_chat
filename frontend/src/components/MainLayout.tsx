'use client';

import React, { useState } from 'react';
import { Sidebar } from './Sidebar';
import { ChatArea } from './ChatArea';
import { ThemeProvider } from '@/components/theme-provider';
import { ChatProvider } from '@/lib/chat-context';

export function MainLayout() {
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);

    const toggleSidebar = () => setIsSidebarOpen(!isSidebarOpen);

    return (
        <ThemeProvider
            attribute="class"
            defaultTheme="dark"
            enableSystem
            disableTransitionOnChange
        >
            <ChatProvider>
                <div className="flex h-screen w-screen overflow-hidden bg-background">
                    <Sidebar isOpen={isSidebarOpen} toggleSidebar={toggleSidebar} />
                    <div className="flex-1 h-full relative">
                        <ChatArea isSidebarOpen={isSidebarOpen} toggleSidebar={toggleSidebar} />
                    </div>
                </div>
            </ChatProvider>
        </ThemeProvider>
    );
}
