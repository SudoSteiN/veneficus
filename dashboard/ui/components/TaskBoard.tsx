// TaskBoard — Kanban: pending / in_progress / completed
import { For, Show, createMemo } from "solid-js";
import { store } from "../store";

export function TaskBoard() {
  const pending = createMemo(() => store.tasks.filter((t) => t.status === "pending"));
  const active = createMemo(() => store.tasks.filter((t) => t.status === "in_progress"));
  const completed = createMemo(() => store.tasks.filter((t) => t.status === "completed"));

  return (
    <Show
      when={store.tasks.length > 0}
      fallback={<div class="empty">No tasks tracked. Tasks will appear when agents create them.</div>}
    >
      <div class="task-columns">
        <div class="task-column">
          <div class="task-column-header">Pending ({pending().length})</div>
          <For each={pending()}>
            {(task) => (
              <div class="task-card">
                <div class="task-id">#{task.id}</div>
                <div class="task-subject">{task.subject}</div>
              </div>
            )}
          </For>
        </div>

        <div class="task-column">
          <div class="task-column-header">In Progress ({active().length})</div>
          <For each={active()}>
            {(task) => (
              <div class="task-card">
                <div class="task-id">#{task.id}</div>
                <div class="task-subject">{task.subject}</div>
              </div>
            )}
          </For>
        </div>

        <div class="task-column">
          <div class="task-column-header">Done ({completed().length})</div>
          <For each={completed()}>
            {(task) => (
              <div class="task-card">
                <div class="task-id">#{task.id}</div>
                <div class="task-subject">{task.subject}</div>
              </div>
            )}
          </For>
        </div>
      </div>
    </Show>
  );
}
