'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { Plus, Search, MoreHorizontal, Trash2 } from 'lucide-react';
import { format, isToday, isYesterday } from 'date-fns';
import { getSessions, deleteSession } from '@/lib/api/chat-api';
import type { ChatSession } from '@/lib/api/chat-api';

interface ChatSidebarProps {
  activeSessionId: string | null;
  onSelectSession: (sessionId: string) => void;
  onNewChat: () => void;
  onSessionDeleted?: (sessionId: string) => void;
}

function formatDateLabel(dateStr: string): string {
  const d = new Date(dateStr);
  if (isToday(d)) return 'Today';
  if (isYesterday(d)) return 'Yesterday';
  return format(d, 'EEEE, MMM d');
}

function groupByDate(sessions: ChatSession[]): Map<string, ChatSession[]> {
  const groups = new Map<string, ChatSession[]>();
  for (const s of sessions) {
    const key = format(new Date(s.last_message_at), 'yyyy-MM-dd');
    const list = groups.get(key) || [];
    list.push(s);
    groups.set(key, list);
  }
  return groups;
}

function SessionMenu({
  session,
  onDelete,
  onClose,
}: {
  session: ChatSession;
  onDelete: (sessionId: string) => void;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [onClose]);

  return (
    <div ref={ref} className="absolute right-0 top-0 z-50 bg-[var(--sidebar)] border border-[var(--sidebar-border)] rounded-lg shadow-lg py-1 w-36">
      <button
        onClick={() => { onDelete(session.session_id); onClose(); }}
        className="flex items-center gap-2 w-full px-3 py-1.5 text-sm text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors"
      >
        <Trash2 className="w-3.5 h-3.5" />
        Delete
      </button>
    </div>
  );
}

export function ChatSidebar({
  activeSessionId,
  onSelectSession,
  onNewChat,
  onSessionDeleted,
}: ChatSidebarProps) {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [search, setSearch] = useState('');
  const [menuSessionId, setMenuSessionId] = useState<string | null>(null);

  const fetchSessions = useCallback(async () => {
    try {
      const data = await getSessions();
      setSessions(data || []);
    } catch {
      // silently fail — backend may not be running yet
    }
  }, []);

  // Fetch on mount only; callers trigger a refresh by calling fetchSessions
  // via the exposed ref pattern. In practice the page calls fetchSessions
  // after each send/delete action.
  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  // Re-fetch when activeSessionId changes (new session created)
  useEffect(() => {
    fetchSessions();
  }, [activeSessionId, fetchSessions]);

  const handleDelete = useCallback(
    async (sessionId: string) => {
      try {
        await deleteSession(sessionId);
        await fetchSessions();
        if (sessionId === activeSessionId) {
          onSessionDeleted?.(sessionId);
        }
      } catch {
        // silently fail
      }
    },
    [fetchSessions, activeSessionId, onSessionDeleted],
  );

  const filtered = search.trim()
    ? sessions.filter(
        (s) =>
          s.session_id.toLowerCase().includes(search.toLowerCase()) ||
          (s.title || '').toLowerCase().includes(search.toLowerCase()) ||
          (s.preview || '').toLowerCase().includes(search.toLowerCase()),
      )
    : sessions;

  const grouped = groupByDate(filtered);

  return (
    <div className="flex flex-col h-full">
      {/* New Chat button */}
      <div className="px-3 pt-2 pb-0">
        <button
          onClick={onNewChat}
          className="flex items-center gap-2.5 w-full px-2 py-1.5 rounded-lg text-sm font-medium text-[var(--sidebar-foreground)] hover:bg-[var(--sidebar-accent)] transition-colors"
        >
          <div className="w-6 h-6 rounded-full border border-[var(--sidebar-border)] flex items-center justify-center">
            <Plus className="w-3.5 h-3.5" />
          </div>
          New chat
        </button>
      </div>

      {/* Search */}
      <div className="px-3 pt-1 pb-1">
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--sidebar-foreground)]" />
          <input
            type="text"
            placeholder="Search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-[var(--sidebar-accent)]/50 border-0 text-sm text-[var(--sidebar-foreground)] placeholder:text-[var(--sidebar-foreground)]/70 focus:outline-none focus:ring-1 focus:ring-[var(--sidebar-border)]"
          />
        </div>
      </div>

      {/* Session list */}
      <div className="flex-1 overflow-y-auto px-1.5">
        {filtered.length === 0 ? (
          <p className="text-xs text-[var(--sidebar-foreground)]/50 text-center mt-8">
            No conversations yet
          </p>
        ) : (
          Array.from(grouped.entries()).map(([dateKey, items]) => (
            <div key={dateKey}>
              {/* Date divider */}
              <div className="flex items-center gap-2 px-2 pt-3 pb-1">
                <div className="flex-1 h-px bg-[var(--sidebar-border)]" />
                <span className="text-[10px] text-[var(--sidebar-foreground)]/80 whitespace-nowrap font-medium uppercase tracking-wider">
                  {formatDateLabel(items[0].last_message_at)}
                </span>
                <div className="flex-1 h-px bg-[var(--sidebar-border)]" />
              </div>

              {items.map((session) => {
                const isActive = session.session_id === activeSessionId;
                const label =
                  session.title ||
                  session.preview ||
                  `Chat ${format(new Date(session.last_message_at), 'HH:mm')}`;

                return (
                  <div key={session.session_id} className="relative">
                    <button
                      onClick={() => onSelectSession(session.session_id)}
                      className={`w-full text-left px-3 py-2 rounded-lg mb-0.5 transition-colors flex items-center group ${
                        isActive
                          ? 'bg-[var(--sidebar-accent)]'
                          : 'hover:bg-[var(--sidebar-accent)]/50'
                      }`}
                    >
                      <p
                        className={`text-[13px] truncate flex-1 ${
                          isActive
                            ? 'font-semibold text-[var(--sidebar-accent-foreground)]'
                            : 'font-medium text-[var(--sidebar-foreground)]'
                        }`}
                      >
                        {label}
                      </p>

                      {/* Three-dot menu trigger — visible on hover */}
                      <span
                        onClick={(e) => {
                          e.stopPropagation();
                          setMenuSessionId(
                            menuSessionId === session.session_id ? null : session.session_id,
                          );
                        }}
                        className="ml-1 p-0.5 rounded opacity-0 group-hover:opacity-100 hover:bg-[var(--sidebar-border)]/50 transition-opacity shrink-0"
                      >
                        <MoreHorizontal className="w-4 h-4 text-[var(--sidebar-foreground)]/60" />
                      </span>
                    </button>

                    {/* Dropdown menu */}
                    {menuSessionId === session.session_id && (
                      <SessionMenu
                        session={session}
                        onDelete={handleDelete}
                        onClose={() => setMenuSessionId(null)}
                      />
                    )}
                  </div>
                );
              })}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
