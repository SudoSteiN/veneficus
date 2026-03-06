// Header — Session info, connection status, cost summary
import { store } from "../store";

export function Header() {
  const formatCost = (usd: number) =>
    usd < 0.01 ? "<$0.01" : `$${usd.toFixed(2)}`;

  const formatTokens = (n: number) =>
    n > 1_000_000 ? `${(n / 1_000_000).toFixed(1)}M` :
    n > 1_000 ? `${(n / 1_000).toFixed(1)}K` :
    String(n);

  return (
    <div class="header">
      <div class="header-title">VENEFICUS</div>
      <div class="header-meta">
        <span>
          <span
            class={`status-dot ${store.connected ? "connected" : "disconnected"}`}
          />
          {store.connected ? "Live" : "Disconnected"}
        </span>
        <span>
          Session: <span class="value">{store.sessionId ? store.sessionId.slice(0, 8) : "—"}</span>
        </span>
        <span>
          Events: <span class="value">{store.events.length}</span>
        </span>
        <span class="token-info">
          <span>
            Tokens: <span class="value">{formatTokens(store.tokens.total_tokens)}</span>
          </span>
          <span>
            Cost: <span class="cost">{formatCost(store.tokens.cost_usd)}</span>
          </span>
        </span>
      </div>
    </div>
  );
}
