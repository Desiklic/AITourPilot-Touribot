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
  const [promptPrefill, setPromptPrefill] = useState<string>('');
  const [isDraggingOver, setIsDraggingOver] = useState(false);
  const dragCounterRef = useRef(0);
  const chatInputRef = useRef<ChatInputHandle>(null);

  const scrollRef = useRef<HTMLDivElement>(null);

  // ── Multi-session streaming support ──────────────────────────────
  // Track which session the user is currently VIEWING (may differ from streaming sessions)
  const activeSessionRef = useRef<string | null>(null);
  // Track all in-flight streams: sessionId → { abort, streamId }
  const activeStreamsRef = useRef<Map<string, { abort: () => void; streamId: number }>>(new Map());
  // Set of sessions with running streams (for UI indicators)
  const [streamingSessions, setStreamingSessions] = useState<Set<string>>(new Set());

  // Keep the ref in sync with state
  useEffect(() => {
    activeSessionRef.current = sessionId;
  }, [sessionId]);

  // Derived: is the CURRENT session streaming?
  const sending = sessionId ? streamingSessions.has(sessionId) : false;

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
      setMessages([]);
      setSessionId(null);
    }
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
        if (!promptParam && data && data.length > 0) {
          const latest = data[0];
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
      // Allow sending even if OTHER sessions are streaming — only block THIS session
      if (sessionId && streamingSessions.has(sessionId)) return;

      // Capture the session at send time — this is the session this stream belongs to
      const sendSessionId = sessionId;

      // Optimistic user message
      const attachmentSuffix =
        files.length > 0 ? '\n\n📎 ' + files.map((f) => f.name).join(', ') : '';
      const tempUserMsg: ChatMessage = {
        id: Date.now(),
        session_id: sendSessionId || '',
        role: 'user',
        content: message + attachmentSuffix,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, tempUserMsg]);

      // Streaming placeholder
      const thisStreamId = streamingIdCounter--;
      const streamingMsg: ChatMessage = {
        id: thisStreamId,
        session_id: sendSessionId || '',
        role: 'assistant',
        content: '',
        created_at: new Date().toISOString(),
        streaming: true,
      };
      setMessages((prev) => [...prev, streamingMsg]);
      setTimeout(() => scrollToBottom('smooth'), 50);

      let accumulatedText = '';
      let streamSessionId = sendSessionId;

      // Mark this session as streaming
      const tempStreamKey = sendSessionId || `new-${Date.now()}`;
      setStreamingSessions((prev) => new Set(prev).add(tempStreamKey));

      try {
        const { stream, abort } = streamChat(message, sendSessionId, files);
        activeStreamsRef.current.set(tempStreamKey, { abort, streamId: thisStreamId });

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
              // Update the stream key if we got a real session ID from the server
              if (data.session_id && data.session_id !== sendSessionId) {
                // Move stream tracking to the real session ID
                const streamInfo = activeStreamsRef.current.get(tempStreamKey);
                if (streamInfo) {
                  activeStreamsRef.current.delete(tempStreamKey);
                  activeStreamsRef.current.set(data.session_id, streamInfo);
                }
                setStreamingSessions((prev) => {
                  const next = new Set(prev);
                  next.delete(tempStreamKey);
                  next.add(data.session_id);
                  return next;
                });

                // Only update visible sessionId if user is still on this session
                if (activeSessionRef.current === sendSessionId || activeSessionRef.current === null) {
                  setSessionId(data.session_id);
                }
              }
              continue;
            }

            // Only update visible messages if user is still viewing THIS session
            const isViewingThisSession =
              activeSessionRef.current === streamSessionId ||
              activeSessionRef.current === sendSessionId ||
              activeSessionRef.current === null;

            if (data.event === 'text_delta') {
              accumulatedText += data.text || '';
              if (isViewingThisSession) {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === thisStreamId ? { ...m, content: accumulatedText } : m,
                  ),
                );
                scrollToBottom('smooth');
              }
            } else if (data.event === 'done') {
              const finalText = data.text || accumulatedText || '';
              if (isViewingThisSession) {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === thisStreamId
                      ? { ...m, content: finalText, streaming: false }
                      : m,
                  ),
                );
              }
              await fetchSessions();
            } else if (data.event === 'error') {
              if (isViewingThisSession) {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === thisStreamId
                      ? { ...m, content: `Error: ${data.text || 'Unknown error'}`, streaming: false }
                      : m,
                  ),
                );
              }
            }
          } catch {
            // Skip malformed JSON lines
          }
        }
      } catch {
        // Stream error
        const isViewing =
          activeSessionRef.current === streamSessionId ||
          activeSessionRef.current === sendSessionId;
        if (isViewing) {
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
        }
      } finally {
        // Clean up stream tracking
        const finalKey = streamSessionId || tempStreamKey;
        activeStreamsRef.current.delete(finalKey);
        activeStreamsRef.current.delete(tempStreamKey);
        setStreamingSessions((prev) => {
          const next = new Set(prev);
          next.delete(finalKey);
          next.delete(tempStreamKey);
          return next;
        });
        if (
          activeSessionRef.current === streamSessionId ||
          activeSessionRef.current === sendSessionId
        ) {
          setTimeout(() => scrollToBottom('smooth'), 100);
        }
      }
    },
    [sessionId, streamingSessions, scrollToBottom, fetchSessions],
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

        {/* Typing indicator — only when waiting for first token on CURRENT session */}
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

        {/* Input — disabled only when THIS session is streaming */}
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
