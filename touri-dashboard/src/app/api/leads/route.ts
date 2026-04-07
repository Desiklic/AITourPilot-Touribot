import { NextRequest, NextResponse } from 'next/server';
import { getMuseums } from '@/lib/db/leads-db';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
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

    const museums = getMuseums(stage);
    return NextResponse.json({ museums, total: museums.length });
  } catch (err) {
    console.error('[GET /api/leads]', err);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
