// ParallelExec — Active threads by type (P/F/C/L)
import { For, Show, createMemo } from "solid-js";
import { store } from "../store";

export function ParallelExec() {
  // Infer thread types from agent patterns and events
  const threads = createMemo(() => {
    const active: Array<{ type: string; label: string; agents: string[] }> = [];

    // Look for patterns in active agents
    const workingAgents = store.agents.filter((a) => a.status === "working");

    if (workingAgents.length > 1) {
      // Multiple parallel agents = likely P-Thread
      active.push({
        type: "P",
        label: `${workingAgents.length} parallel agents`,
        agents: workingAgents.map((a) => a.name || a.id),
      });
    }

    // Check events for thread markers
    const recentEvents = store.events.slice(0, 20);
    for (const event of recentEvents) {
      const details = event.details || {};
      if ((details as any).thread_type) {
        const tt = (details as any).thread_type as string;
        if (!active.some((t) => t.type === tt)) {
          active.push({
            type: tt,
            label: `${tt}-Thread active`,
            agents: [(details as any).agent_id || "agent"],
          });
        }
      }
    }

    return active;
  });

  return (
    <Show
      when={threads().length > 0}
      fallback={<div class="empty">No active threads.</div>}
    >
      <For each={threads()}>
        {(thread) => (
          <div class="thread-item">
            <span class={`thread-type ${thread.type}`}>{thread.type}</span>
            <span>{thread.label}</span>
          </div>
        )}
      </For>
    </Show>
  );
}
