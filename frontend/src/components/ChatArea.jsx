import { useEffect, useRef, useState, useCallback } from "react";
import { useChat } from "../context/ChatContext";
import { API_BASE } from "../config.js";
import { api, uploadFile } from "../hooks/useApi";
import { useWebSocket } from "../hooks/useWebSocket";
import MembersPanel from "./MembersPanel";
import "../styles/Chat.css";

export default function ChatArea() {
  const { state, dispatch } = useChat();
  const { activeRoom, messages, user, onlineUsers, typingUsers, replyingTo } = state;
  const { connect, disconnect, send } = useWebSocket();
  const messagesEndRef = useRef(null);
  const messageInputRef = useRef(null);
  const fileInputRef = useRef(null);
  const [text, setText] = useState("");
  const [showMembers, setShowMembers] = useState(false);
  const [wsTypingInDebug, setWsTypingInDebug] = useState("idle");
  const [lastTypingUser, setLastTypingUser] = useState(null);
  const typingTimerRef = useRef(null);
  const typingHeartbeatRef = useRef(0);
  const isTypingRef = useRef(false);

  // Connect WS when active room changes
  useEffect(() => {
    if (activeRoom && user) {
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

  useEffect(() => {
    const onWsDebug = (event) => {
      const d = event.detail || {};
      if (!d.type || (d.type !== "typing" && d.type !== "stop_typing")) return;
      const when = new Date(d.at || Date.now()).toLocaleTimeString();
      const who = d.user ? ` (${d.user})` : "";
      const rs = d.readyState != null ? ` rs=${d.readyState}` : "";
      const line = `${d.direction}:${d.type}${who}${rs} @ ${when}`;
      if (d.direction === "in") {
        if (d.user) setLastTypingUser(d.user);
        setWsTypingInDebug(line);
      }
    };
    window.addEventListener("chat-ws-debug", onWsDebug);
    return () => window.removeEventListener("chat-ws-debug", onWsDebug);
  }, []);

  // Typing events
  const handleInputChange = (e) => {
    setText(e.target.value);
    const now = Date.now();
    if (!isTypingRef.current || now - typingHeartbeatRef.current > 900) {
      isTypingRef.current = true;
      typingHeartbeatRef.current = now;
      send({ type: "typing" });
    }
    clearTimeout(typingTimerRef.current);
    typingTimerRef.current = setTimeout(() => {
      isTypingRef.current = false;
      typingHeartbeatRef.current = 0;
      send({ type: "stop_typing" });
    }, 10000);
  };

  const handleSend = () => {
    if (!text.trim()) return;
    const payload = { type: "message", content: text.trim() };
    if (replyingTo) {
      payload.reply_to = replyingTo.id;
    }
    send(payload);
    setText("");
    dispatch({ type: "CLEAR_REPLYING_TO" });
    if (isTypingRef.current) {
      isTypingRef.current = false;
      typingHeartbeatRef.current = 0;
      clearTimeout(typingTimerRef.current);
      send({ type: "stop_typing" });
    }
  };

  const handleInputBlur = () => {
    if (isTypingRef.current) {
      isTypingRef.current = false;
      typingHeartbeatRef.current = 0;
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

  const handleDeleteMessage = useCallback(
    async (messageId) => {
      if (!activeRoom || !user) return;
      if (!window.confirm("Delete this message for everyone in the room?")) return;
      try {
        await api(
          `/rooms/${activeRoom.id}/messages/${messageId}?admin_id=${user.id}`,
          { method: "DELETE" }
        );
        dispatch({ type: "REMOVE_MESSAGE", payload: messageId });
      } catch (err) {
        alert(err.message);
      }
    },
    [activeRoom?.id, user, dispatch]
  );

  const handleReply = useCallback(
    (msg) => {
      dispatch({
        type: "SET_REPLYING_TO",
        payload: {
          id: msg.id,
          sender_name: msg.sender_name || `User ${msg.sender_id}`,
          content: msg.type === "file" ? (msg.filename || "Attachment") : msg.content,
        },
      });
      messageInputRef.current?.focus();
    },
    [dispatch]
  );

  const scrollToMessage = useCallback((messageId) => {
    const el = document.getElementById(`msg-${messageId}`);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
      el.classList.add("msg-highlight");
      setTimeout(() => el.classList.remove("msg-highlight"), 1500);
    }
  }, []);

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
  const isAdmin = activeRoom.role === "admin";
  const typingNames = Object.keys(typingUsers);
  const typingDebugText = typingNames.length ? typingNames.join(", ") : (lastTypingUser || "none");
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
        <div className="typing-debug-panel">
          <div>self user: {user?.name || user?.id || "unknown"}</div>
          <div>typingUsers: {typingDebugText}</div>
          <div>ws IN: {wsTypingInDebug}</div>
        </div>

        {/* Header */}
        <div className="chat-header">
          <button
            type="button"
            className="chat-back-btn"
            title="Back to rooms"
            aria-label="Back to rooms"
            onClick={() => dispatch({ type: "SET_ACTIVE_ROOM", payload: null })}
          >
            ←
          </button>
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

        {/* Messages */}
        <div className="messages-container">
          {messages.map((msg, i) => (
            <MessageBubble
              key={msg.id || `sys-${i}`}
              msg={msg}
              userId={user.id}
              isAdmin={isAdmin}
              canWrite={canWrite}
              onDelete={handleDeleteMessage}
              onReply={handleReply}
              onClickReply={scrollToMessage}
            />
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Typing indicator — shown to all users regardless of role */}
        {typingLabel && (
          <div className="typing-indicator">
            <span className="typing-dots">
              <span /><span /><span />
            </span>
            {typingLabel}
          </div>
        )}

        {/* Compose or read-only */}
        {canWrite ? (
          <div className="compose-section">
            {/* Reply preview banner */}
            {replyingTo && (
              <div className="reply-banner">
                <div className="reply-banner-content">
                  <span className="reply-banner-name">{replyingTo.sender_name}</span>
                  <span className="reply-banner-text">{replyingTo.content}</span>
                </div>
                <button
                  type="button"
                  className="reply-banner-close"
                  onClick={() => dispatch({ type: "CLEAR_REPLYING_TO" })}
                >
                  ×
                </button>
              </div>
            )}
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
                ref={messageInputRef}
                type="text"
                className="message-input"
                placeholder={replyingTo ? "Type your reply..." : "Type a message..."}
                value={text}
                onChange={handleInputChange}
                onBlur={handleInputBlur}
                onKeyDown={handleKeyDown}
              />
              <button className="send-btn" onClick={handleSend}>
                Send
              </button>
            </div>
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
function MessageBubble({ msg, userId, isAdmin, canWrite, onDelete, onReply, onClickReply }) {
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
    <div id={`msg-${msg.id}`} className={`msg ${isMe ? "msg-out" : "msg-in"}`}>
      <div className="msg-body-row">
        <div className="msg-main">
          {!isMe && (
            <div className="sender">
              {msg.sender_name || `User ${msg.sender_id}`}
            </div>
          )}

          {/* Quoted reply block */}
          {msg.reply_snippet && (
            <div
              className="msg-reply-quote"
              onClick={() => onClickReply(msg.reply_snippet.id)}
            >
              <span className="reply-quote-name">{msg.reply_snippet.sender_name}</span>
              <span className="reply-quote-text">{msg.reply_snippet.content}</span>
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

        {/* Action icons */}
        {msg.id != null && (
          <div className="msg-actions">
            {canWrite && (
              <button
                type="button"
                className="msg-action-btn"
                title="Reply"
                aria-label="Reply"
                onClick={() => onReply(msg)}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="9 17 4 12 9 7" />
                  <path d="M20 18v-2a4 4 0 00-4-4H4" />
                </svg>
              </button>
            )}
            {isAdmin && (
              <button
                type="button"
                className="msg-action-btn msg-action-delete"
                title="Delete message"
                aria-label="Delete message"
                onClick={() => onDelete(msg.id)}
              >
                ×
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
