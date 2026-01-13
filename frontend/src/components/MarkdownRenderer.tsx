'use client';

import React, { memo } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface MarkdownRendererProps {
    content: string;
}

/**
 * MarkdownRenderer - Renders markdown content with proper syntax highlighting
 * 
 * Features:
 * - Code block syntax highlighting using Prism
 * - Inline code styling
 * - Proper heading hierarchy
 * - Lists, blockquotes, links, etc.
 */
export const MarkdownRenderer = memo(function MarkdownRenderer({ content }: MarkdownRendererProps) {
    return (
        <div className="prose prose-sm dark:prose-invert max-w-none">
            <ReactMarkdown
                components={{
                    // Paragraph
                    p: ({ children }) => (
                        <p className="text-sm leading-relaxed mb-3 last:mb-0">{children}</p>
                    ),

                    // Bold
                    strong: ({ children }) => (
                        <strong className="font-semibold text-foreground">{children}</strong>
                    ),

                    // Italic
                    em: ({ children }) => (
                        <em className="italic">{children}</em>
                    ),

                    // Code blocks and inline code
                    code: ({ children, className, ...props }) => {
                        const match = /language-(\w+)/.exec(className || '');
                        const language = match ? match[1] : '';
                        const codeString = String(children).replace(/\n$/, '');

                        // Check if it's a code block (has language) or inline code
                        const isCodeBlock = match || (codeString.includes('\n'));

                        if (isCodeBlock) {
                            return (
                                // @ts-expect-error - style type mismatch between libraries
                                <SyntaxHighlighter
                                    style={oneDark}
                                    language={language || 'text'}
                                    PreTag="div"
                                    className="!my-3 !text-xs !bg-zinc-900"
                                    customStyle={{
                                        margin: 0,
                                        borderRadius: 0,
                                        padding: '1rem',
                                    }}
                                >
                                    {codeString}
                                </SyntaxHighlighter>
                            );
                        }

                        // Inline code
                        return (
                            <code className="bg-muted px-1.5 py-0.5 text-xs font-mono text-pink-500" {...props}>
                                {children}
                            </code>
                        );
                    },

                    // Pre tag (wrapper for code blocks - we handle in code component)
                    pre: ({ children }) => (
                        <div className="not-prose my-3">{children}</div>
                    ),

                    // Unordered list
                    ul: ({ children }) => (
                        <ul className="list-disc list-outside ml-4 space-y-1 text-sm my-3">{children}</ul>
                    ),

                    // Ordered list
                    ol: ({ children }) => (
                        <ol className="list-decimal list-outside ml-4 space-y-1 text-sm my-3">{children}</ol>
                    ),

                    // List item
                    li: ({ children }) => (
                        <li className="text-sm leading-relaxed">{children}</li>
                    ),

                    // Headings
                    h1: ({ children }) => (
                        <h1 className="text-xl font-bold mb-3 mt-4 first:mt-0">{children}</h1>
                    ),
                    h2: ({ children }) => (
                        <h2 className="text-lg font-bold mb-2 mt-4 first:mt-0">{children}</h2>
                    ),
                    h3: ({ children }) => (
                        <h3 className="text-base font-bold mb-2 mt-3 first:mt-0">{children}</h3>
                    ),
                    h4: ({ children }) => (
                        <h4 className="text-sm font-bold mb-2 mt-3 first:mt-0">{children}</h4>
                    ),

                    // Blockquote
                    blockquote: ({ children }) => (
                        <blockquote className="border-l-4 border-pink-500 pl-4 my-3 italic text-muted-foreground">
                            {children}
                        </blockquote>
                    ),

                    // Links
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

                    // Horizontal rule
                    hr: () => (
                        <hr className="my-4 border-border" />
                    ),

                    // Table
                    table: ({ children }) => (
                        <div className="overflow-x-auto my-3">
                            <table className="min-w-full text-sm border border-border">
                                {children}
                            </table>
                        </div>
                    ),
                    thead: ({ children }) => (
                        <thead className="bg-muted/50">{children}</thead>
                    ),
                    tbody: ({ children }) => (
                        <tbody>{children}</tbody>
                    ),
                    tr: ({ children }) => (
                        <tr className="border-b border-border">{children}</tr>
                    ),
                    th: ({ children }) => (
                        <th className="px-3 py-2 text-left font-semibold">{children}</th>
                    ),
                    td: ({ children }) => (
                        <td className="px-3 py-2">{children}</td>
                    ),
                }}
            >
                {content}
            </ReactMarkdown>
        </div>
    );
});

export default MarkdownRenderer;
