/**
 * Drop-in replacement for window.confirm().
 * Returns a Promise<boolean> — resolves true on OK, false on Cancel.
 */
export function showConfirm(message) {
  return new Promise((resolve) => {
    window.dispatchEvent(new CustomEvent("chat-confirm", {
      detail: { message, resolve },
    }));
  });
}
