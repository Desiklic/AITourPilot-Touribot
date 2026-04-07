import { NextResponse } from 'next/server';
import { getMemoryCount } from '@/lib/db/memory-db';
import { getDb } from '@/lib/db/settings-db';

// GET /api/settings
export async function GET() {
  const touribotHome = process.env.TOURIBOT_HOME ?? null;
  const apiUrl = process.env.TOURIBOT_API_URL ?? 'http://localhost:8765';

  // Memory count
  let memoryCount = 0;
  try {
    memoryCount = getMemoryCount();
  } catch { /* ignore */ }

  // Leads DB counts
  let museums = 0;
  let contacts = 0;
  let interactions = 0;
  try {
    const db = getDb();
    museums = (db.prepare('SELECT COUNT(*) as c FROM museums').get() as { c: number }).c;
    contacts = (db.prepare('SELECT COUNT(*) as c FROM contacts').get() as { c: number }).c;
    interactions = (db.prepare('SELECT COUNT(*) as c FROM interactions').get() as { c: number }).c;
  } catch { /* ignore */ }

  return NextResponse.json(
    {
      touribot_home: touribotHome,
      databases: {
        leads: { museums, contacts, interactions },
        memory: { memories: memoryCount },
      },
      api_url: apiUrl,
    },
    { headers: { 'Cache-Control': 'no-store' } }
  );
}
