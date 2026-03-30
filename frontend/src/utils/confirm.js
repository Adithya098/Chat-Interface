/*
 * Promise-based confirm utility that delegates UI to the shared dialog component.
 *
 * This helper emits a global event carrying message and resolver callbacks, so
 * any component can request a confirmation without directly rendering modal UI.
 */
export function showConfirm(message) {
  /* Triggers the confirm dialog and resolves to true or false based on user choice. */
  return new Promise((resolve) => {
    window.dispatchEvent(new CustomEvent("chat-confirm", {
      detail: { message, resolve },
    }));
  });
}
