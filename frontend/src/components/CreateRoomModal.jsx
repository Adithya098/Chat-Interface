/*
 * Modal dialog for creating a new chat room.
 *
 * This component collects a room name, validates basic input, submits a room
 * creation request using the current user as creator, and notifies the parent
 * when creation succeeds so room lists can refresh.
 */
import { useState } from "react";
import { useChat } from "../context/ChatContext";
import { api } from "../hooks/useApi";
import "../styles/Modal.css";

export default function CreateRoomModal({ onClose, onCreated }) {
  /* Renders room creation form and drives submit/cancel modal behavior. */
  const { state } = useChat();
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleCreate = async (e) => {
    /* Validates and sends room creation request, then signals success upstream. */
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
