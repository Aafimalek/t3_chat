'use client';

import React, { useState, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Check, Copy } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MarkdownRendererProps {
    content: string;
    isStreaming?: boolean;
}

/**
 * CodeBlock - Renders a syntax-highlighted code block with a copy button.
 * Extracted as a separate component so each code block has its own
 * local state for the "Copied!" feedback without affecting React.memo
 * on the parent MarkdownRenderer.
 */
function CodeBlock({ language, children }: { language: string; children: string }) {
    const [copied, setCopied] = useState(false);

    const handleCopy = useCallback(async () => {
        try {
            await navigator.clipboard.writeText(children);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error('Failed to copy code:', err);
        }
    }, [children]);

    return (
        <div className="relative my-4 overflow-hidden group">
            {/* Header bar: language label + copy button */}
            <div className="flex items-center justify-between bg-zinc-800 px-4 py-1.5 text-xs text-zinc-400">
                <span>{language}</span>
                <button
                    onClick={handleCopy}
                    className={cn(
                        "flex items-center gap-1 px-2 py-0.5",
                        "text-zinc-400 hover:text-zinc-200",
                        "transition-colors duration-150 boring:transition-none",
                        copied && "text-green-400 hover:text-green-400"
                    )}
                    aria-label={copied ? "Copied" : "Copy code"}
                >
                    {copied ? (
                        <>
                            <Check size={14} />
                            <span>Copied!</span>
                        </>
                    ) : (
                        <>
                            <Copy size={14} />
                            <span>Copy</span>
                        </>
                    )}
                </button>
            </div>
            {/* Syntax-highlighted code */}
            <SyntaxHighlighter
                style={oneDark}
                language={language}
                PreTag="div"
                customStyle={{
                    margin: 0,
                    borderRadius: 0,
                    padding: '1rem',
                }}
            >
                {children}
            </SyntaxHighlighter>
        </div>
    );
}

/**
 * MarkdownRenderer - Renders markdown content with proper syntax highlighting
 * Using standard react-markdown patterns for stability during streaming
 */
const MarkdownRenderer = React.memo(({ content, isStreaming = false }: MarkdownRendererProps) => {
    // Normalize content to fix common LLM streaming artifacts
    // 1. Fix spaces inside bold tags: ** text ** -> **text**
    const normalizedContent = React.useMemo(() => {
        if (!content) return '';
        return content
            .replace(/\*\* \s+(.*?)\s+ \*\*/g, '**$1**') // Fix ** text **
            .replace(/\*\* (.*?)\*\*/g, '**$1**')       // Fix ** text**
            .replace(/\*\*(.*?) \*\*/g, '**$1**');      // Fix **text **
    }, [content]);

    return (
        <div
            className={cn(
                "prose prose-sm dark:prose-invert max-w-none break-words leading-relaxed",
                isStreaming && "streaming-active"
            )}
        >
            <ReactMarkdown
                components={{
                    // Code blocks and inline code
                    code({ node, inline, className, children, ...props }: any) {
                        const match = /language-(\w+)/.exec(className || '');
                        const isInline = inline || !match;

                        if (!isInline && match) {
                            return (
                                <CodeBlock language={match[1]}>
                                    {String(children).replace(/\n$/, '')}
                                </CodeBlock>
                            );
                        }

                        // Inline code
                        return (
                            <code
                                className="bg-muted px-1.5 py-0.5 rounded text-xs font-mono text-pink-500"
                                {...props}
                            >
                                {children}
                            </code>
                        );
                    },
                    // Custom link styling
                    a: ({ href, children }) => (
                        <a
                            href={href}
                            className="text-pink-500 hover:text-pink-400 underline underline-offset-2"
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            {children}
                        </a>
                    ),
                    // Headings with better spacing
                    h1: ({ children }) => <h1 className="text-xl font-bold mt-6 mb-4 first:mt-0">{children}</h1>,
                    h2: ({ children }) => <h2 className="text-lg font-bold mt-5 mb-3">{children}</h2>,
                    h3: ({ children }) => <h3 className="text-base font-bold mt-4 mb-2">{children}</h3>,
                    // Lists
                    ul: ({ children }) => <ul className="list-disc list-outside ml-4 space-y-1 my-3">{children}</ul>,
                    ol: ({ children }) => <ol className="list-decimal list-outside ml-4 space-y-1 my-3">{children}</ol>,
                    li: ({ children }) => <li className="leading-relaxed">{children}</li>,
                    // Blockquotes
                    blockquote: ({ children }) => (
                        <blockquote className="border-l-4 border-pink-500 pl-4 my-4 italic text-muted-foreground">
                            {children}
                        </blockquote>
                    ),
                }}
            >
                {normalizedContent}
            </ReactMarkdown>
        </div>
    );
});

MarkdownRenderer.displayName = 'MarkdownRenderer';

export { MarkdownRenderer };
