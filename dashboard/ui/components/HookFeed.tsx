// HookFeed — Real-time hook triggers and outcomes
import { For, Show } from "solid-js";
import { store } from "../store";

export function HookFeed() {
  const formatTime = (ts: string) => {
    try {
      const d = new Date(ts);
      return d.toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" });
    } catch {
      return "—";
    }
  };

  const eventClass = (type: string) => {
    if (type.includes("failure")) return "failure";
    if (type.startsWith("file.write") || type.startsWith("file.edit")) return "success";
    return "";
  };

  const shortType = (type: string) => {
    return type.replace("tool.pre.", "pre:").replace("tool.post.", "post:").replace("file.", "");
  };

  const shortDetail = (event: any) => {
    if (event.file_path) {
      const parts = event.file_path.split("/");
      return parts.slice(-2).join("/");
    }
    if (event.tool_name) return event.tool_name;
    if (event.agent_id) return event.agent_id;
    return event.source_event;
  };

  return (
    <Show
      when={store.events.length > 0}
      fallback={<div class="empty">Waiting for hook events...</div>}
    >
      <For each={store.events.slice(0, 100)}>
        {(event) => (
          <div class={`hook-item ${eventClass(event.type)}`}>
            <span class="hook-time">{formatTime(event.timestamp)}</span>
            <span class="hook-type">{shortType(event.type)}</span>
            <span class="hook-detail">{shortDetail(event)}</span>
          </div>
        )}
      </For>
    </Show>
  );
}
