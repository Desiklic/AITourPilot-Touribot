'use client';

import { useEffect, useState, useCallback, useMemo } from 'react';
import { CalendarDays, ChevronLeft, ChevronRight, RefreshCw, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { CalendarEvent } from '@/lib/types';
import { WeekGrid } from './week-view';
import { MonthGrid } from './month-view';
import { YearGrid } from './year-view';

type ViewMode = 'week' | 'month' | 'year';

// ── Date helpers ───────────────────────────────────────────────────────────────

function getWeekDays(offset: number): Date[] {
  const now = new Date();
  const dow = now.getDay();
  const daysToMon = dow === 0 ? -6 : 1 - dow;
  const monday = new Date(now);
  monday.setDate(now.getDate() + daysToMon + offset * 7);
  monday.setHours(0, 0, 0, 0);
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(monday);
    d.setDate(monday.getDate() + i);
    return d;
  });
}

function getDateRange(mode: ViewMode, offset: number): { start: Date; end: Date } {
  const now = new Date();
  if (mode === 'week') {
    const days = getWeekDays(offset);
    const end  = new Date(days[6]);
    end.setDate(days[6].getDate() + 1);
    return { start: days[0], end };
  }
  if (mode === 'month') {
    const base = new Date(now.getFullYear(), now.getMonth() + offset, 1);
    return { start: base, end: new Date(base.getFullYear(), base.getMonth() + 1, 1) };
  }
  // year
  const yr = now.getFullYear() + offset;
  return { start: new Date(yr, 0, 1), end: new Date(yr + 1, 0, 1) };
}

/** Returns the week offset (Mon-anchored) from today's week to the week containing `date`. */
function weekOffsetForDate(date: Date): number {
  const now = new Date();
  const dow = now.getDay();
  const currentMonday = new Date(now);
  currentMonday.setDate(now.getDate() + (dow === 0 ? -6 : 1 - dow));
  currentMonday.setHours(0, 0, 0, 0);

  const tdow = date.getDay();
  const targetMonday = new Date(date);
  targetMonday.setDate(date.getDate() + (tdow === 0 ? -6 : 1 - tdow));
  targetMonday.setHours(0, 0, 0, 0);

  return Math.round((targetMonday.getTime() - currentMonday.getTime()) / (7 * 86_400_000));
}

