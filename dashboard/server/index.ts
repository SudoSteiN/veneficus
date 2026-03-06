// Veneficus Dashboard — Bun server
// HTTP (event ingestion + API + static files) + WebSocket (real-time pub/sub)

import { initDB, insertEvent, getRecentEvents, upsertAgent, getAgents, upsertTask, getTasks, insertFileOp, getRecentFileOps, addTokenEstimate, getTokenTotals } from "./db";
import { classify } from "./classifier";
import type { HookEvent, Agent, WSMessage } from "./types";

const PORT = Number(process.env.VENEFICUS_PORT) || 7777;
const STATIC_DIR = new URL("../ui", import.meta.url).pathname;

// Initialize database
const db = initDB(process.env.VENEFICUS_DB || "veneficus.db");

// Track WebSocket clients
const wsClients = new Set<any>();

function broadcast(msg: WSMessage): void {
  const data = JSON.stringify(msg);
  for (const ws of wsClients) {
    try {
      ws.send(data);
    } catch {
      wsClients.delete(ws);
    }
  }
}

// Build the initial state bundle for new WebSocket connections
function getFullState() {
  return {
    agents: getAgents(),
    tasks: getTasks(),
    events: getRecentEvents(200),
    files: getRecentFileOps(100),
    tokens: getTokenTotals(),
  };
}

const server = Bun.serve({
  port: PORT,

  async fetch(req, server) {
    const url = new URL(req.url);

    // ── WebSocket upgrade ──
    if (url.pathname === "/ws") {
      if (server.upgrade(req)) return undefined;
      return new Response("WebSocket upgrade failed", { status: 400 });
    }

    // ── API: Ingest events ──
    if (url.pathname === "/api/events" && req.method === "POST") {
      try {
        const raw: HookEvent = await req.json();
        const domainEvent = classify(raw);
        const saved = insertEvent(domainEvent);

        // Side effects: update agents, files, tokens
        if (domainEvent.type === "agent.spawn") {
          const agent: Agent = {
            id: domainEvent.agent_id || `agent-${Date.now()}`,
            name: domainEvent.agent_id || "subagent",
            parent_id: domainEvent.session_id,
            status: "working",
            started_at: domainEvent.timestamp,
          };
          upsertAgent(agent);
        }

        if (domainEvent.type === "agent.stop" || domainEvent.type === "agent.idle") {
          const agent: Agent = {
            id: domainEvent.agent_id || "",
            name: domainEvent.agent_id || "subagent",
            status: domainEvent.type === "agent.stop" ? "done" : "idle",
            started_at: domainEvent.timestamp,
            stopped_at: domainEvent.type === "agent.stop" ? domainEvent.timestamp : undefined,
          };
          if (agent.id) upsertAgent(agent);
        }

        if (domainEvent.file_path && domainEvent.type.startsWith("file.")) {
          insertFileOp({
            path: domainEvent.file_path,
            operation: domainEvent.type.replace("file.", "") as "read" | "write" | "edit",
            agent_id: domainEvent.agent_id,
            timestamp: domainEvent.timestamp,
          });
        }

        if (domainEvent.tokens_estimate) {
          addTokenEstimate(
            domainEvent.session_id,
            domainEvent.agent_id || "",
            domainEvent.tokens_estimate
          );
        }

        // Broadcast to all WebSocket clients
        broadcast({ type: "event", payload: saved });

        return Response.json({ ok: true, id: saved.id });
      } catch (err) {
        return Response.json({ error: String(err) }, { status: 400 });
      }
    }

    // ── API: Get state ──
    if (url.pathname === "/api/state" && req.method === "GET") {
      return Response.json(getFullState());
    }

    // ── API: Get events ──
    if (url.pathname === "/api/events" && req.method === "GET") {
      const limit = Number(url.searchParams.get("limit")) || 100;
      return Response.json(getRecentEvents(limit));
    }

    // ── API: Get agents ──
    if (url.pathname === "/api/agents" && req.method === "GET") {
      return Response.json(getAgents());
    }

    // ── API: Get tokens ──
    if (url.pathname === "/api/tokens" && req.method === "GET") {
      return Response.json(getTokenTotals());
    }

    // ── Static files ──
    if (url.pathname === "/" || url.pathname === "/index.html") {
      const file = Bun.file(`${STATIC_DIR}/index.html`);
      if (await file.exists()) {
        return new Response(file, { headers: { "Content-Type": "text/html" } });
      }
    }

    // Serve static assets
    const filePath = `${STATIC_DIR}${url.pathname}`;
    const file = Bun.file(filePath);
    if (await file.exists()) {
      return new Response(file);
    }

    return new Response("Not Found", { status: 404 });
  },

  websocket: {
    open(ws) {
      wsClients.add(ws);
      // Send full state on connect
      ws.send(JSON.stringify({ type: "state", payload: getFullState() }));
    },
    message(ws, message) {
      // Handle ping/pong
      try {
        const msg = JSON.parse(String(message));
        if (msg.type === "ping") {
          ws.send(JSON.stringify({ type: "pong" }));
        }
      } catch {
        // Ignore invalid messages
      }
    },
    close(ws) {
      wsClients.delete(ws);
    },
  },
});

console.log(`\x1b[32m[veneficus]\x1b[0m Dashboard running at http://localhost:${PORT}`);
console.log(`\x1b[32m[veneficus]\x1b[0m WebSocket at ws://localhost:${PORT}/ws`);
console.log(`\x1b[32m[veneficus]\x1b[0m Event API at http://localhost:${PORT}/api/events`);
