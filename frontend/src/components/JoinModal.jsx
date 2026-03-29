import { useState } from "react";
import { useChat } from "../context/ChatContext";
import { api } from "../hooks/useApi";
import "../styles/Modal.css";

export default function JoinModal({ room, onClose, onJoined }) {
  const { state } = useChat();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleJoin = async (role) => {
    setError("");
    setLoading(true);
    try {
      await api(`/rooms/${room.id}/join`, {
        method: "POST",
        body: JSON.stringify({ user_id: state.user.id, role }),
      });
      onJoined();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h3>Join Room: {room.name}</h3>
        <p>Select your desired role:</p>
        <div className="role-buttons">
          <button
            className="role-btn"
            onClick={() => handleJoin("read")}
            disabled={loading}
          >
            Reader
          </button>
          <button
            className="role-btn"
            onClick={() => handleJoin("write")}
            disabled={loading}
          >
            Writer
          </button>
        </div>
        <button className="cancel-btn" onClick={onClose}>
          Cancel
        </button>
        {error && <p className="error">{error}</p>}
      </div>
    </div>
  );
}
