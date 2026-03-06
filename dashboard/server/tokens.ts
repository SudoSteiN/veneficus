// Token and cost estimation for Veneficus dashboard.
// Rough heuristic: ~4 characters per token.

const CHARS_PER_TOKEN = 4;

// Pricing per million tokens (blended input/output estimate)
const MODEL_PRICING: Record<string, number> = {
  "claude-sonnet-4-6": 6.0,    // ~$3 input + $15 output, blended
  "claude-opus-4-6": 30.0,     // ~$15 input + $75 output, blended
  "claude-haiku-4-5": 1.6,     // ~$0.8 input + $4 output, blended
  default: 6.0,
};

export function estimateTokens(text: string): number {
  if (!text) return 0;
  return Math.ceil(text.length / CHARS_PER_TOKEN);
}

export function estimateCost(tokens: number, model: string = "default"): number {
  const pricePerMillion = MODEL_PRICING[model] || MODEL_PRICING.default;
  return (tokens / 1_000_000) * pricePerMillion;
}

export function formatCost(usd: number): string {
  if (usd < 0.01) return `$${(usd * 100).toFixed(2)}¢`;
  return `$${usd.toFixed(2)}`;
}
