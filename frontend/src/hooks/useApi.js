const BASE = "";  // same origin — Vite proxy handles it in dev

export async function api(path, opts = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...opts.headers },
    ...opts,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

export async function uploadFile(roomId, userId, file) {
  const form = new FormData();
  form.append("user_id", userId);
  form.append("file", file);

  const res = await fetch(`${BASE}/rooms/${roomId}/upload`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Upload failed");
  }
  return res.json();
}
