import { NextRequest, NextResponse } from 'next/server';
import { getCalendarEvents } from '@/lib/db/leads-db';

export const dynamic = 'force-dynamic';

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = req.nextUrl;
    const start = searchParams.get('start');
    const end = searchParams.get('end');

    if (!start || !end) {
      return NextResponse.json(
        { error: true, message: 'start and end query params are required (ISO date strings)' },
        { status: 400 }
      );
    }

    // Normalise to YYYY-MM-DD if full ISO datetime strings were passed
    const startDate = start.slice(0, 10);
    const endDate = end.slice(0, 10);

    const events = getCalendarEvents(startDate, endDate);
    return NextResponse.json({ events });
  } catch (err) {
    console.error('[api/calendar] error:', err);
    return NextResponse.json(
      { error: true, message: 'Failed to load calendar events' },
      { status: 500 }
    );
  }
}
