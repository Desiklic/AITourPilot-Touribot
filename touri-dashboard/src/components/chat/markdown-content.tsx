'use client';

import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import { Copy, Check } from 'lucide-react';
import type { Components } from 'react-markdown';

// Recursively extract plain text from React children (needed for copy button)
function extractText(children: React.ReactNode): string {
  if (typeof children === 'string') return children;
  if (typeof children === 'number') return String(children);
  if (Array.isArray(children)) return children.map(extractText).join('');
  if (React.isValidElement(children)) {
    const el = children as React.ReactElement<{ children?: React.ReactNode }>;
    return extractText(el.props.children);
  }
  return '';
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }).catch(() => {});
  };

  return (
    <button
      onClick={handleCopy}
      aria-label="Copy code to clipboard"
      title="Copy code"
      className="flex items-center gap-1 text-xs text-muted-foreground/60 hover:text-muted-foreground transition-colors px-2 py-1 rounded hover:bg-white/5"
    >
      {copied
        ? <><Check className="w-3 h-3 text-green-400" /> Copied</>
        : <><Copy className="w-3 h-3" /> Copy</>
      }
    </button>
  );
}

// Pre component: wraps fenced code blocks with a header bar and copy button
function Pre({ children }: React.ComponentPropsWithoutRef<'pre'>) {
  // children is typically a <code> React element with className and children
  const codeElement = React.isValidElement(children)
    ? (children as React.ReactElement<{ className?: string; children?: React.ReactNode }>)
    : null;

  const className = codeElement?.props?.className || '';
  // rehype-highlight adds "hljs language-xxx" — extract the language part.
  // Guard against returning "hljs" itself when no language is specified.
  const rawLang = className.replace(/.*language-/, '').split(' ')[0] || '';
  const language = rawLang === 'hljs' ? '' : rawLang;
  const codeText = extractText(codeElement?.props?.children);

  return (
    <div className="code-block-wrapper">
      <div className="code-block-header">
        <span className="text-xs text-muted-foreground/60 font-mono">
          {language || 'code'}
        </span>
        <CopyButton text={codeText} />
      </div>
      <pre>
        <code className={className}>{codeElement?.props?.children}</code>
      </pre>
    </div>
  );
}

// Code component: handles inline code only (code elements that are NOT inside a pre)
function InlineCode({ children }: React.ComponentPropsWithoutRef<'code'>) {
  return <code className="inline-code">{children}</code>;
}

// Link component: opens in new tab with safety attributes
function Link({ href, children }: React.ComponentPropsWithoutRef<'a'>) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="text-[var(--primary)] underline underline-offset-2 hover:opacity-80 transition-opacity"
    >
      {children}
    </a>
  );
}

// Table component: wrapped for horizontal scroll on narrow viewports
function Table({ children }: React.ComponentPropsWithoutRef<'table'>) {
  return (
    <div className="overflow-x-auto my-4">
      <table className="markdown-table">{children}</table>
    </div>
  );
}

const COMPONENTS: Components = {
  pre: Pre,
  code: InlineCode,
  a: Link,
  table: Table,
};

interface MarkdownContentProps {
  content: string;
  isStreaming?: boolean;
}

function MarkdownContentInner({ content, isStreaming }: MarkdownContentProps) {
  // Strip the streaming cursor character before markdown parsing so it never
  // breaks code block syntax highlighting or ends up inside rendered output.
  const cleaned = content.replace(/\u258c/g, '');

  return (
    <div className={`markdown-body text-[15px]${isStreaming ? ' streaming-cursor' : ''}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={COMPONENTS}
      >
        {cleaned}
      </ReactMarkdown>
    </div>
  );
}

export const MarkdownContent = React.memo(MarkdownContentInner);