function getNavLabel(mode: ViewMode, offset: number): string {
  const now = new Date();
  if (mode === 'week') {
    const days  = getWeekDays(offset);
    const start = days[0];
    const end   = days[6];
    const sm    = start.toLocaleDateString('en-US', { month: 'short' });
    const em    = end.toLocaleDateString('en-US', { month: 'short' });
    const yr    = end.getFullYear() !== now.getFullYear() ? ` ${end.getFullYear()}` : '';
    return sm === em
      ? `${start.getDate()}–${end.getDate()} ${em}${yr}`
      : `${start.getDate()} ${sm} – ${end.getDate()} ${em}${yr}`;
  }
  if (mode === 'month') {
    const base = new Date(now.getFullYear(), now.getMonth() + offset, 1);
    return base.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  }
  return String(now.getFullYear() + offset);
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function CalendarPage() {
  const [viewMode, setViewMode]   = useState<ViewMode>('month');
  const [navOffset, setNavOffset] = useState(0);
  const [events, setEvents]       = useState<CalendarEvent[]>([]);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState<string | null>(null);

  // Reset offset when switching views
  const switchView = useCallback((mode: ViewMode) => {
    setViewMode(mode);
    setNavOffset(0);
  }, []);

  // Cross-view navigation: clicking a day in month/year jumps to that week
  const handleDayClick = useCallback((date: Date) => {
    setViewMode('week');
    setNavOffset(weekOffsetForDate(date));
  }, []);

  // ── Fetch events ─────────────────────────────────────────────────────────────

  const fetchEvents = useCallback(async (mode: ViewMode, offset: number) => {
    setLoading(true);
    setError(null);
    const { start, end } = getDateRange(mode, offset);
    // API expects YYYY-MM-DD
    const startStr = start.toISOString().slice(0, 10);
    const endStr   = end.toISOString().slice(0, 10);
    try {
      const res  = await fetch(`/api/calendar?start=${startStr}&end=${endStr}`, { cache: 'no-store' });
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

  useEffect(() => { fetchEvents(viewMode, navOffset); }, [viewMode, navOffset, fetchEvents]);

  // ── Derived state ─────────────────────────────────────────────────────────────

  const weekDays = useMemo(() => getWeekDays(navOffset), [navOffset]);

  const monthInfo = useMemo(() => {
    const now  = new Date();
    const base = new Date(now.getFullYear(), now.getMonth() + (viewMode === 'month' ? navOffset : 0), 1);
    return { year: base.getFullYear(), month: base.getMonth() };
  }, [viewMode, navOffset]);

  const yearValue = useMemo(
    () => new Date().getFullYear() + (viewMode === 'year' ? navOffset : 0),
    [viewMode, navOffset],
  );

  const navLabel = useMemo(() => getNavLabel(viewMode, navOffset), [viewMode, navOffset]);

  // ── Render ────────────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col h-full bg-[var(--background)] text-[var(--foreground)] overflow-hidden">

      {/* ── Header ── */}
      <div className="border-b border-[var(--border)] px-4 py-2.5 shrink-0">
        <div className="flex items-center justify-between gap-3">

          {/* Left: icon + title */}
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-[var(--primary)]/15 flex items-center justify-center shrink-0">
              <CalendarDays className="w-4 h-4 text-[var(--primary)]" />
            </div>
            <div>
              <span className="font-semibold text-sm leading-tight block">Calendar</span>
              <span className="text-[11px] text-[var(--muted-foreground)] leading-tight">Follow-ups and demos</span>
            </div>
          </div>

          {/* Centre: view-mode switcher */}
          <div className="flex items-center gap-0.5 bg-[var(--muted)]/50 rounded-lg p-0.5">
            {(['week', 'month', 'year'] as ViewMode[]).map(mode => (
              <button
                key={mode}
                onClick={() => switchView(mode)}
                className={`px-3 py-1 text-xs rounded-md capitalize transition-colors
                  ${viewMode === mode
                    ? 'bg-[var(--card)] text-[var(--foreground)] shadow-sm'
                    : 'text-[var(--muted-foreground)] hover:text-[var(--foreground)]'}`}
              >
                {mode}
              </button>
            ))}
          </div>

          {/* Right: navigation */}
          <div className="flex items-center gap-1">
            <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => setNavOffset(o => o - 1)}>
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <button
              onClick={() => setNavOffset(0)}
              className="text-xs text-[var(--muted-foreground)] hover:text-[var(--foreground)] px-2 py-1 rounded hover:bg-[var(--muted)]/40 transition-colors min-w-[130px] text-center tabular-nums"
            >
              {navLabel}
            </button>
            <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => setNavOffset(o => o + 1)}>
              <ChevronRight className="w-4 h-4" />
            </Button>
            {navOffset !== 0 && (
              <Button variant="ghost" size="sm" className="h-7 px-2 text-xs" onClick={() => setNavOffset(0)}>
                Today
              </Button>
            )}
            <Button
              variant="ghost" size="sm" className="h-7 w-7 p-0 ml-1"
              onClick={() => fetchEvents(viewMode, navOffset)}
              title="Refresh"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </Button>
          </div>

        </div>

        {error && (
          <div className="mt-1.5 p-2 bg-red-500/10 border border-red-500/30 rounded text-xs text-red-400">
            {error}
          </div>
        )}
      </div>

      {/* ── Calendar area ── */}
      <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center flex-1">
            <Loader2 className="w-5 h-5 animate-spin text-[var(--muted-foreground)]" />
          </div>
        ) : viewMode === 'week' ? (
          <WeekGrid events={events} days={weekDays} />
        ) : viewMode === 'month' ? (
          <MonthGrid events={events} year={monthInfo.year} month={monthInfo.month} onDayClick={handleDayClick} />
        ) : (
          <YearGrid events={events} year={yearValue} onDayClick={handleDayClick} />
        )}
      </div>

      {/* ── Legend ── */}
      <div className="flex items-center gap-4 px-4 py-2 border-t border-[var(--border)] shrink-0 bg-[var(--card)]">
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
      <span className={`w-2 h-2 rounded-full ${color}`} />
      <span className="text-[10px] text-[var(--muted-foreground)]">{label}</span>
    </span>
  );
}
