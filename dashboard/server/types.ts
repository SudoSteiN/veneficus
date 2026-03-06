// Shared TypeScript interfaces for Veneficus dashboard

export interface HookEvent {
  session_id?: string;
  hook_event_name: string;
  tool_name?: string;
  tool_input?: Record<string, unknown>;
  tool_response?: string;
  transcript_path?: string;
  cwd?: string;
  received_at: string;
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

export interface FileOp {
  id: number;
  path: string;
  operation: "read" | "write" | "edit";
  agent_id?: string;
  timestamp: string;
}

export interface TokenEstimate {
  session_id: string;
  total_tokens: number;
  cost_usd: number;
  by_agent: Record<string, number>;
}

export interface DashboardState {
  agents: Agent[];
  tasks: TaskItem[];
  events: DomainEvent[];
  files: FileOp[];
  tokens: TokenEstimate;
}

export interface WSMessage {
  type: "event" | "state" | "ping";
  payload: unknown;
}
