import { useState, useEffect, useRef } from "react";
import { useChat } from "../context/ChatContext";
import { api } from "../hooks/useApi";
import "../styles/Members.css";

export default function MembersPanel({ onClose }) {
  const { state } = useChat();
  const { activeRoom, user } = state;
  const [members, setMembers] = useState([]);
  const [pending, setPending] = useState([]);
  const [names, setNames] = useState({});

  const isAdmin = activeRoom?.role === "admin";

  const loadMembersRef = useRef(async () => {});

  const loadMembers = async () => {
    if (!activeRoom) return;
    const admin = activeRoom.role === "admin";
    try {
      const all = await api(`/rooms/${activeRoom.id}/members`);
      const approved = all.filter((m) => m.status === "approved");
      setMembers(approved);

      // Resolve names
      const nameMap = { ...names };
      for (const m of all) {
        if (!nameMap[m.user_id]) {
          try {
            const u = await api(`/users/${m.user_id}`);
            nameMap[u.id] = u.name;
          } catch {
            nameMap[m.user_id] = `User ${m.user_id}`;
          }
        }
      }
      setNames(nameMap);

      if (admin) {
        const pend = await api(`/rooms/${activeRoom.id}/pending`);
        setPending(pend);
      } else {
        setPending([]);
      }
    } catch (err) {
      console.error("Failed to load members", err);
    }
  };

  loadMembersRef.current = loadMembers;

  useEffect(() => {
    loadMembers();
  }, [activeRoom?.id, activeRoom?.role]);

  useEffect(() => {
    const onMembersRefresh = () => loadMembersRef.current();
    window.addEventListener("chat-refresh-members", onMembersRefresh);
    return () => window.removeEventListener("chat-refresh-members", onMembersRefresh);
  }, []);

  const handleRemoveMember = async (targetUserId) => {
    if (!activeRoom || !user) return;
    if (!window.confirm("Remove this member from the room?")) return;
    try {
      await api(
        `/rooms/${activeRoom.id}/members/${targetUserId}?admin_id=${user.id}`,
        { method: "DELETE" }
      );
      loadMembers();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleAction = async (userId, action) => {
    try {
      await api(`/rooms/${activeRoom.id}/${action}`, {
        method: "POST",
        body: JSON.stringify({ admin_id: user.id, user_id: userId }),
      });
      loadMembers();
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <aside className="members-panel">
      <div className="panel-header">
        <h3>Members</h3>
        <button onClick={onClose}>&times;</button>
      </div>

      <div className="members-list">
        {members.map((m) => {
          const canRemove =
            isAdmin &&
            Number(m.user_id) !== Number(user?.id) &&
            m.role !== "admin";
          return (
            <div key={m.id} className="member-row">
              <span className="name">{names[m.user_id] || `User ${m.user_id}`}</span>
              <span className="member-row-actions">
                <span className={`badge badge-${m.role}`}>{m.role}</span>
                {canRemove && (
                  <button
                    type="button"
                    className="btn-remove"
                    title="Remove from room"
                    onClick={() => handleRemoveMember(m.user_id)}
                  >
                    Remove
                  </button>
                )}
              </span>
            </div>
          );
        })}
      </div>

      {isAdmin && pending.length > 0 && (
        <div className="pending-section">
          <h4>Pending Requests</h4>
          {pending.map((p) => (
            <div key={p.id} className="pending-row">
              <span className="name">
                {names[p.user_id] || `User ${p.user_id}`}
                <span className={`badge badge-${p.role}`}>{p.role}</span>
              </span>
              <button
                className="btn-approve"
                onClick={() => handleAction(p.user_id, "approve")}
              >
                Approve
              </button>
              <button
                className="btn-reject"
                onClick={() => handleAction(p.user_id, "reject")}
              >
                Reject
              </button>
            </div>
          ))}
        </div>
      )}
    </aside>
  );
}
