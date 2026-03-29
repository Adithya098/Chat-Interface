import { useState } from "react";
import { useChat } from "../context/ChatContext";
import { api } from "../hooks/useApi";
import "../styles/Modal.css";

export default function CreateRoomModal({ onClose, onCreated }) {
  const { state } = useChat();
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!name.trim()) {
      setError("Room name is required");
      return;
    }
    setError("");
    setLoading(true);
    try {
      await api("/rooms/", {
        method: "POST",
        body: JSON.stringify({ name: name.trim(), created_by: state.user.id }),
      });
      onCreated();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h3>Create New Room</h3>
        <form onSubmit={handleCreate}>
          <input
            type="text"
            placeholder="Room name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            autoFocus
          />
          <button type="submit" disabled={loading}>
            {loading ? "Creating..." : "Create"}
          </button>
          <button type="button" className="cancel-btn" onClick={onClose}>
            Cancel
          </button>
        </form>
        {error && <p className="error">{error}</p>}
      </div>
    </div>
  );
}
