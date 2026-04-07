'use client';

import { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import type { ChatMessage } from '@/lib/api/chat-api';
import { MarkdownContent } from './markdown-content';

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const showConfirmation = () => {
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleCopy = () => {
    // navigator.clipboard requires secure context (HTTPS/localhost).
    // TouriBot dashboard runs over HTTP on localhost, so always try
    // the clipboard API first, then fall back to execCommand.
    if (navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(text)
        .then(showConfirmation)
        .catch(() => {
          fallbackCopy(text);
          showConfirmation();
        });
    } else {
      fallbackCopy(text);
      showConfirmation();
    }
  };

  const fallbackCopy = (t: string) => {
    const textarea = document.createElement('textarea');
    textarea.value = t;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
  };

  return (
    <button
      onClick={handleCopy}
      title={copied ? 'Copied!' : 'Copy message'}
      className="transition-colors"
    >
      {copied
        ? <Check className="w-3.5 h-3.5 text-green-500" />
        : <Copy className="w-3.5 h-3.5 text-muted-foreground/50 hover:text-muted-foreground" />}
    </button>
  );
}

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isStreaming = !!message.streaming;

  const timestamp = isStreaming
    ? null
    : formatDistanceToNow(new Date(message.created_at), { addSuffix: true });

  // Trim whitespace and collapse runs of 3+ newlines to max 2 (single blank line).
  // Prevents excessive blank lines from bloating bubbles.
  const content = message.content.trim().replace(/\n{3,}/g, '\n\n');

  if (message.role === 'user') {
    return (
      <div className="flex justify-end animate-in fade-in duration-300">
        <div className="max-w-[65%]">
          {content && (
            <div className="bg-muted rounded-2xl rounded-br-sm px-4 py-2.5">
              <p className="text-[15px] whitespace-pre-wrap text-foreground">{content}</p>
            </div>
          )}
          <div className="flex items-center justify-end gap-2 mt-1">
            <p className="text-[11px] text-muted-foreground">{timestamp}</p>
            {content && <CopyButton text={content} />}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="animate-in fade-in duration-300 ml-[8%] mr-[4%]">
      <div>
        <div className={`px-1 py-1${isStreaming ? ' border-l-2 border-[var(--primary)]/30 pl-3' : ''}`}>
          <MarkdownContent content={content} isStreaming={isStreaming} />
        </div>
        <div className="flex items-center gap-2 mt-1">
          {isStreaming ? (
            <span className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--primary)] animate-pulse" />
              Streaming...
            </span>
          ) : (
            <>
              <p className="text-[11px] text-muted-foreground">{timestamp}</p>
              <CopyButton text={content} />
            </>
          )}
        </div>
      </div>
    </div>
  );
}
