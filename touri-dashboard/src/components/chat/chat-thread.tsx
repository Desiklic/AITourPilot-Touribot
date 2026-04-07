'use client';

import { Loader2, MessageCircle } from 'lucide-react';
import { format } from 'date-fns';
import type { ChatMessage } from '@/lib/api/chat-api';
import { MessageBubble } from '@/components/chat/message-bubble';

interface ChatThreadProps {
  messages: ChatMessage[];
  loading?: boolean;
  bottomRef?: React.RefObject<HTMLDivElement>;
}

export function ChatThread({ messages, loading, bottomRef }: ChatThreadProps) {
  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (messages.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3 text-muted-foreground">
        <MessageCircle className="w-10 h-10 opacity-40" />
        <p className="text-sm">No messages yet — say hello to Touri!</p>
      </div>
    );
  }

  return (
    <div className="relative">
      <div className="flex flex-col gap-3 p-4">
        {messages.map((message, index) => {
          const prevMessage = index > 0 ? messages[index - 1] : null;
          const msgDate = format(new Date(message.created_at), 'yyyy-MM-dd');
          const prevDate = prevMessage
            ? format(new Date(prevMessage.created_at), 'yyyy-MM-dd')
            : null;
          const showDateDivider = !prevDate || prevDate !== msgDate;

          return (
            <div key={message.id}>
              {showDateDivider && (
                <div className="flex items-center gap-3 py-4">
                  <div className="flex-1 h-px bg-border" />
                  <span className="text-[11px] text-muted-foreground whitespace-nowrap">
                    {format(new Date(message.created_at), 'EEEE, MMM d, yyyy')}
                  </span>
                  <div className="flex-1 h-px bg-border" />
                </div>
              )}
              <MessageBubble message={message} />
            </div>
          );
        })}
        {bottomRef && <div ref={bottomRef} />}
      </div>
    </div>
  );
}
