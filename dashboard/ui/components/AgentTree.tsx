// AgentTree — Agent hierarchy with status badges
import { For, Show } from "solid-js";
import { store } from "../store";

export function AgentTree() {
  const rootAgents = () => store.agents.filter((a) => !a.parent_id || a.parent_id === store.sessionId);
  const childAgents = (parentId: string) => store.agents.filter((a) => a.parent_id === parentId);

  return (
    <Show
      when={store.agents.length > 0}
      fallback={<div class="empty">No agents active. Start a Claude session to see agents here.</div>}
    >
      <For each={rootAgents()}>
        {(agent) => (
          <>
            <div class="agent-item">
              <span class={`agent-badge ${agent.status}`} />
              <span class="agent-name">{agent.name || agent.id}</span>
            </div>
            <For each={childAgents(agent.id)}>
              {(child) => (
                <div class="agent-item agent-sub">
                  <span class={`agent-badge ${child.status}`} />
                  <span class="agent-name">{child.name || child.id}</span>
                </div>
              )}
            </For>
          </>
        )}
      </For>
    </Show>
  );
}
