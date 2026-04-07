import { NextRequest, NextResponse } from 'next/server';
import { getMuseumDetail, updateMuseum } from '@/lib/db/leads-db';

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

    const detail = getMuseumDetail(museumId);
    if (!detail.museum) {
      return NextResponse.json({ error: 'Museum not found' }, { status: 404 });
    }

    return NextResponse.json(detail);
  } catch (err) {
    console.error('[GET /api/leads/[id]]', err);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const museumId = parseInt(id, 10);
    if (isNaN(museumId)) {
      return NextResponse.json({ error: 'Invalid ID' }, { status: 400 });
    }

    const body = await request.json();

    // Validate stage
    if (body.stage !== undefined) {
      if (!Number.isInteger(body.stage) || body.stage < 0 || body.stage > 10) {
        return NextResponse.json(
          { error: 'Stage must be 0-10' },
          { status: 400 }
        );
      }
    }

    // Validate score (null is allowed to clear it)
    if (body.score !== undefined && body.score !== null) {
      if (!Number.isInteger(body.score) || body.score < 1 || body.score > 5) {
        return NextResponse.json(
          { error: 'Score must be 1-5' },
          { status: 400 }
        );
      }
    }

    const updated = updateMuseum(museumId, body);
    if (!updated) {
      return NextResponse.json({ error: 'Museum not found' }, { status: 404 });
    }

    return NextResponse.json({ museum: updated });
  } catch (err) {
    console.error('[PATCH /api/leads/[id]]', err);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
