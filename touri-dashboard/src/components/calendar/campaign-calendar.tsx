'use client';

import { useRouter } from 'next/navigation';
import {
  startOfMonth,
  endOfMonth,
  eachDayOfInterval,
  isSameMonth,
  isToday,
  format,
  addMonths,
  subMonths,
  getDay,
} from 'date-fns';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import type { CalendarEvent } from '@/lib/types';

// ── Types ─────────────────────────────────────────────────────────────────────

interface CampaignCalendarProps {
  events: CalendarEvent[];
  currentMonth: Date;
  onMonthChange: (date: Date) => void;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const DAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

/** Returns 0-indexed day-of-week with Monday = 0. */
function mondayOffset(date: Date): number {
  const dow = getDay(date); // 0 = Sunday
  return dow === 0 ? 6 : dow - 1;
}

function eventColor(event: CalendarEvent, today: string): string {
  const dateStr = event.follow_up_date.slice(0, 10);
  if (event.type === 'demo') return 'bg-cyan-500/20 text-cyan-700 border-cyan-300';
  if (dateStr < today) return 'bg-red-500/20 text-red-700 border-red-300';
  return 'bg-amber-500/20 text-amber-700 border-amber-300';
}

function dotColor(event: CalendarEvent, today: string): string {
  const dateStr = event.follow_up_date.slice(0, 10);
  if (event.type === 'demo') return 'bg-cyan-500';
  if (dateStr < today) return 'bg-red-500';
  return 'bg-amber-500';
}

// ── Component ─────────────────────────────────────────────────────────────────

export function CampaignCalendar({ events, currentMonth, onMonthChange }: CampaignCalendarProps) {
  const router = useRouter();
  const today = new Date().toISOString().slice(0, 10);

  // Build calendar grid: pad with null cells to start on Monday
  const monthStart = startOfMonth(currentMonth);
  const monthEnd = endOfMonth(currentMonth);
  const days = eachDayOfInterval({ start: monthStart, end: monthEnd });

  const leadingNulls = mondayOffset(monthStart);
  const cells: (Date | null)[] = [
    ...Array(leadingNulls).fill(null),
    ...days,
  ];

  // Fill trailing nulls to complete last row
  const remainder = cells.length % 7;
  if (remainder !== 0) {
    cells.push(...Array(7 - remainder).fill(null));
  }

  // Index events by date string
  const eventsByDate = new Map<string, CalendarEvent[]>();
  for (const event of events) {
    const key = event.follow_up_date.slice(0, 10);
    if (!eventsByDate.has(key)) eventsByDate.set(key, []);
    eventsByDate.get(key)!.push(event);
  }

  const monthLabel = format(currentMonth, 'MMMM yyyy');
  const isCurrentMonth =
    format(currentMonth, 'yyyy-MM') === format(new Date(), 'yyyy-MM');

  return (
    <div className="flex flex-col h-full">
      {/* ── Month header ── */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--border)] shrink-0">
        <button
          onClick={() => onMonthChange(subMonths(currentMonth, 1))}
          className="p-1.5 rounded hover:bg-[var(--muted)]/50 transition-colors"
          aria-label="Previous month"
        >
          <ChevronLeft className="w-4 h-4 text-[var(--muted-foreground)]" />
        </button>

        <div className="flex items-center gap-3">
          <span className="font-semibold text-sm">{monthLabel}</span>
          {!isCurrentMonth && (
            <button
              onClick={() => onMonthChange(new Date())}
              className="text-xs px-2 py-0.5 rounded bg-[var(--muted)]/50 text-[var(--muted-foreground)] hover:bg-[var(--muted)] transition-colors"
            >
              Today
            </button>
          )}
        </div>

        <button
          onClick={() => onMonthChange(addMonths(currentMonth, 1))}
          className="p-1.5 rounded hover:bg-[var(--muted)]/50 transition-colors"
          aria-label="Next month"
        >
          <ChevronRight className="w-4 h-4 text-[var(--muted-foreground)]" />
        </button>
      </div>

      {/* ── Day labels ── */}
      <div className="grid grid-cols-7 border-b border-[var(--border)] shrink-0">
        {DAY_LABELS.map((label) => (
          <div
            key={label}
            className="py-2 text-center text-[10px] font-medium text-[var(--muted-foreground)] uppercase tracking-wide"
          >
            {label}
          </div>
        ))}
      </div>

      {/* ── Calendar grid ── */}
      <div className="grid grid-cols-7 flex-1 overflow-auto">
        {cells.map((day, idx) => {
          if (day === null) {
            return (
              <div
                key={`empty-${idx}`}
                className="min-h-[80px] border-b border-r border-[var(--border)] bg-[var(--muted)]/10"
              />
            );
          }

          const dateStr = format(day, 'yyyy-MM-dd');
          const dayEvents = eventsByDate.get(dateStr) ?? [];
          const isCurrentDay = isToday(day);
          const isInMonth = isSameMonth(day, currentMonth);

          return (
            <div
              key={dateStr}
              className={[
                'min-h-[80px] border-b border-r border-[var(--border)] p-1.5 flex flex-col gap-1',
                !isInMonth && 'opacity-40',
                isCurrentDay && 'ring-2 ring-inset ring-[var(--primary)]/40 bg-[var(--primary)]/5',
              ]
                .filter(Boolean)
                .join(' ')}
            >
              {/* Date number */}
              <span
                className={[
                  'text-xs font-medium leading-none self-start px-1',
                  isCurrentDay
                    ? 'text-[var(--primary)] font-bold'
                    : 'text-[var(--muted-foreground)]',
                ]
                  .filter(Boolean)
                  .join(' ')}
              >
                {format(day, 'd')}
              </span>

              {/* Event pills */}
              {dayEvents.slice(0, 3).map((event) => (
                <button
                  key={`${event.type}-${event.id}`}
                  onClick={() => router.push(`/pipeline/${event.museum_id}`)}
                  title={event.follow_up_action ?? event.museum_name}
                  className={[
                    'flex items-center gap-1 w-full rounded px-1.5 py-0.5 text-[10px] border truncate text-left hover:opacity-80 transition-opacity',
                    eventColor(event, today),
                  ].join(' ')}
                >
                  <span
                    className={['w-1.5 h-1.5 rounded-full shrink-0', dotColor(event, today)].join(
                      ' '
                    )}
                  />
                  <span className="truncate">{event.museum_name}</span>
                </button>
              ))}

              {dayEvents.length > 3 && (
                <span className="text-[9px] text-[var(--muted-foreground)] pl-1">
                  +{dayEvents.length - 3} more
                </span>
              )}
            </div>
          );
        })}
      </div>

      {/* ── Legend ── */}
      <div className="flex items-center gap-4 px-4 py-2 border-t border-[var(--border)] shrink-0">
        <span className="text-[10px] text-[var(--muted-foreground)] font-medium uppercase tracking-wide">
          Legend:
        </span>
        <LegendItem color="bg-amber-500" label="Follow-up" />
        <LegendItem color="bg-cyan-500" label="Demo" />
        <LegendItem color="bg-red-500" label="Overdue" />
      </div>
    </div>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <span className="flex items-center gap-1.5">
      <span className={['w-2 h-2 rounded-full', color].join(' ')} />
      <span className="text-[10px] text-[var(--muted-foreground)]">{label}</span>
    </span>
  );
}
