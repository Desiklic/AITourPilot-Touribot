'use client';

import { useRef, useState, useEffect } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';

export interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  sending?: boolean;
  initialValue?: string;
  onInitialValueConsumed?: () => void;
}

export function ChatInput({ onSend, disabled, sending, initialValue, onInitialValueConsumed }: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [value, setValue] = useState('');

  // Pre-fill from initialValue (e.g. ?prompt= query param)
  useEffect(() => {
    if (initialValue) {
      setValue(initialValue);
      // Trigger height adjustment after value is set
      requestAnimationFrame(() => {
        const el = textareaRef.current;
        if (el) {
          el.style.height = 'auto';
          el.style.height = Math.min(el.scrollHeight, 340) + 'px';
          el.focus();
          el.setSelectionRange(el.value.length, el.value.length);
        }
      });
      onInitialValueConsumed?.();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialValue]);

  const adjustHeight = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 340) + 'px';
  };

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setValue('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  };

  const isDisabled = !!disabled || !!sending;
  const canSend = !isDisabled && value.trim().length > 0;

  return (
    <div className="border-t bg-background p-4">
      <form
        autoComplete="off"
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="flex gap-2 items-end"
      >
        {/* Safari AutoFill blocker */}
        <input type="text" name="prevent-autofill" style={{ display: 'none' }} tabIndex={-1} />

        {/* Message textarea */}
        <textarea
          ref={textareaRef}
          name="chat-message"
          value={value}
          onChange={(e) => {
            setValue(e.target.value);
            adjustHeight();
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          placeholder="Message Touri..."
          disabled={isDisabled}
          autoComplete="off"
          data-form-type="other"
          data-lpignore="true"
          className="flex-1 resize-none bg-muted rounded-xl px-4 py-3 text-[15px] placeholder:text-muted-foreground/60 focus:outline-none focus:ring-1 focus:ring-[var(--primary)] min-h-[72px] max-h-[340px] transition-all"
          rows={3}
        />

        {/* Send button */}
        <Button
          type="submit"
          size="icon"
          disabled={!canSend}
          className="shrink-0 rounded-xl h-[44px] w-[44px]"
        >
          {sending ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Send className="w-4 h-4" />
          )}
        </Button>
      </form>
    </div>
  );
}
