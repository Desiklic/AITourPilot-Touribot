import Database from 'better-sqlite3';
import path from 'path';
import fs from 'fs';

import type { Memory } from '@/lib/types';

const TOURIBOT_HOME = process.env.TOURIBOT_HOME;
const MEMORY_DB_PATH = TOURIBOT_HOME
  ? path.join(TOURIBOT_HOME, 'data', 'memory.db')
  : null;

/**
 * Read-only connection to memory.db.
 * Re-opens each call to see latest WAL writes from Python.
 * Returns null if TOURIBOT_HOME is not set or DB file doesn't exist.
 */
function getMemoryDb(): Database.Database | null {
  if (!MEMORY_DB_PATH || !fs.existsSync(MEMORY_DB_PATH)) {
    return null;
  }

  const db = new Database(MEMORY_DB_PATH, { readonly: true, fileMustExist: true });
  db.pragma('busy_timeout = 5000');
  return db;
}

export function getMemories(type?: string, search?: string): Memory[] {
  const db = getMemoryDb();
  if (!db) return [];

  try {
    const conditions: string[] = [];
    const params: string[] = [];

    if (type) {
      conditions.push('type = ?');
      params.push(type);
    }
    if (search) {
      conditions.push('content LIKE ?');
      params.push(`%${search}%`);
    }

    const whereClause = conditions.length > 0 ? ` WHERE ${conditions.join(' AND ')}` : '';
    const sql = `SELECT * FROM memories${whereClause} ORDER BY created_at DESC`;

    return db.prepare(sql).all(...params) as Memory[];
  } finally {
    try { db.close(); } catch { /* ignore */ }
  }
}

export function getMemory(id: number): Memory | undefined {
  const db = getMemoryDb();
  if (!db) return undefined;

  try {
    return db.prepare('SELECT * FROM memories WHERE id = ?').get(id) as Memory | undefined;
  } finally {
    try { db.close(); } catch { /* ignore */ }
  }
}

export function getMemoryCount(): number {
  const db = getMemoryDb();
  if (!db) return 0;

  try {
    const row = db.prepare('SELECT COUNT(*) as total FROM memories').get() as { total: number };
    return row.total;
  } finally {
    try { db.close(); } catch { /* ignore */ }
  }
}
