'use client';

import { useEffect, useState } from 'react';
import { AlertTriangle, Calendar, CalendarDays, CheckSquare, Clock, Loader2 } from 'lucide-react';
import { TaskColumn } from '@/components/board/task-column';
import type { FollowUpTask } from '@/lib/types';

// ── Types ─────────────────────────────────────────────────────────────────────

interface FollowUpsResponse {
  overdue: FollowUpTask[];
  due_today: FollowUpTask[];
  this_week: FollowUpTask[];
  next_week: FollowUpTask[];
  later: FollowUpTask[];
  total: number;
  error?: boolean;
  message?: string;
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function TasksPage() {
  const [data, setData] = useState<FollowUpsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch('/api/followups', { cache: 'no-store' });
        const json: FollowUpsResponse = await res.json();
        if (json.error) {
          setError(json.message ?? 'Failed to load follow-ups');
        } else {
          setData(json);
        }
      } catch {
        setError('Failed to fetch follow-up tasks');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const total = data?.total ?? 0;

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="border-b border-[var(--border)] px-5 py-3 shrink-0">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-[var(--primary)]/15 flex items-center justify-center shrink-0">
              <CheckSquare className="w-4 h-4 text-[var(--primary)]" />
            </div>
            <div>
              <h1 className="font-semibold text-sm leading-tight">Follow-up Tasks</h1>
              <p className="text-[11px] text-[var(--muted-foreground)] leading-tight">
                Scheduled follow-up actions from your interactions
              </p>
            </div>
          </div>
          {!loading && data && (
            <span className="text-xs text-[var(--muted-foreground)]">
              {total} task{total !== 1 ? 's' : ''} total
            </span>
          )}
        </div>
        {error && (
          <div className="mt-2 p-2 bg-red-500/10 border border-red-500/30 rounded text-xs text-red-400">
            {error}
          </div>
        )}
      </div>

      {/* Body */}
      <div className="flex-1 min-h-0 p-4 overflow-auto">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <Loader2 className="w-5 h-5 animate-spin text-[var(--muted-foreground)]" />
          </div>
        ) : !data || total === 0 ? (
          <EmptyState />
        ) : (
          <div className="flex gap-3 h-full min-h-[400px]">
            <TaskColumn
              title="Overdue"
              tasks={data.overdue}
              color="text-red-500"
              icon={<AlertTriangle className="w-3.5 h-3.5" />}
            />
            <TaskColumn
              title="Due Today"
              tasks={data.due_today}
              color="text-amber-500"
              icon={<Clock className="w-3.5 h-3.5" />}
            />
            <TaskColumn
              title="This Week"
              tasks={data.this_week}
              color="text-blue-500"
              icon={<CalendarDays className="w-3.5 h-3.5" />}
            />
            <TaskColumn
              title="Next Week & Later"
              tasks={[...data.next_week, ...data.later]}
              color="text-[var(--muted-foreground)]"
              icon={<Calendar className="w-3.5 h-3.5" />}
            />
          </div>
        )}
      </div>
    </div>
  );
}

// ── Empty state ───────────────────────────────────────────────────────────────

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center py-12">
      <div className="w-12 h-12 rounded-full bg-[var(--muted)]/50 flex items-center justify-center mb-4">
        <CheckSquare className="w-6 h-6 text-[var(--muted-foreground)] opacity-50" />
      </div>
      <h2 className="font-semibold text-sm mb-1.5">No follow-ups scheduled</h2>
      <p className="text-xs text-[var(--muted-foreground)] max-w-xs">
        Use the chat to draft emails and schedule follow-ups. They will appear here once added.
      </p>
    </div>
  );
}
