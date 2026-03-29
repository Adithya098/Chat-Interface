import { useState, useEffect } from "react";
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

  useEffect(() => {
    loadMembers();
  }, [activeRoom?.id, activeRoom?.role]);

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
        {members.map((m) => (
          <div key={m.id} className="member-row">
            <span className="name">{names[m.user_id] || `User ${m.user_id}`}</span>
            <span className={`badge badge-${m.role}`}>{m.role}</span>
          </div>
        ))}
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
