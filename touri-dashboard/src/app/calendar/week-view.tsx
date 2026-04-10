'use client';

import { useMemo } from 'react';
import { useRouter } from 'next/navigation';
import type { CalendarEvent } from '@/lib/types';

const WEEKDAY_ABBR = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

function eventPillClass(event: CalendarEvent, todayStr: string): string {
  if (event.type === 'demo') return 'bg-cyan-100 text-cyan-800';
  const eventDate = event.follow_up_date.slice(0, 10);
  if (eventDate < todayStr) return 'bg-red-100 text-red-800';
  return 'bg-amber-100 text-amber-800';
}

interface WeekGridProps {
  events: CalendarEvent[];
  days: Date[];
}

export function WeekGrid({ events, days }: WeekGridProps) {
  const router = useRouter();
  const today = new Date();
  const todayStr = today.toISOString().slice(0, 10);

  const eventsByDay = useMemo(() => {
    const map = new Map<string, CalendarEvent[]>();
    days.forEach(d => map.set(d.toDateString(), []));
    events.forEach(e => {
      // Match on follow_up_date (YYYY-MM-DD)
      const dateStr = e.follow_up_date.slice(0, 10);
      // Find the day in our week that matches
      for (const d of days) {
        const dStr = d.toISOString().slice(0, 10);
        if (dStr === dateStr) {
          const arr = map.get(d.toDateString()) || [];
          arr.push(e);
          map.set(d.toDateString(), arr);
          break;
        }
      }
    });
    return map;
  }, [events, days]);

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      {/* Day headers */}
      <div className="grid grid-cols-7 border-b border-[var(--border)] bg-[var(--background)] shrink-0">
        {days.map((day, i) => {
          const isToday = day.toDateString() === today.toDateString();
          const isWeekend = day.getDay() === 0 || day.getDay() === 6;
          return (
            <div
              key={day.toISOString()}
              className={`py-2.5 text-center border-r border-[var(--border)] last:border-r-0 ${isWeekend ? 'bg-[var(--muted)]/20' : ''}`}
            >
              <p className="text-[10px] font-semibold text-[var(--muted-foreground)] uppercase tracking-wider">
                {WEEKDAY_ABBR[i]}
              </p>
              <p
                className={`text-lg font-semibold leading-tight mt-0.5 ${
                  isToday
                    ? 'text-white bg-[var(--primary)] w-7 h-7 rounded-full flex items-center justify-center mx-auto text-sm'
                    : 'text-[var(--foreground)]'
                }`}
              >
                {day.getDate()}
              </p>
            </div>
          );
        })}
      </div>

      {/* Day columns — scrollable */}
      <div className="flex-1 overflow-y-auto">
        <div className="grid grid-cols-7 h-full min-h-[300px]">
          {days.map((day, i) => {
            const dayEvents = eventsByDay.get(day.toDateString()) || [];
            const isWeekend = day.getDay() === 0 || day.getDay() === 6;
            return (
              <div
                key={day.toISOString()}
                className={`border-r border-[var(--border)] last:border-r-0 p-1.5 flex flex-col gap-1 ${
                  isWeekend ? 'bg-[var(--muted)]/10' : 'bg-[var(--card)]'
                }`}
              >
                {dayEvents.map(event => (
                  <button
                    key={`${event.type}-${event.id}`}
                    onClick={() => router.push(`/pipeline/${event.museum_id}`)}
                    title={event.follow_up_action ?? event.museum_name}
                    className={`text-[10px] truncate rounded px-1.5 py-1 text-left w-full hover:opacity-80 transition-opacity leading-tight ${eventPillClass(event, todayStr)}`}
                  >
                    {event.museum_name}
                    {event.follow_up_action && (
                      <span className="block text-[9px] opacity-70 truncate">{event.follow_up_action}</span>
                    )}
                  </button>
                ))}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
