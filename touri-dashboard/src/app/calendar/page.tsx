'use client';

import { useCallback, useEffect, useState } from 'react';
import { startOfMonth, endOfMonth, format } from 'date-fns';
import { CalendarDays, Loader2 } from 'lucide-react';
import { CampaignCalendar } from '@/components/calendar/campaign-calendar';
import type { CalendarEvent } from '@/lib/types';

export default function CalendarPage() {
  const [currentMonth, setCurrentMonth] = useState<Date>(() => {
    // Start on April 2026 (today's month)
    return new Date(2026, 3, 1); // month is 0-indexed
  });
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchEvents = useCallback(async (month: Date) => {
    setLoading(true);
    setError(null);
    try {
      const start = format(startOfMonth(month), 'yyyy-MM-dd');
      const end = format(endOfMonth(month), 'yyyy-MM-dd');
      const res = await fetch(`/api/calendar?start=${start}&end=${end}`, { cache: 'no-store' });
      const data = await res.json();
      if (data.error) {
        setError(data.message || 'Failed to load calendar events');
        setEvents([]);
      } else {
        setEvents(data.events ?? []);
      }
    } catch {
      setError('Failed to fetch calendar events');
      setEvents([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchEvents(currentMonth);
  }, [currentMonth, fetchEvents]);

  const handleMonthChange = useCallback(
    (date: Date) => {
      setCurrentMonth(date);
    },
    []
  );

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="border-b border-[var(--border)] px-5 py-3 shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-[var(--primary)]/15 flex items-center justify-center shrink-0">
            <CalendarDays className="w-4 h-4 text-[var(--primary)]" />
          </div>
          <div>
            <h1 className="font-semibold text-sm leading-tight">Calendar</h1>
            <p className="text-[11px] text-[var(--muted-foreground)] leading-tight">
              Follow-ups and demos
            </p>
          </div>
        </div>
        {error && (
          <div className="mt-2 p-2 bg-red-500/10 border border-red-500/30 rounded text-xs text-red-400">
            {error}
          </div>
        )}
      </div>

      {/* Calendar body */}
      <div className="flex-1 min-h-0 overflow-auto relative">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <Loader2 className="w-5 h-5 animate-spin text-[var(--muted-foreground)]" />
          </div>
        ) : (
          <CampaignCalendar
            events={events}
            currentMonth={currentMonth}
            onMonthChange={handleMonthChange}
          />
        )}
      </div>
    </div>
  );
}
