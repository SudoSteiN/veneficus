// CommLog — Agent-to-agent communication feed
import { For, Show, createMemo } from "solid-js";
import { store } from "../store";

export function CommLog() {
  // Filter events that represent agent communication
  const commEvents = createMemo(() =>
    store.events.filter((e) =>
      e.type === "agent.spawn" ||
      e.type === "agent.stop" ||
      e.type === "agent.idle" ||
      e.type === "task.complete" ||
      e.type === "notification" ||
      e.source_event === "SubagentStart" ||
      e.source_event === "SubagentStop" ||
      e.source_event === "TaskCompleted" ||
      e.source_event === "Notification"
    ).slice(0, 50)
  );

  const formatTime = (ts: string) => {
    try {
      return new Date(ts).toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" });
    } catch {
      return "—";
    }
  };

  const describe = (event: any) => {
    switch (event.type) {
      case "agent.spawn":
        return { agent: event.agent_id || "agent", action: "spawned" };
      case "agent.stop":
        return { agent: event.agent_id || "agent", action: "stopped" };
      case "agent.idle":
        return { agent: event.agent_id || "agent", action: "idle" };
      case "task.complete":
        return { agent: "system", action: "task completed" };
      case "notification":
        return { agent: "system", action: "notification" };
      default:
        return { agent: event.agent_id || "system", action: event.type };
    }
  };

  return (
    <Show
      when={commEvents().length > 0}
      fallback={<div class="empty">No agent communication yet.</div>}
    >
      <For each={commEvents()}>
        {(event) => {
          const d = describe(event);
          return (
            <div class="comm-item">
              <span class="hook-time">{formatTime(event.timestamp)}</span>{" "}
              <span class="comm-agent">{d.agent}</span>{" "}
              <span class="comm-action">{d.action}</span>
            </div>
          );
        }}
      </For>
    </Show>
  );
}
