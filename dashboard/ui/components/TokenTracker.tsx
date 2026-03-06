// TokenTracker — Running token count and cost estimate
// Currently integrated into Header.tsx — this component provides a detailed view
import { store } from "../store";

export function TokenTracker() {
  const formatTokens = (n: number) =>
    n > 1_000_000
      ? `${(n / 1_000_000).toFixed(1)}M`
      : n > 1_000
      ? `${(n / 1_000).toFixed(1)}K`
      : String(n);

  const formatCost = (usd: number) =>
    usd < 0.01 ? "<$0.01" : `$${usd.toFixed(2)}`;

  return (
    <div>
      <div>
        Total tokens: <strong>{formatTokens(store.tokens.total_tokens)}</strong>
      </div>
      <div>
        Estimated cost: <strong class="cost">{formatCost(store.tokens.cost_usd)}</strong>
      </div>
    </div>
  );
}
