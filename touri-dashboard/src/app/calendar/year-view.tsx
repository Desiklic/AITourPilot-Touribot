'use client';

import { useMemo } from 'react';
import type { CalendarEvent } from '@/lib/types';

interface EventDotInfo {
  hasCyan: boolean;
  hasRed: boolean;
  hasAmber: boolean;
}

function getEventDotInfo(events: CalendarEvent[], dateStr: string, todayStr: string): EventDotInfo {
  let hasCyan = false, hasRed = false, hasAmber = false;
  for (const e of events) {
    if (e.follow_up_date.slice(0, 10) !== dateStr) continue;
    if (e.type === 'demo') { hasCyan = true; continue; }
    if (dateStr < todayStr) { hasRed = true; continue; }
    hasAmber = true;
  }
  return { hasCyan, hasRed, hasAmber };
}

interface MiniMonthProps {
  year: number;
  month: number;
  eventsByDay: Map<string, CalendarEvent[]>;
  today: Date;
  todayStr: string;
  onDayClick: (date: Date) => void;
}

function MiniMonth({ year, month, eventsByDay, today, todayStr, onDayClick }: MiniMonthProps) {
  const firstDay       = new Date(year, month, 1);
  const daysInMonth    = new Date(year, month + 1, 0).getDate();
  const dow            = firstDay.getDay();
  const startOffset    = dow === 0 ? 6 : dow - 1;
  const totalCells     = Math.ceil((daysInMonth + startOffset) / 7) * 7;
  const monthName      = firstDay.toLocaleDateString('en-US', { month: 'long' });
  const isCurrentMonth = today.getFullYear() === year && today.getMonth() === month;

  return (
    <div className="bg-[var(--card)] rounded-lg p-3">
      <p className={`text-xs font-semibold mb-2 ${isCurrentMonth ? 'text-[var(--primary)]' : 'text-[var(--foreground)]'}`}>
        {monthName}
      </p>
      <div className="grid grid-cols-7 gap-0">
        {['M', 'T', 'W', 'T', 'F', 'S', 'S'].map((d, i) => (
          <div key={i} className="text-center text-[8px] text-[var(--muted-foreground)] pb-0.5">
            {d}
          </div>
        ))}
        {Array.from({ length: totalCells }, (_, i) => {
          const dayNum = i - startOffset + 1;
          if (dayNum < 1 || dayNum > daysInMonth) return <div key={i} className="h-5" />;

          const date    = new Date(year, month, dayNum);
          const dateStr = date.toISOString().slice(0, 10);
          const isToday = date.toDateString() === today.toDateString();
          const dayEvents = eventsByDay.get(dateStr) || [];
          const hasEvent  = dayEvents.length > 0;

          // Determine dot color: prefer red (overdue) > cyan (demo) > amber (future)
          let dotClass = 'bg-[var(--primary)]/60';
          if (hasEvent) {
            const info = getEventDotInfo(dayEvents, dateStr, todayStr);
            if (info.hasRed)   dotClass = 'bg-red-500';
            else if (info.hasCyan)  dotClass = 'bg-cyan-500';
            else if (info.hasAmber) dotClass = 'bg-amber-500';
          }

          return (
            <div
              key={i}
              className="relative h-5 flex flex-col items-center justify-center cursor-pointer group"
              onClick={() => onDayClick(date)}
              title={`Open week of ${date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}`}
            >
              <span
                className={`text-[9px] w-4 h-4 flex items-center justify-center rounded-full leading-none transition-colors
                  ${isToday
                    ? 'bg-[var(--primary)] text-white font-bold'
                    : 'text-[var(--foreground)] group-hover:bg-[var(--primary)]/20 group-hover:text-[var(--primary)]'}`}
              >
                {dayNum}
              </span>
              {hasEvent && !isToday && (
                <span className={`absolute bottom-0 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full ${dotClass}`} />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

interface YearGridProps {
  events: CalendarEvent[];
  year: number;
  onDayClick: (date: Date) => void;
}

export function YearGrid({ events, year, onDayClick }: YearGridProps) {
  const today    = new Date();
  const todayStr = today.toISOString().slice(0, 10);

  const eventsByDay = useMemo(() => {
    const map = new Map<string, CalendarEvent[]>();
    events.forEach(e => {
      const key = e.follow_up_date.slice(0, 10);
      const arr = map.get(key) || [];
      arr.push(e);
      map.set(key, arr);
    });
    return map;
  }, [events]);

  return (
    <div className="flex-1 overflow-y-auto p-4">
      <div className="grid grid-cols-3 gap-4 max-w-3xl mx-auto">
        {Array.from({ length: 12 }, (_, i) => (
          <MiniMonth
            key={i}
            year={year}
            month={i}
            eventsByDay={eventsByDay}
            today={today}
            todayStr={todayStr}
            onDayClick={onDayClick}
          />
        ))}
      </div>
    </div>
  );
}
