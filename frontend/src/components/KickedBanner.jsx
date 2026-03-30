import { useState, useEffect } from "react";

export default function KickedBanner() {
  const [toasts, setToasts] = useState([]);

  const addToast = (message, type = "error") => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => removeToast(id), 5000);
  };

  const removeToast = (id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  useEffect(() => {
    // Removed from room
    const kickedHandler = (e) => {
      addToast(e.detail?.message || "You were removed from this room", "error");
    };
    // General toasts (errors, info, success)
    const toastHandler = (e) => {
      addToast(e.detail?.message, e.detail?.type || "error");
    };

    window.addEventListener("chat-kicked", kickedHandler);
    window.addEventListener("chat-toast", toastHandler);
    return () => {
      window.removeEventListener("chat-kicked", kickedHandler);
      window.removeEventListener("chat-toast", toastHandler);
    };
  }, []);

  if (!toasts.length) return null;

  return (
    <div className="toast-container">
      {toasts.map((t) => (
        <div key={t.id} className={`toast toast-${t.type}`}>
          <span className="toast-icon">
            {t.type === "error" ? "⚠" : t.type === "success" ? "✓" : "ℹ"}
          </span>
          <span className="toast-text">{t.message}</span>
          <button className="toast-close" onClick={() => removeToast(t.id)}>×</button>
        </div>
      ))}
    </div>
  );
}
