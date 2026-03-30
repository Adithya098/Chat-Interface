/*
 * Global toast notifier used by components to display transient status messages.
 *
 * This helper dispatches a custom browser event consumed by the toast banner
 * component, allowing non-related components to surface errors and feedback.
 */
export function showToast(message, type = "error") {
  /* Emits a toast event with message text and semantic type. */
  window.dispatchEvent(new CustomEvent("chat-toast", { detail: { message, type } }));
}
