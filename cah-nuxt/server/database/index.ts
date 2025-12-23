import Database from 'better-sqlite3'
import { drizzle } from 'drizzle-orm/better-sqlite3'
import { join } from 'path'
import * as schema from './schema'

let _db: ReturnType<typeof drizzle<typeof schema>> | null = null

export function useDB() {
  if (!_db) {
    const dbPath = join(process.cwd(), 'data', 'cah.db')
    const sqlite = new Database(dbPath)
    sqlite.pragma('journal_mode = WAL')
    _db = drizzle(sqlite, { schema })
  }
  return _db
}

export { schema }
