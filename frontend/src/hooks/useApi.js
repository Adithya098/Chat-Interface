/*
 * HTTP utility helpers for backend API requests and file uploads.
 *
 * This file normalizes backend error payloads, enforces request timeouts, adds
 * default headers for JSON endpoints, and exposes convenience wrappers for
 * generic API calls and multipart room file uploads.
 */
import { API_BASE } from "../config.js";

const BASE = API_BASE;

const API_TIMEOUT_MS = 30_000;

function formatDetail(detail) {
  /* Converts varied backend error detail formats into readable text. */
  if (detail == null || detail === "") return "";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail))
    return detail.map((x) => (typeof x?.msg === "string" ? x.msg : JSON.stringify(x))).join("; ");
  if (typeof detail === "object" && typeof detail.msg === "string") return detail.msg;
  try {
    return JSON.stringify(detail);
  } catch {
    return String(detail);
  }
}

async function fetchWithTimeout(url, opts = {}) {
  /* Runs fetch with an abort timeout and user-friendly timeout errors. */
  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), API_TIMEOUT_MS);
  try {
    return await fetch(url, { ...opts, signal: controller.signal });
  } catch (e) {
    if (e.name === "AbortError") {
      throw new Error(
        "Request timed out. Is the API running (port 8000)? Open the URL Vite prints (e.g. :3001 if 3000 is busy)."
      );
    }
    throw e;
  } finally {
    clearTimeout(t);
  }
}

export async function api(path, opts = {}) {
  /* Performs a JSON API request and throws normalized errors on failure. */
  const method = (opts.method || "GET").toUpperCase();
  const headers = { ...opts.headers };
  if (method !== "DELETE" && headers["Content-Type"] === undefined) {
    headers["Content-Type"] = "application/json";
  }
  const res = await fetchWithTimeout(`${BASE}${path}`, {
    headers,
    ...opts,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(formatDetail(err.detail) || res.statusText);
  }
  return res.json();
}

export async function uploadFile(roomId, userId, file) {
  /* Uploads a file to a room endpoint using multipart form data. */
  const form = new FormData();
  form.append("user_id", userId);
  form.append("file", file);

  const res = await fetchWithTimeout(`${BASE}/rooms/${roomId}/upload`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(formatDetail(err.detail) || "Upload failed");
  }
  return res.json();
}
