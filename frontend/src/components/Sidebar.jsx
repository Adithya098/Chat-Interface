import { useState, useEffect, useCallback } from "react";
import { useChat } from "../context/ChatContext";
import { api } from "../hooks/useApi";
import JoinModal from "./JoinModal";
import CreateRoomModal from "./CreateRoomModal";
import "../styles/Sidebar.css";

export default function Sidebar({ onEnterRoom }) {
  const { state, dispatch } = useChat();
  const { user, rooms, activeRoom } = state;
  const [search, setSearch] = useState("");
  const [joinTarget, setJoinTarget] = useState(null);
  const [showCreate, setShowCreate] = useState(false);

  const loadRooms = useCallback(async () => {
    try {
      const allRooms = await api("/rooms/");
      const enriched = await Promise.all(
        allRooms.map(async (room) => {
          try {
            const members = await api(`/rooms/${room.id}/members`);
            const me = members.find((m) => m.user_id === user.id);
            return { ...room, membership: me || null };
          } catch {
            return { ...room, membership: null };
          }
        })
      );
      dispatch({ type: "SET_ROOMS", payload: enriched });
    } catch (err) {
      console.error("Failed to load rooms", err);
    }
  }, [user, dispatch]);

  useEffect(() => {
    loadRooms();
  }, [loadRooms]);

  const filtered = rooms
    .filter((r) => r.name.toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => {
      const order = (m) => {
        if (!m) return 3;
        if (m.status === "approved") return 0;
        if (m.status === "pending") return 1;
        return 2;
      };
      return order(a.membership) - order(b.membership);
    });

  const handleRoomClick = (room) => {
    const m = room.membership;
    if (m && m.status === "approved") {
      onEnterRoom(room, m.role);
    } else if (m && m.status === "pending") {
      alert("Your join request is pending admin approval.");
    } else if (m && m.status === "rejected") {
      alert("Your join request was rejected.");
    } else {
      setJoinTarget(room);
    }
  };

  const badgeFor = (m) => {
    if (!m) return null;
    if (m.status === "approved")
      return <span className={`badge badge-${m.role}`}>{m.role}</span>;
    if (m.status === "pending")
      return <span className="badge badge-pending">pending</span>;
    if (m.status === "rejected")
      return <span className="badge badge-rejected">rejected</span>;
    return null;
  };

  const handleLogout = () => {
    dispatch({ type: "LOGOUT" });
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="user-info">
          <span className="user-name">{user.name}</span>
        </div>
        <div className="sidebar-header-actions">
          <button
            type="button"
            className="logout-btn"
            onClick={handleLogout}
            title="Sign out and log in as someone else"
          >
            Log out
          </button>
          <button className="create-room-btn" onClick={() => setShowCreate(true)} title="Create room">
            +
          </button>
        </div>
      </div>

      <div className="search-bar">
        <input
          type="text"
          placeholder="Search rooms..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <ul className="room-list">
        {filtered.map((room) => (
          <li
            key={room.id}
            className={activeRoom?.id === room.id ? "active" : ""}
            onClick={() => handleRoomClick(room)}
          >
            <span className="room-name">{room.name}</span>
            <span className="room-meta">{badgeFor(room.membership)}</span>
          </li>
        ))}
        {filtered.length === 0 && (
          <li className="empty-rooms">No rooms found</li>
        )}
      </ul>

      {joinTarget && (
        <JoinModal
          room={joinTarget}
          onClose={() => setJoinTarget(null)}
          onJoined={() => {
            setJoinTarget(null);
            loadRooms();
          }}
        />
      )}

      {showCreate && (
        <CreateRoomModal
          onClose={() => setShowCreate(false)}
          onCreated={() => {
            setShowCreate(false);
            loadRooms();
          }}
        />
      )}
    </aside>
  );
}
