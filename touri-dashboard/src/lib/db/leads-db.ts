import Database from 'better-sqlite3';
import path from 'path';

import type { Museum, Contact, Interaction, Research } from '@/lib/types';

const TOURIBOT_HOME = process.env.TOURIBOT_HOME;
if (!TOURIBOT_HOME) throw new Error('TOURIBOT_HOME environment variable is not set');

const LEADS_DB_PATH = path.join(TOURIBOT_HOME, 'data', 'leads.db');

let db: Database.Database | null = null;

function getDb(): Database.Database {
  if (!db) {
    db = new Database(LEADS_DB_PATH);
    db.pragma('journal_mode = WAL');
    db.pragma('busy_timeout = 5000');
    db.pragma('foreign_keys = ON');
  }
  return db;
}

// Extended types for query results with joined fields
type MuseumRow = Museum & {
  primary_contact_name: string | null;
  primary_contact_email: string | null;
  last_activity: string | null;
};

type InteractionRow = Interaction & {
  contact_name: string | null;
};

// ─── Museums ────────────────────────────────────────────────────────────────

const MUSEUMS_BASE_QUERY = `
  SELECT m.*,
    c.full_name as primary_contact_name,
    c.email    as primary_contact_email,
    (SELECT MAX(created_at) FROM interactions WHERE museum_id = m.id) as last_activity
  FROM museums m
  LEFT JOIN contacts c ON c.museum_id = m.id AND c.is_primary = 1
`;

export function getMuseums(stage?: number): MuseumRow[] {
  const database = getDb();

  if (stage !== undefined) {
    const stmt = database.prepare<[number]>(
      `${MUSEUMS_BASE_QUERY} WHERE m.stage = ? ORDER BY m.stage ASC, m.name ASC`
    );
    return stmt.all(stage) as MuseumRow[];
  }

  const stmt = database.prepare(
    `${MUSEUMS_BASE_QUERY} ORDER BY m.stage ASC, m.name ASC`
  );
  return stmt.all() as MuseumRow[];
}

export function getMuseum(id: number): MuseumRow | undefined {
  const database = getDb();
  const stmt = database.prepare<[number]>(
    `${MUSEUMS_BASE_QUERY} WHERE m.id = ?`
  );
  return stmt.get(id) as MuseumRow | undefined;
}

export function getMuseumDetail(id: number): {
  museum: MuseumRow | undefined;
  contacts: Contact[];
  interactions: InteractionRow[];
  research: Research[];
} {
  const database = getDb();

  const museum = getMuseum(id);

  const contactsStmt = database.prepare<[number]>(
    `SELECT * FROM contacts WHERE museum_id = ? ORDER BY is_primary DESC, created_at ASC`
  );
  const contacts = contactsStmt.all(id) as Contact[];

  const interactionsStmt = database.prepare<[number]>(`
    SELECT i.*, c.full_name as contact_name
    FROM interactions i
    LEFT JOIN contacts c ON c.id = i.contact_id
    WHERE i.museum_id = ?
    ORDER BY i.created_at DESC
  `);
  const interactions = interactionsStmt.all(id) as InteractionRow[];

  const researchStmt = database.prepare<[number]>(
    `SELECT * FROM research WHERE museum_id = ? AND is_current = 1`
  );
  const research = researchStmt.all(id) as Research[];

  return { museum, contacts, interactions, research };
}

export function updateMuseum(
  id: number,
  data: { stage?: number; score?: number | null; notes?: string }
): MuseumRow | undefined {
  const database = getDb();

  // Verify the museum exists before updating
  const existing = getMuseum(id);
  if (!existing) return undefined;

  const setClauses: string[] = [];
  const values: (number | string | null)[] = [];

  if (data.stage !== undefined) {
    setClauses.push('stage = ?');
    values.push(data.stage);
    setClauses.push("stage_updated_at = datetime('now')");
  }

  if ('score' in data) {
    setClauses.push('score = ?');
    values.push(data.score ?? null);
  }

  if (data.notes !== undefined) {
    setClauses.push('notes = ?');
    values.push(data.notes);
  }

  // Always update updated_at
  setClauses.push("updated_at = datetime('now')");

  if (setClauses.length === 1) {
    // Only updated_at — nothing substantive changed, just return existing
    return existing;
  }

  // Append the id for the WHERE clause
  values.push(id);

  const sql = `UPDATE museums SET ${setClauses.join(', ')} WHERE id = ?`;
  const stmt = database.prepare(sql);
  stmt.run(...values);

  return getMuseum(id);
}

// ─── Interactions ────────────────────────────────────────────────────────────

export function getInteractionHistory(museumId: number): InteractionRow[] {
  const database = getDb();
  const stmt = database.prepare<[number]>(`
    SELECT i.*, c.full_name as contact_name
    FROM interactions i
    LEFT JOIN contacts c ON c.id = i.contact_id
    WHERE i.museum_id = ?
    ORDER BY i.created_at DESC
  `);
  return stmt.all(museumId) as InteractionRow[];
}
