import Database from 'better-sqlite3';
import path from 'path';
import fs from 'fs';

const TOURIBOT_HOME = process.env.TOURIBOT_HOME;
const LEADS_DB_PATH = TOURIBOT_HOME
  ? path.join(TOURIBOT_HOME, 'data', 'leads.db')
  : null;

let db: Database.Database | null = null;

/**
 * Read-only connection to leads.db for settings/stats queries.
 * Returns a shared singleton; safe for read queries.
 */
export function getDb(): Database.Database {
  if (!LEADS_DB_PATH) {
    throw new Error('TOURIBOT_HOME environment variable is not set');
  }
  if (!fs.existsSync(LEADS_DB_PATH)) {
    throw new Error(`leads.db not found at ${LEADS_DB_PATH}`);
  }
  if (!db) {
    db = new Database(LEADS_DB_PATH, { readonly: true, fileMustExist: true });
    db.pragma('busy_timeout = 5000');
  }
  return db;
}
