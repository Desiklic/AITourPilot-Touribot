'use client';

import { useRouter } from 'next/navigation';
import { format, parseISO } from 'date-fns';
import type { ReactNode } from 'react';
import { StageBadge } from '@/components/pipeline/stage-badge';
import type { FollowUpTask, PipelineStage } from '@/lib/types';

// ── Types ─────────────────────────────────────────────────────────────────────

interface TaskColumnProps {
  title: string;
  tasks: FollowUpTask[];
  color: string; // Tailwind border/text colour class, e.g. 'border-red-400 text-red-500'
  icon: ReactNode;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatDate(dateStr: string): string {
  try {
    return format(parseISO(dateStr), 'MMM d, yyyy');
  } catch {
    return dateStr;
  }
}

// ── Component ─────────────────────────────────────────────────────────────────

export function TaskColumn({ title, tasks, color, icon }: TaskColumnProps) {
  const router = useRouter();

  return (
    <div className="flex flex-col min-w-0 flex-1 border border-[var(--border)] rounded-lg overflow-hidden bg-[var(--card)]">
      {/* Column header */}
      <div className={['flex items-center gap-2 px-3 py-2.5 border-b border-[var(--border)]', color].join(' ')}>
        <span className="shrink-0">{icon}</span>
        <span className="font-semibold text-xs truncate">{title}</span>
        <span className="ml-auto shrink-0 text-xs font-bold tabular-nums opacity-70">
          {tasks.length}
        </span>
      </div>

      {/* Task cards */}
      <div className="flex-1 overflow-y-auto p-2 flex flex-col gap-2">
        {tasks.length === 0 ? (
          <p className="text-[11px] text-[var(--muted-foreground)] px-2 py-4 text-center">
            No tasks
          </p>
        ) : (
          tasks.map((task) => (
            <TaskCard key={task.id} task={task} onClick={() => router.push(`/pipeline/${task.museum_id}`)} />
          ))
        )}
      </div>
    </div>
  );
}

// ── Task card ─────────────────────────────────────────────────────────────────

function TaskCard({ task, onClick }: { task: FollowUpTask; onClick: () => void }) {
  const location = [task.city, task.country].filter(Boolean).join(', ');

  return (
    <button
      onClick={onClick}
      className="w-full text-left rounded-md border border-[var(--border)] bg-[var(--background)] hover:bg-[var(--muted)]/40 transition-colors p-2.5 flex flex-col gap-1.5"
    >
      {/* Museum name */}
      <div className="flex items-start justify-between gap-2">
        <span className="font-medium text-xs leading-snug truncate flex-1">
          {task.museum_name}
        </span>
        <StageBadge stage={task.stage as PipelineStage} size="sm" />
      </div>

      {/* Follow-up action */}
      {task.follow_up_action && (
        <p className="text-[11px] text-[var(--muted-foreground)] leading-snug line-clamp-2">
          {task.follow_up_action}
        </p>
      )}

      {/* Footer: date + location */}
      <div className="flex items-center justify-between gap-2 mt-0.5">
        <span className="text-[10px] text-[var(--muted-foreground)] tabular-nums">
          {formatDate(task.follow_up_date)}
        </span>
        {location && (
          <span className="text-[10px] text-[var(--muted-foreground)] truncate max-w-[100px]">
            {location}
          </span>
        )}
      </div>
    </button>
  );
}
