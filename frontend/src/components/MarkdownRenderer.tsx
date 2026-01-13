'use client';

import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface MarkdownRendererProps {
    content: string;
}

/**
 * MarkdownRenderer - Renders markdown content with proper syntax highlighting
 * Using standard react-markdown patterns for stability during streaming
 */
const MarkdownRenderer = React.memo(({ content }: MarkdownRendererProps) => {
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
        <div className="prose prose-sm dark:prose-invert max-w-none break-words leading-relaxed">
            <ReactMarkdown
                components={{
                    // Code blocks and inline code
                    code({ node, inline, className, children, ...props }: any) {
                        const match = /language-(\w+)/.exec(className || '');
                        const isInline = inline || !match;

                        if (!isInline) {
                            return (
                                // @ts-expect-error - style type mismatch between libraries
                                <SyntaxHighlighter
                                    style={oneDark}
                                    language={match![1]}
                                    PreTag="div"
                                    className="!my-4 !rounded-md !bg-zinc-900"
                                    customStyle={{
                                        margin: '1em 0',
                                        borderRadius: '0.375rem',
                                        padding: '1rem',
                                    }}
                                    {...props}
                                >
                                    {String(children).replace(/\n$/, '')}
                                </SyntaxHighlighter>
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
