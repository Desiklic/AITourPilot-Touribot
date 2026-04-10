'use client';

import { useState, useEffect, useRef, useCallback, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { Upload } from 'lucide-react';
import { ChatThread } from '@/components/chat/chat-thread';
import { ChatInput } from '@/components/chat/chat-input';
import type { ChatInputHandle } from '@/components/chat/chat-input';
import { ChatSidebar } from '@/components/chat/chat-sidebar';
import { useSidebarContent } from '@/components/layout/layout-shell';
import { streamChat, getSessions, getMessages } from '@/lib/api/chat-api';
import type { ChatMessage, ChatSession } from '@/lib/api/chat-api';

// Counter for unique streaming placeholder IDs (negative to avoid collision with DB IDs)
let streamingIdCounter = -1000;

export default function ChatPage() {
  return (
    <Suspense fallback={<div className="flex flex-col h-full -m-6" />}>
      <ChatPageInner />
    </Suspense>
  );
}

function ChatPageInner() {
  const searchParams = useSearchParams();
  const { setSidebarContent } = useSidebarContent();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [promptPrefill, setPromptPrefill] = useState<string>('');
  const [isDraggingOver, setIsDraggingOver] = useState(false);
  const dragCounterRef = useRef(0);
  const chatInputRef = useRef<ChatInputHandle>(null);

  const scrollRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<(() => void) | null>(null);

  const scrollToBottom = useCallback((behavior: ScrollBehavior = 'smooth') => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior });
  }, []);

  const fetchSessions = useCallback(async () => {
    try {
      const data = await getSessions();
      setSessions(data || []);
    } catch {
      // silently fail — backend may not be running
    }
  }, []);

  const loadSession = useCallback(
    async (sid: string) => {
      setLoading(true);
      setMessages([]);
      setSessionId(sid);
      try {
        const msgs = await getMessages(sid);
        setMessages(msgs || []);
      } catch {
        // silently fail
      } finally {
        setLoading(false);
        setTimeout(() => scrollToBottom('instant'), 50);
      }
    },
    [scrollToBottom],
  );

  // Read ?prompt= query param and pre-fill the input
  useEffect(() => {
    const prompt = searchParams.get('prompt');
    if (prompt) {
      setPromptPrefill(decodeURIComponent(prompt));
      // Start a new chat session so the prefilled prompt goes into a fresh context
      setMessages([]);
      setSessionId(null);
    }
    // Only run on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // On mount: fetch sessions and load the most recent one (skip if prompt param present)
  useEffect(() => {
    const promptParam = searchParams.get('prompt');
    const init = async () => {
      setLoading(true);
      try {
        const data = await getSessions();
        setSessions(data || []);
        // If a prompt param was given, don't load the last session — start fresh
        if (!promptParam && data && data.length > 0) {
          const latest = data[0]; // sessions are ordered by last_message_at DESC
          setSessionId(latest.session_id);
          const msgs = await getMessages(latest.session_id);
          setMessages(msgs || []);
        }
      } catch {
        // Backend not running yet — show empty state
      } finally {
        setLoading(false);
        setTimeout(() => scrollToBottom('instant'), 50);
      }
    };
    init();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scrollToBottom]);

  const handleSelectSession = useCallback(
    (sid: string) => {
      if (sid === sessionId) return;
      loadSession(sid);
    },
    [sessionId, loadSession],
  );

  const handleNewChat = useCallback(() => {
    setMessages([]);
    setSessionId(null);
  }, []);

  const handleSessionDeleted = useCallback(
    (deletedSid: string) => {
      if (deletedSid === sessionId) {
        handleNewChat();
      }
      fetchSessions();
    },
    [sessionId, handleNewChat, fetchSessions],
  );

  // Inject ChatSidebar into the global layout sidebar slot
  useEffect(() => {
    setSidebarContent(
      <ChatSidebar
        activeSessionId={sessionId}
        onSelectSession={handleSelectSession}
        onNewChat={handleNewChat}
        onSessionDeleted={handleSessionDeleted}
      />,
    );
    return () => setSidebarContent(null);
  }, [sessionId, handleSelectSession, handleNewChat, handleSessionDeleted, setSidebarContent]);

  // Full-screen drag/drop overlay (counter-ref pattern)
  useEffect(() => {
    const handleDragEnter = (e: DragEvent) => {
      e.preventDefault();
      dragCounterRef.current++;
      if (e.dataTransfer?.types.includes('Files')) {
        setIsDraggingOver(true);
      }
    };
    const handleDragLeave = (e: DragEvent) => {
      e.preventDefault();
      dragCounterRef.current--;
      if (dragCounterRef.current <= 0) {
        dragCounterRef.current = 0;
        setIsDraggingOver(false);
      }
    };
    const handleDragOver = (e: DragEvent) => {
      e.preventDefault();
    };
    const handleDrop = (e: DragEvent) => {
      e.preventDefault();
      dragCounterRef.current = 0;
      setIsDraggingOver(false);
      if (e.dataTransfer?.files?.length) {
        chatInputRef.current?.addFiles(e.dataTransfer.files);
      }
    };

    window.addEventListener('dragenter', handleDragEnter);
    window.addEventListener('dragleave', handleDragLeave);
    window.addEventListener('dragover', handleDragOver);
    window.addEventListener('drop', handleDrop);
    return () => {
      window.removeEventListener('dragenter', handleDragEnter);
      window.removeEventListener('dragleave', handleDragLeave);
      window.removeEventListener('dragover', handleDragOver);
      window.removeEventListener('drop', handleDrop);
    };
  }, []);

  // Active session title for the header
  const activeSession = sessions.find((s) => s.session_id === sessionId);
  const activeTitle = activeSession?.title || activeSession?.preview || null;

  const handleSend = useCallback(
    async (message: string, files: File[]) => {
      if (sending) return;
      setSending(true);

      // Optimistic user message — include attachment names so user sees what was sent
      const attachmentSuffix =
        files.length > 0 ? '\n\n📎 ' + files.map((f) => f.name).join(', ') : '';
      const tempUserMsg: ChatMessage = {
        id: Date.now(),
        session_id: sessionId || '',
        role: 'user',
        content: message + attachmentSuffix,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, tempUserMsg]);

      // Add streaming placeholder with unique ID
      const thisStreamId = streamingIdCounter--;
      const streamingMsg: ChatMessage = {
        id: thisStreamId,
        session_id: sessionId || '',
        role: 'assistant',
        content: '',
        created_at: new Date().toISOString(),
        streaming: true,
      };
      setMessages((prev) => [...prev, streamingMsg]);
      setTimeout(() => scrollToBottom('smooth'), 50);

      let accumulatedText = '';
      let streamSessionId = sessionId;

      try {
        const { stream, abort } = streamChat(message, sessionId, files);
        abortRef.current = abort;

        const reader = stream.getReader();
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const jsonStr = value.trim();
          if (!jsonStr) continue;

          try {
            const data = JSON.parse(jsonStr);

            if (data.event === 'meta') {
              streamSessionId = data.session_id;
              if (data.session_id && data.session_id !== sessionId) {
                setSessionId(data.session_id);
              }
              continue;
            }

            if (data.event === 'text_delta') {
              accumulatedText += data.text || '';
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === thisStreamId ? { ...m, content: accumulatedText } : m,
                ),
              );
              scrollToBottom('smooth');
            } else if (data.event === 'done') {
              const finalText = data.text || accumulatedText || '';
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === thisStreamId
                    ? { ...m, content: finalText, streaming: false }
                    : m,
                ),
              );
              setSending(false);
              // Refresh session list to pick up the new/updated session
              if (streamSessionId) {
                await fetchSessions();
              }
            } else if (data.event === 'error') {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === thisStreamId
                    ? { ...m, content: `Error: ${data.text || 'Unknown error'}`, streaming: false }
                    : m,
                ),
              );
              setSending(false);
            }
          } catch {
            // Skip malformed JSON lines
          }
        }
      } catch {
        // Stream error — finalize with whatever accumulated
        setMessages((prev) =>
          prev.map((m) =>
            m.id === thisStreamId
              ? {
                  ...m,
                  content: accumulatedText || 'Connection error — is the Touri backend running?',
                  streaming: false,
                }
              : m,
          ),
        );
      } finally {
        setSending(false);
        abortRef.current = null;
        setTimeout(() => scrollToBottom('smooth'), 100);
      }
    },
    [sending, sessionId, scrollToBottom, fetchSessions],
  );

  return (
    <div className="flex flex-col h-full -m-6">
      {/* Header */}
      <div className="px-6 py-4 border-b shrink-0">
        <div className="flex items-baseline gap-3">
          <h1 className="text-2xl font-bold tracking-tight">Chat</h1>
          {activeTitle && (
            <span className="text-base font-normal text-muted-foreground/70 truncate max-w-[50%]">
              {activeTitle}
            </span>
          )}
        </div>
      </div>

      {/* Chat thread — scrollable — relative for the drag overlay */}
      <div className="relative flex-1 min-h-0 flex flex-col">
        <div
          ref={scrollRef}
          className="flex-1 overflow-y-auto min-h-0"
          style={{ overscrollBehavior: 'contain' }}
        >
          <ChatThread messages={messages} loading={loading} />
        </div>

        {/* Typing indicator — only when waiting for first token */}
        {sending && messages[messages.length - 1]?.content === '' && (
          <div className="px-6 py-2 flex items-center gap-2 shrink-0">
            <div className="flex gap-1">
              <span className="w-2 h-2 rounded-full bg-muted-foreground/40 animate-bounce [animation-delay:0ms]" />
              <span className="w-2 h-2 rounded-full bg-muted-foreground/40 animate-bounce [animation-delay:150ms]" />
              <span className="w-2 h-2 rounded-full bg-muted-foreground/40 animate-bounce [animation-delay:300ms]" />
            </div>
            <span className="text-xs text-muted-foreground">Touri is thinking...</span>
          </div>
        )}

        {/* Input */}
        <div className="shrink-0">
          <ChatInput
            ref={chatInputRef}
            onSend={handleSend}
            sending={sending}
            disabled={false}
            initialValue={promptPrefill}
            onInitialValueConsumed={() => setPromptPrefill('')}
          />
        </div>

        {/* Full-screen drag/drop overlay */}
        {isDraggingOver && (
          <div className="absolute inset-0 z-50 flex flex-col items-center justify-center bg-background/80 backdrop-blur-sm border-2 border-dashed border-primary/40 rounded-lg">
            <Upload className="w-10 h-10 text-primary mb-2" />
            <p className="text-sm font-medium">Drop files here to add to chat</p>
          </div>
        )}
      </div>
    </div>
  );
}
