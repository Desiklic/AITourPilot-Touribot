import { NextRequest, NextResponse } from 'next/server';
import { getContacts } from '@/lib/db/leads-db';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const sourceParam = searchParams.get('source');
    const stageParam = searchParams.get('stage');

    let stage: number | undefined;
    if (stageParam !== null) {
      stage = parseInt(stageParam, 10);
      if (isNaN(stage) || stage < 0 || stage > 10) {
        return NextResponse.json(
          { error: 'Invalid stage parameter (must be 0-10)' },
          { status: 400 }
        );
      }
    }

    const source = sourceParam ?? undefined;

    const contacts = getContacts(source, stage);
    return NextResponse.json({ contacts, total: contacts.length });
  } catch (err) {
    console.error('[GET /api/contacts]', err);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
