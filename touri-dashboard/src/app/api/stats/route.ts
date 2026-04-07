import { NextResponse } from 'next/server';
import { getStats } from '@/lib/db/leads-db';

export async function GET() {
  try {
    const stats = getStats();
    return NextResponse.json(stats);
  } catch (err) {
    console.error('[GET /api/stats]', err);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
