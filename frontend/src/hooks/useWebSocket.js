import { useEffect, useRef, useCallback } from "react";
import { useChat } from "../context/ChatContext";
import { wsUrl } from "../config.js";

export function useWebSocket() {
  const { dispatch } = useChat();
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);
  const skipReconnectRef = useRef(false);
  const typingTimers = useRef({});

  const connect = useCallback((roomId, userId) => {
    // Clean up previous
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    clearTimeout(reconnectTimer.current);
    skipReconnectRef.current = false;

    const url = wsUrl(`/ws/${roomId}?user_id=${userId}`);

    const socket = new WebSocket(url);
    wsRef.current = socket;

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case "message":
          dispatch({
            type: "ADD_MESSAGE",
            payload: {
              id: data.id,
              sender_id: data.sender_id,
              sender_name: data.sender_name,
              type: "text",
              content: data.content,
              created_at: data.created_at,
              reply_to: data.reply_to || null,
              reply_snippet: data.reply_snippet || null,
            },
          });
          break;

        case "file":
          dispatch({
            type: "ADD_MESSAGE",
            payload: {
              id: data.id,
              sender_id: data.sender_id,
              sender_name: data.sender_name,
              type: "file",
              content: data.file_url,
              filename: data.filename,
              created_at: new Date().toISOString(),
            },
          });
          break;

        case "typing":
          window.dispatchEvent(
            new CustomEvent("chat-ws-debug", {
              detail: { direction: "in", type: "typing", user: data.user_name, at: Date.now() },
            })
          );
          console.log("[WS] typing received from", data.user_name);
          dispatch({ type: "ADD_TYPING", payload: data.user_name });
          // Keep indicator visible long enough to be noticeable on receiver
          clearTimeout(typingTimers.current[data.user_name]);
          typingTimers.current[data.user_name] = setTimeout(() => {
            dispatch({ type: "REMOVE_TYPING", payload: data.user_name });
            delete typingTimers.current[data.user_name];
          }, 10000);
          break;

        case "stop_typing":
          window.dispatchEvent(
            new CustomEvent("chat-ws-debug", {
              detail: { direction: "in", type: "stop_typing", user: data.user_name, at: Date.now() },
            })
          );
          // Don't remove immediately — keep visible for 3s so others can see it
          clearTimeout(typingTimers.current[data.user_name]);
          typingTimers.current[data.user_name] = setTimeout(() => {
            dispatch({ type: "REMOVE_TYPING", payload: data.user_name });
            delete typingTimers.current[data.user_name];
          }, 3000);
          break;

        case "system":
          dispatch({
            type: "ADD_MESSAGE",
            payload: { type: "system", content: data.content },
          });
          break;

        case "online_users":
          dispatch({ type: "SET_ONLINE_USERS", payload: data.users });
          break;

        case "error":
          dispatch({
            type: "ADD_MESSAGE",
            payload: { type: "system", content: `Error: ${data.content}` },
          });
          break;

        case "message_deleted":
          if (data.message_id != null) {
            dispatch({ type: "REMOVE_MESSAGE", payload: data.message_id });
          }
          break;

        case "member_removed":
          window.dispatchEvent(new CustomEvent("chat-refresh-members"));
          break;

        case "kicked":
          skipReconnectRef.current = true;
          alert(data.content || "You were removed from this room");
          dispatch({ type: "SET_ACTIVE_ROOM", payload: null });
          dispatch({ type: "SET_MESSAGES", payload: [] });
          window.dispatchEvent(new CustomEvent("chat-refresh-rooms"));
          break;
      }
    };

    socket.onclose = () => {
      if (skipReconnectRef.current) return;
      // Auto-reconnect after 3s
      reconnectTimer.current = setTimeout(() => {
        if (wsRef.current === socket) {
          connect(roomId, userId);
        }
      }, 3000);
    };

    socket.onerror = (e) => console.error("WS error", e);
  }, [dispatch]);

  const disconnect = useCallback(() => {
    clearTimeout(reconnectTimer.current);
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const send = useCallback((data) => {
    if (data?.type === "typing" || data?.type === "stop_typing") {
      window.dispatchEvent(
        new CustomEvent("chat-ws-debug", {
          detail: { direction: "out", type: data.type, at: Date.now() },
        })
      );
    }
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    } else if (data?.type === "typing" || data?.type === "stop_typing") {
      window.dispatchEvent(
        new CustomEvent("chat-ws-debug", {
          detail: {
            direction: "drop",
            type: data.type,
            at: Date.now(),
            readyState: wsRef.current?.readyState ?? -1,
          },
        })
      );
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => disconnect();
  }, [disconnect]);

  return { connect, disconnect, send };
}
