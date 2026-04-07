import { NextRequest, NextResponse } from 'next/server';
import { getInteractionHistory } from '@/lib/db/leads-db';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const museumId = parseInt(id, 10);
    if (isNaN(museumId)) {
      return NextResponse.json({ error: 'Invalid ID' }, { status: 400 });
    }

    const interactions = getInteractionHistory(museumId);
    return NextResponse.json({ interactions, total: interactions.length });
  } catch (err) {
    console.error('[GET /api/leads/[id]/history]', err);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
