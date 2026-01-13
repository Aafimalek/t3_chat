'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { X, Trash2, Save, Brain } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
    AboutYou,
    MemoryItem,
    getAboutYou,
    updateAboutYou,
    getMemories,
    deleteMemory as apiDeleteMemory,
    clearMemories
} from '@/lib/api';

interface SettingsModalProps {
    isOpen: boolean;
    onClose: () => void;
    userId: string;
}

export function SettingsModal({ isOpen, onClose, userId }: SettingsModalProps) {
    const [activeTab, setActiveTab] = useState<'about' | 'memory'>('about');
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);

    // About You state
    const [aboutYou, setAboutYou] = useState<AboutYou>({
        nickname: '',
        occupation: '',
        about: '',
        memory_enabled: true,
    });

    // Memories state
    const [memories, setMemories] = useState<MemoryItem[]>([]);

    // Load data on open
    useEffect(() => {
        if (isOpen && userId) {
            loadData();
        }
    }, [isOpen, userId]);

    const loadData = async () => {
        setLoading(true);
        try {
            const [aboutData, memoriesData] = await Promise.all([
                getAboutYou(userId),
                getMemories(userId),
            ]);
            setAboutYou(aboutData);
            setMemories(memoriesData);
        } catch (err) {
            console.error('Failed to load settings:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleSaveAbout = async () => {
        setSaving(true);
        try {
            await updateAboutYou(userId, aboutYou);
            // Reload memories since saving about creates new memories
            const memoriesData = await getMemories(userId);
            setMemories(memoriesData);
        } catch (err) {
            console.error('Failed to save:', err);
        } finally {
            setSaving(false);
        }
    };

    const handleDeleteMemory = async (key: string) => {
        try {
            await apiDeleteMemory(userId, key);
            setMemories(memories.filter(m => m.key !== key));
        } catch (err) {
            console.error('Failed to delete memory:', err);
        }
    };

    const handleClearAllMemories = async () => {
        if (!confirm('Are you sure you want to clear all memories? This cannot be undone.')) {
            return;
        }
        try {
            await clearMemories(userId);
            setMemories([]);
        } catch (err) {
            console.error('Failed to clear memories:', err);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
            <div className="bg-background border border-border w-full max-w-2xl max-h-[80vh] flex flex-col shadow-xl">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-border">
                    <h2 className="text-lg font-semibold">Settings</h2>
                    <Button variant="ghost" size="icon" onClick={onClose}>
                        <X size={20} />
                    </Button>
                </div>

                {/* Tabs */}
                <div className="flex border-b border-border">
                    <button
                        className={`px-6 py-3 text-sm font-medium transition-colors ${activeTab === 'about'
                            ? 'text-pink-500 border-b-2 border-pink-500'
                            : 'text-muted-foreground hover:text-foreground'
                            }`}
                        onClick={() => setActiveTab('about')}
                    >
                        About You
                    </button>
                    <button
                        className={`px-6 py-3 text-sm font-medium transition-colors flex items-center gap-2 ${activeTab === 'memory'
                            ? 'text-pink-500 border-b-2 border-pink-500'
                            : 'text-muted-foreground hover:text-foreground'
                            }`}
                        onClick={() => setActiveTab('memory')}
                    >
                        <Brain size={16} />
                        Memory ({memories.length})
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-hidden">
                    {loading ? (
                        <div className="flex items-center justify-center h-full">
                            <p className="text-muted-foreground">Loading...</p>
                        </div>
                    ) : activeTab === 'about' ? (
                        <ScrollArea className="h-full">
                            <div className="p-6 space-y-6">
                                <p className="text-sm text-muted-foreground">
                                    Tell us about yourself so the AI can personalize responses.
                                    This information is saved to memory.
                                </p>

                                <div className="space-y-4">
                                    <div>
                                        <label className="text-sm font-medium text-foreground block mb-2">
                                            Nickname
                                        </label>
                                        <Input
                                            value={aboutYou.nickname}
                                            onChange={(e) => setAboutYou({ ...aboutYou, nickname: e.target.value })}
                                            placeholder="What should I call you?"
                                        />
                                    </div>

                                    <div>
                                        <label className="text-sm font-medium text-foreground block mb-2">
                                            Occupation
                                        </label>
                                        <Input
                                            value={aboutYou.occupation}
                                            onChange={(e) => setAboutYou({ ...aboutYou, occupation: e.target.value })}
                                            placeholder="e.g., Software Developer, Student, Designer"
                                        />
                                    </div>

                                    <div>
                                        <label className="text-sm font-medium text-foreground block mb-2">
                                            More about you
                                        </label>
                                        <Textarea
                                            value={aboutYou.about}
                                            onChange={(e) => setAboutYou({ ...aboutYou, about: e.target.value })}
                                            placeholder="Share anything you'd like the AI to remember about you..."
                                            className="min-h-[120px]"
                                        />
                                        <p className="text-xs text-muted-foreground mt-1">
                                            e.g., your interests, goals, preferred communication style
                                        </p>
                                    </div>
                                </div>

                                <Button
                                    onClick={handleSaveAbout}
                                    disabled={saving}
                                    className="bg-pink-600 hover:bg-pink-700"
                                >
                                    <Save size={16} className="mr-2" />
                                    {saving ? 'Saving...' : 'Save'}
                                </Button>
                            </div>
                        </ScrollArea>
                    ) : (
                        <div className="h-full flex flex-col">
                            <div className="p-4 border-b border-border flex items-center justify-between">
                                <p className="text-sm text-muted-foreground">
                                    Facts the AI remembers about you
                                </p>
                                {memories.length > 0 && (
                                    <Button
                                        variant="destructive"
                                        size="sm"
                                        onClick={handleClearAllMemories}
                                    >
                                        Clear All
                                    </Button>
                                )}
                            </div>
                            <ScrollArea className="flex-1 h-[400px]">
                                <div className="p-4 space-y-2">
                                    {memories.length === 0 ? (
                                        <p className="text-center text-muted-foreground py-8">
                                            No memories yet. The AI will learn about you as you chat.
                                        </p>
                                    ) : (
                                        memories.map((memory) => (
                                            <div
                                                key={memory.key}
                                                className="flex items-start gap-3 p-3 bg-muted/30 border border-border group rounded-md"
                                            >
                                                <div className="flex-1">
                                                    <p className="text-sm">{memory.content}</p>
                                                    <p className="text-xs text-muted-foreground mt-1">
                                                        {memory.type === 'core_fact' ? '📌 From settings' : '💬 From conversation'}
                                                    </p>
                                                </div>
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity text-destructive hover:text-destructive hover:bg-destructive/10"
                                                    onClick={() => handleDeleteMemory(memory.key)}
                                                >
                                                    <Trash2 size={14} />
                                                </Button>
                                            </div>
                                        ))
                                    )}
                                </div>
                            </ScrollArea>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
