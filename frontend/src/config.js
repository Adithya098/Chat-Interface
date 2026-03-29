/**
 * Always use same-origin requests — Vite's proxy (vite.config.js) forwards
 * /users, /rooms, /ws, etc. to the backend in dev.  In production the FastAPI
 * server serves both the SPA and the API on the same origin.
 */
export const API_BASE = "";

export function wsUrl(path) {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}${path}`;
}
