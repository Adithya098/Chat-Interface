/**
 * HTTP uses same-origin paths (proxied by Vite in dev, same-origin in prod).
 * WebSocket uses direct backend URL in local dev to avoid noisy Vite ws-proxy logs.
 */
export const API_BASE = "";

export function wsUrl(path) {
  const isLocalDevHost =
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1";
  if (isLocalDevHost) {
    return `ws://127.0.0.1:8000${path}`;
  }
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}${path}`;
}
