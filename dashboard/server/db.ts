// SQLite database for Veneficus dashboard
// Uses Bun's built-in SQLite support

import { Database } from "bun:sqlite";
import type { DomainEvent, Agent, TaskItem, FileOp } from "./types";

let db: Database;

export function initDB(path: string = "veneficus.db"): Database {
  db = new Database(path, { create: true });
  db.exec("PRAGMA journal_mode = WAL;");
  db.exec("PRAGMA synchronous = NORMAL;");
  migrate();
  return db;
}

function migrate(): void {
  db.exec(`
    CREATE TABLE IF NOT EXISTS events (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      type TEXT NOT NULL,
      source_event TEXT NOT NULL,
      session_id TEXT DEFAULT '',
      agent_id TEXT DEFAULT '',
      tool_name TEXT DEFAULT '',
      file_path TEXT DEFAULT '',
      details TEXT DEFAULT '{}',
      tokens_estimate INTEGER DEFAULT 0,
      timestamp TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS agents (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      parent_id TEXT DEFAULT '',
      status TEXT DEFAULT 'idle',
      started_at TEXT NOT NULL,
      stopped_at TEXT DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS tasks (
      id TEXT PRIMARY KEY,
      subject TEXT NOT NULL,
      status TEXT DEFAULT 'pending',
      agent_id TEXT DEFAULT '',
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS file_activity (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      path TEXT NOT NULL,
      operation TEXT NOT NULL,
      agent_id TEXT DEFAULT '',
      timestamp TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS token_estimates (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id TEXT NOT NULL,
      agent_id TEXT DEFAULT '',
      tokens INTEGER DEFAULT 0,
      timestamp TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);
    CREATE INDEX IF NOT EXISTS idx_events_type ON events(type);
    CREATE INDEX IF NOT EXISTS idx_file_activity_path ON file_activity(path);
  `);
}

// ── Event operations ──

export function insertEvent(event: Omit<DomainEvent, "id">): DomainEvent {
  const stmt = db.prepare(`
    INSERT INTO events (type, source_event, session_id, agent_id, tool_name, file_path, details, tokens_estimate, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);
  const result = stmt.run(
    event.type,
    event.source_event,
    event.session_id,
    event.agent_id || "",
    event.tool_name || "",
    event.file_path || "",
    JSON.stringify(event.details),
    event.tokens_estimate || 0,
    event.timestamp
  );
  return { ...event, id: Number(result.lastInsertRowid) };
}

export function getRecentEvents(limit: number = 100): DomainEvent[] {
  const rows = db.prepare(
    "SELECT * FROM events ORDER BY id DESC LIMIT ?"
  ).all(limit) as any[];

  return rows.map(row => ({
    ...row,
    details: JSON.parse(row.details || "{}"),
  }));
}

// ── Agent operations ──

export function upsertAgent(agent: Agent): void {
  db.prepare(`
    INSERT INTO agents (id, name, parent_id, status, started_at, stopped_at)
    VALUES (?, ?, ?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
      status = excluded.status,
      stopped_at = excluded.stopped_at
  `).run(
    agent.id,
    agent.name,
    agent.parent_id || "",
    agent.status,
    agent.started_at,
    agent.stopped_at || ""
  );
}

export function getAgents(): Agent[] {
  return db.prepare("SELECT * FROM agents ORDER BY started_at").all() as Agent[];
}

// ── Task operations ──

export function upsertTask(task: TaskItem): void {
  db.prepare(`
    INSERT INTO tasks (id, subject, status, agent_id, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
      subject = excluded.subject,
      status = excluded.status,
      agent_id = excluded.agent_id,
      updated_at = excluded.updated_at
  `).run(
    task.id,
    task.subject,
    task.status,
    task.agent_id || "",
    task.created_at,
    task.updated_at
  );
}

export function getTasks(): TaskItem[] {
  return db.prepare("SELECT * FROM tasks ORDER BY created_at").all() as TaskItem[];
}

// ── File activity operations ──

export function insertFileOp(op: Omit<FileOp, "id">): FileOp {
  const result = db.prepare(`
    INSERT INTO file_activity (path, operation, agent_id, timestamp)
    VALUES (?, ?, ?, ?)
  `).run(op.path, op.operation, op.agent_id || "", op.timestamp);

  return { ...op, id: Number(result.lastInsertRowid) };
}

export function getRecentFileOps(limit: number = 50): FileOp[] {
  return db.prepare(
    "SELECT * FROM file_activity ORDER BY id DESC LIMIT ?"
  ).all(limit) as FileOp[];
}

// ── Token operations ──

export function addTokenEstimate(sessionId: string, agentId: string, tokens: number): void {
  db.prepare(`
    INSERT INTO token_estimates (session_id, agent_id, tokens, timestamp)
    VALUES (?, ?, ?, datetime('now'))
  `).run(sessionId, agentId, tokens);
}

export function getTokenTotals(sessionId?: string): { total_tokens: number; cost_usd: number } {
  const where = sessionId ? "WHERE session_id = ?" : "";
  const params = sessionId ? [sessionId] : [];
  const row = db.prepare(
    `SELECT COALESCE(SUM(tokens), 0) as total_tokens FROM token_estimates ${where}`
  ).get(...params) as any;

  const total = row?.total_tokens || 0;
  // Rough estimate: $3/MTok input, $15/MTok output (Sonnet pricing) — blended ~$6/MTok
  const costPerToken = 6 / 1_000_000;

  return { total_tokens: total, cost_usd: total * costPerToken };
}

export function getDB(): Database {
  return db;
}
