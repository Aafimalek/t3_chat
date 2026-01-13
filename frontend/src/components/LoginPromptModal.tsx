'use client';

import React from 'react';
import { Button } from '@/components/ui/button';
import { SignInButton } from '@clerk/nextjs';
import { LogIn, MessageCircle, X } from 'lucide-react';

interface LoginPromptModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export function LoginPromptModal({ isOpen, onClose }: LoginPromptModalProps) {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
            <div className="bg-background border border-border w-full max-w-md mx-4 shadow-xl rounded-lg overflow-hidden">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-border">
                    <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-full bg-pink-100 dark:bg-pink-900/20 flex items-center justify-center">
                            <MessageCircle className="h-5 w-5 text-pink-600 dark:text-pink-400" />
                        </div>
                        <h2 className="text-lg font-semibold">Sign in to chat</h2>
                    </div>
                    <Button variant="ghost" size="icon" onClick={onClose}>
                        <X size={20} />
                    </Button>
                </div>

                {/* Content */}
                <div className="p-6 space-y-4">
                    <p className="text-sm text-muted-foreground text-center">
                        You need to be logged in to start chatting with AI models.
                        Sign in to continue your conversation and access your chat history.
                    </p>

                    <div className="flex flex-col gap-3">
                        <SignInButton mode="modal">
                            <Button className="w-full gap-2 bg-pink-600 hover:bg-pink-700">
                                <LogIn size={18} />
                                Sign in with Clerk
                            </Button>
                        </SignInButton>

                        <Button variant="outline" onClick={onClose} className="w-full">
                            Cancel
                        </Button>
                    </div>

                    <p className="text-xs text-center text-muted-foreground">
                        Don't have an account? Click above to sign up.
                    </p>
                </div>
            </div>
        </div>
    );
}
