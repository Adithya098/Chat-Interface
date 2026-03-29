import { useEffect, useRef, useState, useCallback } from "react";
import { useChat } from "../context/ChatContext";
import { API_BASE } from "../config.js";
import { api, uploadFile } from "../hooks/useApi";
import { useWebSocket } from "../hooks/useWebSocket";
import MembersPanel from "./MembersPanel";
import "../styles/Chat.css";

export default function ChatArea() {
  const { state, dispatch } = useChat();
  const { activeRoom, messages, user, onlineUsers, typingUsers } = state;
  const { connect, disconnect, send } = useWebSocket();
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const [text, setText] = useState("");
  const [showMembers, setShowMembers] = useState(false);
  const typingTimerRef = useRef(null);
  const isTypingRef = useRef(false);

  // Connect WS when active room changes
  useEffect(() => {
    if (activeRoom && user) {
      // Load message history
      api(`/rooms/${activeRoom.id}/messages/?limit=100`)
        .then((msgs) => dispatch({ type: "SET_MESSAGES", payload: msgs }))
        .catch(console.error);

      connect(activeRoom.id, user.id);
      return () => disconnect();
    }
  }, [activeRoom?.id, user?.id]);

  // Auto-scroll on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Typing events
  const handleInputChange = (e) => {
    setText(e.target.value);
    if (!isTypingRef.current) {
      isTypingRef.current = true;
      send({ type: "typing" });
    }
    clearTimeout(typingTimerRef.current);
    typingTimerRef.current = setTimeout(() => {
      isTypingRef.current = false;
      send({ type: "stop_typing" });
    }, 2000);
  };

  const handleSend = () => {
    if (!text.trim()) return;
    send({ type: "message", content: text.trim() });
    setText("");
    // Stop typing
    if (isTypingRef.current) {
      isTypingRef.current = false;
      clearTimeout(typingTimerRef.current);
      send({ type: "stop_typing" });
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file || !activeRoom) return;
    try {
      const data = await uploadFile(activeRoom.id, user.id, file);
      send({
        type: "file",
        message_id: data.message_id,
        file_url: data.file_url,
        filename: data.filename,
      });
    } catch (err) {
      alert("Upload failed: " + err.message);
    }
    e.target.value = "";
  };

  if (!activeRoom) {
    return (
      <main className="chat-area">
        <div className="empty-state">
          <p>Select a room to start chatting</p>
        </div>
      </main>
    );
  }

  const canWrite = activeRoom.role === "write" || activeRoom.role === "admin";
  const typingNames = Object.keys(typingUsers);
  const typingLabel =
    typingNames.length === 1
      ? `${typingNames[0]} is typing...`
      : typingNames.length === 2
      ? `${typingNames[0]} and ${typingNames[1]} are typing...`
      : typingNames.length > 2
      ? `${typingNames.length} people are typing...`
      : null;

  return (
    <main className="chat-area">
      <div className="chat-view">
        {/* Header */}
        <div className="chat-header">
          <h2>{activeRoom.name}</h2>
          <div className="chat-header-right">
            <span className={`badge badge-${activeRoom.role}`}>{activeRoom.role}</span>
            <span className="online-count">{onlineUsers.length} online</span>
            <button
              className="members-btn"
              onClick={() => setShowMembers((v) => !v)}
            >
              Members
            </button>
          </div>
        </div>

        {/* Typing indicator */}
        {typingLabel && (
          <div className="typing-indicator">{typingLabel}</div>
        )}

        {/* Messages */}
        <div className="messages-container">
          {messages.map((msg, i) => (
            <Message key={msg.id || `sys-${i}`} msg={msg} userId={user.id} />
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Compose or read-only */}
        {canWrite ? (
          <div className="compose-bar">
            <label className="file-label" title="Attach file">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48" />
              </svg>
              <input
                ref={fileInputRef}
                type="file"
                hidden
                onChange={handleFileUpload}
              />
            </label>
            <input
              type="text"
              className="message-input"
              placeholder="Type a message..."
              value={text}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
            />
            <button className="send-btn" onClick={handleSend}>
              Send
            </button>
          </div>
        ) : (
          <div className="readonly-banner">
            You have read-only access to this room
          </div>
        )}
      </div>

      {showMembers && (
        <MembersPanel onClose={() => setShowMembers(false)} />
      )}
    </main>
  );
}

/* ── Single message bubble ── */
function Message({ msg, userId }) {
  if (msg.type === "system") {
    return <div className="msg-system">{msg.content}</div>;
  }

  const isMe = msg.sender_id === userId;
  const time = msg.created_at
    ? new Date(msg.created_at).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      })
    : "";

  return (
    <div className={`msg ${isMe ? "msg-out" : "msg-in"}`}>
      {!isMe && (
        <div className="sender">
          {msg.sender_name || `User ${msg.sender_id}`}
        </div>
      )}
      {msg.type === "file" ? (
        <div className="text">
          <a
            className="file-link"
            href={`${API_BASE}${msg.content}?user_id=${userId}`}
            target="_blank"
            rel="noreferrer"
          >
            {msg.filename || "Attachment"}
          </a>
        </div>
      ) : (
        <div className="text">{msg.content}</div>
      )}
      <div className="meta">{time}</div>
    </div>
  );
}
