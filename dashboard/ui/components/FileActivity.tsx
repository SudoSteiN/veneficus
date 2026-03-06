// FileActivity — File operations table with agent attribution
import { For, Show } from "solid-js";
import { store } from "../store";

export function FileActivity() {
  const shortPath = (path: string) => {
    const parts = path.split("/");
    return parts.slice(-2).join("/");
  };

  return (
    <Show
      when={store.files.length > 0}
      fallback={<div class="empty">No file activity yet.</div>}
    >
      <For each={store.files.slice(0, 50)}>
        {(file) => (
          <div class="file-item">
            <span class={`file-op ${file.operation}`}>
              {file.operation === "read" ? "R" : file.operation === "write" ? "W" : "E"}
            </span>
            <span class="file-path" title={file.path}>
              {shortPath(file.path)}
            </span>
          </div>
        )}
      </For>
    </Show>
  );
}
