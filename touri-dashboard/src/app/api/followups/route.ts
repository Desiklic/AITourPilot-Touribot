import { NextResponse } from 'next/server';
import { getFollowUps } from '@/lib/db/leads-db';
import type { FollowUpTask } from '@/lib/types';

export const dynamic = 'force-dynamic';

// Today for bucketing (2026-04-07)
function getTodayStr(): string {
  return new Date().toISOString().slice(0, 10);
}

function getEndOfWeekStr(todayStr: string): string {
  const today = new Date(todayStr + 'T00:00:00');
  const dow = today.getDay(); // 0 = Sunday
  // Days until Saturday (end of this week, Sunday-anchored)
  const daysUntilSunday = 7 - dow;
  const endOfWeek = new Date(today);
  endOfWeek.setDate(today.getDate() + daysUntilSunday);
  return endOfWeek.toISOString().slice(0, 10);
}

function getEndOfNextWeekStr(todayStr: string): string {
  const endOfWeek = new Date(getEndOfWeekStr(todayStr) + 'T00:00:00');
  const endOfNextWeek = new Date(endOfWeek);
  endOfNextWeek.setDate(endOfWeek.getDate() + 7);
  return endOfNextWeek.toISOString().slice(0, 10);
}

export async function GET() {
  try {
    const tasks = getFollowUps();

    const today = getTodayStr();
    const endOfWeek = getEndOfWeekStr(today);
    const endOfNextWeek = getEndOfNextWeekStr(today);

    const overdue: FollowUpTask[] = [];
    const due_today: FollowUpTask[] = [];
    const this_week: FollowUpTask[] = [];
    const next_week: FollowUpTask[] = [];
    const later: FollowUpTask[] = [];

    for (const task of tasks) {
      const date = task.follow_up_date.slice(0, 10);
      if (date < today) {
        overdue.push(task);
      } else if (date === today) {
        due_today.push(task);
      } else if (date <= endOfWeek) {
        this_week.push(task);
      } else if (date <= endOfNextWeek) {
        next_week.push(task);
      } else {
        later.push(task);
      }
    }

    return NextResponse.json({
      overdue,
      due_today,
      this_week,
      next_week,
      later,
      total: tasks.length,
    });
  } catch (err) {
    console.error('[api/followups] error:', err);
    return NextResponse.json(
      { error: true, message: 'Failed to load follow-ups' },
      { status: 500 }
    );
  }
}
