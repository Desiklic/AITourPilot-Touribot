'use client';

import { useMemo } from 'react';
import { useRouter } from 'next/navigation';
import type { CalendarEvent } from '@/lib/types';

const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

function eventPillClass(event: CalendarEvent, todayStr: string): string {
  if (event.type === 'demo') return 'bg-cyan-100 text-cyan-800';
  const eventDate = event.follow_up_date.slice(0, 10);
  if (eventDate < todayStr) return 'bg-red-100 text-red-800';
  return 'bg-amber-100 text-amber-800';
}

interface MonthGridProps {
  events: CalendarEvent[];
  year: number;
  month: number; // 0-indexed
  onDayClick: (date: Date) => void;
}

export function MonthGrid({ events, year, month, onDayClick }: MonthGridProps) {
  const router = useRouter();
  const firstDay    = new Date(year, month, 1);
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const dow         = firstDay.getDay(); // 0=Sun
  const startOffset = dow === 0 ? 6 : dow - 1; // days from Monday
  const totalCells  = Math.ceil((daysInMonth + startOffset) / 7) * 7;
  const today       = new Date();
  const todayStr    = today.toISOString().slice(0, 10);

  const eventsByDay = useMemo(() => {
    const map = new Map<string, CalendarEvent[]>();
    events.forEach(e => {
      const key = e.follow_up_date.slice(0, 10); // YYYY-MM-DD
      const arr = map.get(key) || [];
      arr.push(e);
      map.set(key, arr);
    });
    return map;
  }, [events]);

  return (
    <div className="flex-1 overflow-y-auto p-3">
      {/* Weekday headers */}
      <div className="grid grid-cols-7 mb-1">
        {WEEKDAYS.map(d => (
          <div key={d} className="text-center text-xs font-medium text-[var(--muted-foreground)] py-1">
            {d}
          </div>
        ))}
      </div>

      {/* Day cells */}
      <div className="grid grid-cols-7 gap-px bg-[var(--border)]">
        {Array.from({ length: totalCells }, (_, i) => {
          const dayNum = i - startOffset + 1;
          if (dayNum < 1 || dayNum > daysInMonth) {
            return <div key={i} className="bg-[var(--background)] min-h-[90px]" />;
          }
          const date      = new Date(year, month, dayNum);
          const dateStr   = date.toISOString().slice(0, 10);
          const isToday   = date.toDateString() === today.toDateString();
          const isWeekend = date.getDay() === 0 || date.getDay() === 6;
          const dayEvents = eventsByDay.get(dateStr) || [];

          return (
            <div
              key={i}
              onClick={() => onDayClick(date)}
              className={`min-h-[90px] p-1.5 cursor-pointer group transition-colors
                ${isWeekend ? 'bg-[var(--muted)]/20 hover:bg-[var(--muted)]/40' : 'bg-[var(--card)] hover:bg-[var(--muted)]/20'}`}
              title={`Open week of ${date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}`}
            >
              <p
                className={`text-xs font-semibold mb-1 w-5 h-5 flex items-center justify-center rounded-full transition-colors
                  ${isToday
                    ? 'bg-[var(--primary)] text-white'
                    : 'text-[var(--foreground)] group-hover:bg-[var(--primary)]/20 group-hover:text-[var(--primary)]'}`}
              >
                {dayNum}
              </p>
              <div className="space-y-0.5">
                {dayEvents.slice(0, 3).map(event => (
                  <button
                    key={`${event.type}-${event.id}`}
                    onClick={e => { e.stopPropagation(); router.push(`/pipeline/${event.museum_id}`); }}
                    title={event.follow_up_action ?? event.museum_name}
                    className={`text-[9px] truncate rounded px-1 py-0.5 leading-tight w-full text-left hover:opacity-80 transition-opacity ${eventPillClass(event, todayStr)}`}
                  >
                    {event.museum_name}
                  </button>
                ))}
                {dayEvents.length > 3 && (
                  <p className="text-[9px] text-[var(--muted-foreground)] pl-0.5">
                    +{dayEvents.length - 3} more
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
