import { useState } from "react";
import { useChat } from "../context/ChatContext";
import { api } from "../hooks/useApi";
import "../styles/Modal.css";

export default function JoinModal({ room, onClose, onJoined }) {
  const { state } = useChat();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleJoin = async (role) => {
    setError("");
    setLoading(true);
    try {
      await api(`/rooms/${room.id}/join`, {
        method: "POST",
        body: JSON.stringify({ user_id: state.user.id, role }),
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
