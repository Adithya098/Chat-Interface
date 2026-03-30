/*
 * Admin moderation modal for pending room join requests across managed rooms.
 *
 * This component groups pending requests by room, resolves display names for
 * requesting users, and lets admins approve or reject each request while
 * notifying the parent to refresh membership state.
 */
import { useState, useEffect } from "react";
import { api } from "../hooks/useApi";
import { showToast } from "../utils/toast";
import "../styles/Modal.css";
import "../styles/AdminJoinRequestsModal.css";

export default function AdminJoinRequestsModal({ bundles, user, onClose, onChanged }) {
  /* Renders grouped pending join requests and moderation controls for admins. */
  const [names, setNames] = useState({});

  useEffect(() => {
    let cancelled = false;
    async function resolveNames() {
      const need = new Set();
      for (const b of bundles) {
        for (const p of b.pending) need.add(p.user_id);
      }
      const next = {};
      for (const uid of need) {
        try {
          const u = await api(`/users/${uid}`);
          next[u.id] = u.name;
        } catch {
          next[uid] = `User ${uid}`;
        }
      }
      if (!cancelled) setNames((prev) => ({ ...prev, ...next }));
    }
    if (bundles.length) resolveNames();
    return () => {
      cancelled = true;
    };
  }, [bundles]);

  const handleAction = async (roomId, targetUserId, action) => {
    /* Sends approve/reject action for a target user in a specific room. */
    try {
      await api(`/rooms/${roomId}/${action}`, {
        method: "POST",
        body: JSON.stringify({ admin_id: user.id, user_id: targetUserId }),
      });
      onChanged();
    } catch (err) {
      showToast(err.message);
    }
  };

  const total = bundles.reduce((n, b) => n + b.pending.length, 0);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content admin-join-modal"
        onClick={(e) => e.stopPropagation()}
      >
        <h3>Join requests</h3>
        <p className="admin-join-lead">
          {total === 1
            ? "Someone asked to join a room you manage."
            : `${total} people asked to join rooms you manage.`}
        </p>

        <div className="admin-join-bundles">
          {bundles.map(({ room, pending }) => (
            <section key={room.id} className="admin-join-room-block">
              <h4>{room.name}</h4>
              <ul className="admin-join-list">
                {pending.map((p) => (
                  <li key={p.id} className="admin-join-row">
                    <span className="admin-join-who">
                      {names[p.user_id] || `User ${p.user_id}`}
                      <span className={`badge badge-${p.role}`}>{p.role}</span>
                    </span>
                    <span className="admin-join-actions">
                      <button
                        type="button"
                        className="btn-approve"
                        onClick={() => handleAction(room.id, p.user_id, "approve")}
                      >
                        Approve
                      </button>
                      <button
                        type="button"
                        className="btn-reject"
                        onClick={() => handleAction(room.id, p.user_id, "reject")}
                      >
                        Reject
                      </button>
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>

        <button type="button" className="cancel-btn" onClick={onClose}>
          Close
        </button>
      </div>
    </div>
  );
}
