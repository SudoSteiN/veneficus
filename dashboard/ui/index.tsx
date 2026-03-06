// Veneficus Dashboard — App root, WebSocket connection, store provider
import { render } from "solid-js/web";
import { onMount, onCleanup } from "solid-js";
import { store, loadFullState, addEvent, setConnected } from "./store";
import { Header } from "./components/Header";
import { AgentTree } from "./components/AgentTree";
import { TaskBoard } from "./components/TaskBoard";
import { HookFeed } from "./components/HookFeed";
import { ParallelExec } from "./components/ParallelExec";
import { CommLog } from "./components/CommLog";
import { FileActivity } from "./components/FileActivity";

function App() {
  let ws: WebSocket | null = null;
  let reconnectTimer: ReturnType<typeof setTimeout>;

  function connect() {
    const wsUrl = `ws://${window.location.hostname}:${window.location.port || 7777}/ws`;
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setConnected(true);
      console.log("[veneficus] Connected to dashboard");
    };

    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        if (msg.type === "state") {
          loadFullState(msg.payload);
        } else if (msg.type === "event") {
          addEvent(msg.payload);
        }
      } catch (err) {
        console.error("[veneficus] Bad message:", err);
      }
    };

    ws.onclose = () => {
      setConnected(false);
      console.log("[veneficus] Disconnected, reconnecting in 3s...");
      reconnectTimer = setTimeout(connect, 3000);
    };

    ws.onerror = () => {
      ws?.close();
    };
  }

  onMount(() => {
    connect();
  });

  onCleanup(() => {
    clearTimeout(reconnectTimer);
    ws?.close();
  });

  return (
    <>
      <Header />
      <div class="dashboard-grid">
        <div class="panel agent-tree">
          <div class="panel-header">Agent Tree</div>
          <div class="panel-content">
            <AgentTree />
          </div>
        </div>

        <div class="panel task-board">
          <div class="panel-header">Task Board</div>
          <div class="panel-content">
            <TaskBoard />
          </div>
        </div>

        <div class="panel hook-feed">
          <div class="panel-header">Hook Feed</div>
          <div class="panel-content">
            <HookFeed />
          </div>
        </div>

        <div class="panel parallel-exec">
          <div class="panel-header">Threads</div>
          <div class="panel-content">
            <ParallelExec />
          </div>
        </div>

        <div class="panel comm-log">
          <div class="panel-header">Communication Log</div>
          <div class="panel-content">
            <CommLog />
          </div>
        </div>

        <div class="panel file-activity">
          <div class="panel-header">File Activity</div>
          <div class="panel-content">
            <FileActivity />
          </div>
        </div>
      </div>
    </>
  );
}

render(() => <App />, document.getElementById("app")!);
