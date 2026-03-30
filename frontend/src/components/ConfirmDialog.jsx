import { useState, useEffect } from "react";
import "../styles/ConfirmDialog.css";

export default function ConfirmDialog() {
  const [dialog, setDialog] = useState(null); // { message, resolve }

  useEffect(() => {
    const handler = (e) => setDialog(e.detail);
    window.addEventListener("chat-confirm", handler);
    return () => window.removeEventListener("chat-confirm", handler);
  }, []);

  if (!dialog) return null;

  const answer = (result) => {
    dialog.resolve(result);
    setDialog(null);
  };

  return (
    <div className="confirm-overlay" onClick={() => answer(false)}>
      <div className="confirm-dialog" onClick={(e) => e.stopPropagation()}>
        <p className="confirm-message">{dialog.message}</p>
        <div className="confirm-actions">
          <button className="confirm-cancel" onClick={() => answer(false)}>Cancel</button>
          <button className="confirm-ok" onClick={() => answer(true)}>OK</button>
        </div>
      </div>
    </div>
  );
}
