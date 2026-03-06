// Central reactive store for the Veneficus dashboard.
// Receives state from WebSocket and provides it to all components.

import { createSignal, createRoot } from "solid-js";
import { createStore, reconcile } from "solid-js/store";

export interface Agent {
  id: string;
  name: string;
  parent_id?: string;
  status: "working" | "idle" | "error" | "done";
  started_at: string;
  stopped_at?: string;
}

export interface TaskItem {
  id: string;
  subject: string;
  status: "pending" | "in_progress" | "completed";
  agent_id?: string;
  created_at: string;
  updated_at: string;
}

export interface DomainEvent {
  id: number;
  type: string;
  source_event: string;
  session_id: string;
  agent_id?: string;
  tool_name?: string;
  file_path?: string;
  details: Record<string, unknown>;
  tokens_estimate?: number;
  timestamp: string;
}

export interface FileOp {
  id: number;
  path: string;
  operation: "read" | "write" | "edit";
  agent_id?: string;
  timestamp: string;
}

export interface TokenEstimate {
  total_tokens: number;
  cost_usd: number;
}

export interface DashboardStore {
  agents: Agent[];
  tasks: TaskItem[];
  events: DomainEvent[];
  files: FileOp[];
  tokens: TokenEstimate;
  connected: boolean;
  sessionId: string;
}

const initialState: DashboardStore = {
  agents: [],
  tasks: [],
  events: [],
  files: [],
  tokens: { total_tokens: 0, cost_usd: 0 },
  connected: false,
  sessionId: "",
};

export const [store, setStore] = createStore<DashboardStore>(initialState);

export function loadFullState(state: any): void {
  setStore("agents", reconcile(state.agents || []));
  setStore("tasks", reconcile(state.tasks || []));
  setStore("events", reconcile((state.events || []).reverse()));
  setStore("files", reconcile(state.files || []));
  setStore("tokens", reconcile(state.tokens || { total_tokens: 0, cost_usd: 0 }));
  if (state.events?.length) {
    setStore("sessionId", state.events[0]?.session_id || "");
  }
}

export function addEvent(event: DomainEvent): void {
  setStore("events", (prev) => [event, ...prev].slice(0, 500));

  // Update agents if relevant
  if (event.type === "agent.spawn" && event.agent_id) {
    setStore("agents", (prev) => [
      ...prev,
      {
        id: event.agent_id!,
        name: event.agent_id!,
        parent_id: event.session_id,
        status: "working" as const,
        started_at: event.timestamp,
      },
    ]);
  }

  if ((event.type === "agent.stop" || event.type === "agent.idle") && event.agent_id) {
    setStore("agents", (a) => a.id === event.agent_id, "status",
      event.type === "agent.stop" ? "done" : "idle"
    );
  }

  // Update file activity
  if (event.file_path && event.type.startsWith("file.")) {
    setStore("files", (prev) => [
      {
        id: Date.now(),
        path: event.file_path!,
        operation: event.type.replace("file.", "") as "read" | "write" | "edit",
        agent_id: event.agent_id,
        timestamp: event.timestamp,
      },
      ...prev,
    ].slice(0, 200));
  }

  // Update tokens
  if (event.tokens_estimate) {
    setStore("tokens", "total_tokens", (t) => t + (event.tokens_estimate || 0));
    setStore("tokens", "cost_usd", (c) => c + ((event.tokens_estimate || 0) / 1_000_000) * 6);
  }

  // Update session ID
  if (event.session_id && !store.sessionId) {
    setStore("sessionId", event.session_id);
  }
}

export function setConnected(val: boolean): void {
  setStore("connected", val);
}
