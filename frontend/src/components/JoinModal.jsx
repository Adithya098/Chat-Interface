/*
 * Modal dialog for requesting access to a room with a selected role.
 *
 * This component sends membership requests for read/write/admin roles, shows a
 * confirmation state after submission, and communicates completion back to the
 * parent so room membership status can be refreshed.
 */
import { useState } from "react";
import { useChat } from "../context/ChatContext";
import { api } from "../hooks/useApi";
import "../styles/Modal.css";

export default function JoinModal({ room, onClose, onJoined }) {
  /* Renders role request options and tracks join-request submission state. */
  const { state } = useChat();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleJoin = async (role) => {
    /* Submits a join request for the selected role and updates local UI state. */
    setError("");
    setLoading(true);
    try {
      // user_id is resolved from the JWT on the backend — only role in body
      await api(`/rooms/${room.id}/join`, {
        method: "POST",
        body: JSON.stringify({ role }),
      });
      setSent(true);
      onJoined();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    /* Closes the modal and returns control to the parent component. */
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {sent ? (
          <>
            <h3>Request sent</h3>
            <p>
              Your request to join <strong>{room.name}</strong> was sent to the
              room admin. You will be able to open the room after they approve
              it.
            </p>
            <button type="button" className="role-btn" onClick={handleClose}>
              OK
            </button>
          </>
        ) : (
          <>
            <h3>Join Room: {room.name}</h3>
            <p>Request access. An admin must approve your request.</p>
            <div className="role-buttons">
              <button
                type="button"
                className="role-btn"
                onClick={() => handleJoin("read")}
                disabled={loading}
              >
                Reader
              </button>
              <button
                type="button"
                className="role-btn"
                onClick={() => handleJoin("write")}
                disabled={loading}
              >
                Writer
              </button>
              <button
                type="button"
                className="role-btn role-admin"
                onClick={() => handleJoin("admin")}
                disabled={loading}
              >
                Admin
              </button>
            </div>
            <button type="button" className="cancel-btn" onClick={handleClose}>
              Cancel
            </button>
            {error && <p className="error">{error}</p>}
          </>
        )}
      </div>
    </div>
  );
}
