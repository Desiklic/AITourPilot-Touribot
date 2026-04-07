import Database from 'better-sqlite3';
import path from 'path';

import type { Museum, Contact, Interaction, Research } from '@/lib/types';
import { PIPELINE_STAGES } from '@/lib/constants';

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

// ─── Stats ───────────────────────────────────────────────────────────────────

interface StageCount {
  stage: number;
  count: number;
}

interface EmailStats {
  total_sent: number | null;
  total_drafts: number | null;
  responses_received: number | null;
}

interface TimelineRow {
  date: string;
  count: number;
  event_type: string | null;
}

interface ContactStats {
  total: number;
  with_email: number;
  primary_contacts: number;
}

interface CampaignStart {
  start_date: string | null;
}

interface MuseumsContacted {
  contacted: number;
}

interface ActiveMuseums {
  active: number;
}

export interface DashboardStats {
  pipeline: {
    total_museums: number;
    by_stage: Array<{ stage: number; name: string; count: number; color: string }>;
    active_museums: number;
  };
  emails: {
    total_sent: number;
    total_drafts: number;
    awaiting_reply: number;
    responses_received: number;
    conversion_rate: number;
  };
  activity: {
    timeline: Array<{ date: string; count: number; types: Record<string, number> }>;
    total_interactions: number;
    days_active: number;
  };
  contacts: {
    total: number;
    with_email: number;
    primary_contacts: number;
  };
  campaign: {
    start_date: string;
    days_running: number;
    avg_interactions_per_day: number;
    museums_contacted: number;
    velocity: number;
  };
}

export function getStats(): DashboardStats {
  const database = getDb();

  // ── Pipeline by stage ────────────────────────────────────────────────────
  const stageCounts = database
    .prepare<[], StageCount>(`SELECT stage, COUNT(*) as count FROM museums GROUP BY stage ORDER BY stage`)
    .all() as StageCount[];

  const stageCountMap = new Map<number, number>(stageCounts.map((r) => [r.stage, r.count]));
  const totalMuseums = stageCounts.reduce((sum, r) => sum + r.count, 0);

  const byStage = PIPELINE_STAGES.map((def) => ({
    stage: def.stage,
    name: def.name,
    count: stageCountMap.get(def.stage) ?? 0,
    color: def.color,
  }));

  const activeMuseums = (
    database
      .prepare<[], ActiveMuseums>(`SELECT COUNT(*) as active FROM museums WHERE stage > 0`)
      .get() as ActiveMuseums
  ).active;

  // ── Email stats ───────────────────────────────────────────────────────────
  const emailStats = database
    .prepare<[], EmailStats>(`
      SELECT
        SUM(CASE WHEN direction='outbound' AND channel='email' AND is_draft=0 THEN 1 ELSE 0 END) as total_sent,
        SUM(CASE WHEN is_draft=1 THEN 1 ELSE 0 END) as total_drafts,
        SUM(CASE WHEN direction='inbound' THEN 1 ELSE 0 END) as responses_received
      FROM interactions
    `)
    .get() as EmailStats;

  const totalSent = emailStats.total_sent ?? 0;
  const totalDrafts = emailStats.total_drafts ?? 0;
  const responsesReceived = emailStats.responses_received ?? 0;

  const awaitingReply = (
    database
      .prepare<[], { count: number }>(`SELECT COUNT(*) as count FROM museums WHERE stage IN (3, 4)`)
      .get() as { count: number }
  ).count;

  const conversionRate = totalSent > 0 ? responsesReceived / totalSent : 0;

  // ── Activity timeline (last 30 days) ─────────────────────────────────────
  const timelineRows = database
    .prepare<[], TimelineRow>(`
      SELECT DATE(created_at) as date, COUNT(*) as count, event_type
      FROM interactions
      WHERE created_at >= date('now', '-30 days')
      GROUP BY DATE(created_at), event_type
      ORDER BY date
    `)
    .all() as TimelineRow[];

  // Merge rows with same date, accumulating type counts
  const timelineMap = new Map<string, { count: number; types: Record<string, number> }>();
  for (const row of timelineRows) {
    const key = row.date;
    if (!timelineMap.has(key)) {
      timelineMap.set(key, { count: 0, types: {} });
    }
    const entry = timelineMap.get(key)!;
    entry.count += row.count;
    const typeName = row.event_type ?? 'unknown';
    entry.types[typeName] = (entry.types[typeName] ?? 0) + row.count;
  }
  const timeline = Array.from(timelineMap.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, data]) => ({ date, count: data.count, types: data.types }));

  const totalInteractions = (
    database
      .prepare<[], { total: number }>(`SELECT COUNT(*) as total FROM interactions`)
      .get() as { total: number }
  ).total;

  const daysActive = timeline.length;

  // ── Contact stats ─────────────────────────────────────────────────────────
  const contactStats = database
    .prepare<[], ContactStats>(`
      SELECT
        COUNT(*) as total,
        SUM(CASE WHEN email IS NOT NULL AND email != '' THEN 1 ELSE 0 END) as with_email,
        SUM(CASE WHEN is_primary = 1 THEN 1 ELSE 0 END) as primary_contacts
      FROM contacts
    `)
    .get() as ContactStats;

  // ── Campaign stats ────────────────────────────────────────────────────────
  const campaignStart = database
    .prepare<[], CampaignStart>(`SELECT MIN(created_at) as start_date FROM interactions`)
    .get() as CampaignStart;

  const startDateStr = campaignStart.start_date ?? new Date().toISOString();
  const startDate = new Date(startDateStr);
  const now = new Date();
  const daysRunning = Math.max(
    1,
    Math.floor((now.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24))
  );

  const avgInteractionsPerDay =
    totalInteractions > 0 ? Math.round((totalInteractions / daysRunning) * 100) / 100 : 0;

  const museumsContacted = (
    database
      .prepare<[], MuseumsContacted>(
        `SELECT COUNT(DISTINCT museum_id) as contacted FROM interactions WHERE direction='outbound'`
      )
      .get() as MuseumsContacted
  ).contacted;

  // Velocity: museums moved past stage 0 per week
  const velocity = daysRunning > 0 ? Math.round((activeMuseums / (daysRunning / 7)) * 100) / 100 : 0;

  return {
    pipeline: {
      total_museums: totalMuseums,
      by_stage: byStage,
      active_museums: activeMuseums,
    },
    emails: {
      total_sent: totalSent,
      total_drafts: totalDrafts,
      awaiting_reply: awaitingReply,
      responses_received: responsesReceived,
      conversion_rate: Math.round(conversionRate * 10000) / 10000, // 4 decimal precision
    },
    activity: {
      timeline,
      total_interactions: totalInteractions,
      days_active: daysActive,
    },
    contacts: {
      total: contactStats.total,
      with_email: contactStats.with_email,
      primary_contacts: contactStats.primary_contacts,
    },
    campaign: {
      start_date: startDateStr,
      days_running: daysRunning,
      avg_interactions_per_day: avgInteractionsPerDay,
      museums_contacted: museumsContacted,
      velocity,
    },
  };
}
