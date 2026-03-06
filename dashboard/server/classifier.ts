// Maps raw hook events to domain events for the dashboard.

import type { HookEvent, DomainEvent } from "./types";
import { estimateTokens } from "./tokens";

type PartialDomainEvent = Omit<DomainEvent, "id">;

export function classify(raw: HookEvent): PartialDomainEvent {
  const base: PartialDomainEvent = {
    type: "unknown",
    source_event: raw.hook_event_name || "unknown",
    session_id: raw.session_id || "",
    agent_id: "",
    tool_name: raw.tool_name || "",
    file_path: "",
    details: {},
    tokens_estimate: 0,
    timestamp: raw.received_at || new Date().toISOString(),
  };

  const input = raw.tool_input || {};

  switch (raw.hook_event_name) {
    // ── Agent lifecycle ──
    case "SubagentStart":
      return {
        ...base,
        type: "agent.spawn",
        agent_id: (input as any).agent_id || (input as any).name || "",
        details: { input },
      };

    case "SubagentStop":
      return {
        ...base,
        type: "agent.stop",
        agent_id: (input as any).agent_id || (input as any).name || "",
        details: { input },
      };

    // ── Tool usage ──
    case "PreToolUse":
      return {
        ...base,
        type: `tool.pre.${raw.tool_name || "unknown"}`,
        file_path: extractFilePath(input),
        details: { tool_input: input },
        tokens_estimate: estimateTokens(JSON.stringify(input)),
      };

    case "PostToolUse": {
      const filePath = extractFilePath(input);
      const opType = mapToolToOp(raw.tool_name || "");
      return {
        ...base,
        type: opType ? `file.${opType}` : `tool.post.${raw.tool_name || "unknown"}`,
        file_path: filePath,
        details: { tool_input: input },
        tokens_estimate: estimateTokens(JSON.stringify(input) + (raw.tool_response || "")),
      };
    }

    case "PostToolUseFailure":
      return {
        ...base,
        type: `tool.failure.${raw.tool_name || "unknown"}`,
        file_path: extractFilePath(input),
        details: { tool_input: input, response: raw.tool_response },
        tokens_estimate: estimateTokens(raw.tool_response || ""),
      };

    // ── Task lifecycle ──
    case "TaskCompleted":
      return {
        ...base,
        type: "task.complete",
        details: { input },
      };

    // ── Session lifecycle ──
    case "Stop":
      return {
        ...base,
        type: "session.stop",
        details: { input },
      };

    case "SessionEnd":
      return {
        ...base,
        type: "session.end",
        details: { input },
      };

    // ── Communication ──
    case "Notification":
      return {
        ...base,
        type: "notification",
        details: { input },
      };

    case "TeammateIdle":
      return {
        ...base,
        type: "agent.idle",
        agent_id: (input as any).agent_id || "",
        details: { input },
      };

    default:
      return {
        ...base,
        type: `raw.${raw.hook_event_name || "unknown"}`,
        details: { raw },
      };
  }
}

function extractFilePath(input: Record<string, unknown>): string {
  return (input.file_path as string) || (input.path as string) || "";
}

function mapToolToOp(toolName: string): string | null {
  switch (toolName) {
    case "Write":
      return "write";
    case "Edit":
      return "edit";
    case "Read":
      return "read";
    default:
      return null;
  }
}
