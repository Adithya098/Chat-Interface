/**
 * Dispatch a toast notification.
 * type: "error" | "info" | "success"
 */
export function showToast(message, type = "error") {
  window.dispatchEvent(new CustomEvent("chat-toast", { detail: { message, type } }));
}
