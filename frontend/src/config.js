/*
 * Runtime frontend network configuration for HTTP and WebSocket traffic.
 *
 * This file keeps API calls on same-origin relative paths while generating a
 * direct backend WebSocket URL in local development to avoid Vite proxy noise.
 */
export const API_BASE = "";

export function wsUrl(path) {
  /* Builds a websocket endpoint URL that matches local or deployed environments. */
  const isLocalDevHost =
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1";
  if (isLocalDevHost) {
    return `ws://127.0.0.1:8000${path}`;
  }
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}${path}`;
}
