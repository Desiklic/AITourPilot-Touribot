import { NextRequest, NextResponse } from 'next/server';
import { getMemories } from '@/lib/db/memory-db';

// GET /api/memory?type=fact&search=BTU
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const type = searchParams.get('type') ?? undefined;
  const search = searchParams.get('search') ?? undefined;

  try {
    const memories = getMemories(type, search);
    return NextResponse.json(
      { memories, total: memories.length },
      { headers: { 'Cache-Control': 'no-store' } }
    );
  } catch (err) {
    console.error('[GET /api/memory]', err);
    return NextResponse.json(
      { error: String(err), memories: [], total: 0 },
      { status: 500, headers: { 'Cache-Control': 'no-store' } }
    );
  }
}
