/*
 * Shared React context and reducer for application-wide chat state.
 *
 * This file centralizes user session persistence, room selection, message
 * timeline updates, typing indicators, reply state, and online-user presence
 * so all chat UI components can read and dispatch consistent state changes.
 */
import { createContext, useContext, useReducer } from "react";

const ChatContext = createContext(null);

function loadStoredUser() {
  /* Restores the last signed-in user from localStorage when available. */
  try {
    const raw = localStorage.getItem("chat_user");
    if (raw == null || raw === "") return null;
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" ? parsed : null;
  } catch {
    return null;
  }
}

function getInitialState() {
  /* Creates the default state object used to initialize the chat reducer. */
  return {
    user: loadStoredUser(),
    rooms: [],
    activeRoom: null,
    messages: [],
    onlineUsers: [],
    typingUsers: {},
    replyingTo: null,
  };
}

function reducer(state, action) {
  /* Applies chat state transitions for auth, room, message, and typing actions. */
  switch (action.type) {
    case "SET_USER":
      localStorage.setItem("chat_user", JSON.stringify(action.payload));
      return { ...state, user: action.payload };

    case "LOGOUT":
      localStorage.removeItem("chat_user");
      return { ...getInitialState(), user: null };

    case "SET_ROOMS":
      return { ...state, rooms: action.payload };

    case "SET_ACTIVE_ROOM":
      return { ...state, activeRoom: action.payload, messages: [], onlineUsers: [], typingUsers: {}, replyingTo: null };

    case "SET_MESSAGES":
      return { ...state, messages: action.payload };

    case "ADD_MESSAGE":
      return { ...state, messages: [...state.messages, action.payload] };

    case "REMOVE_MESSAGE":
      return {
        ...state,
        messages: state.messages.filter(
          (m) => m.id == null || Number(m.id) !== Number(action.payload)
        ),
      };

    case "SET_REPLYING_TO":
      return { ...state, replyingTo: action.payload };

    case "CLEAR_REPLYING_TO":
      return { ...state, replyingTo: null };

    case "SET_ONLINE_USERS":
      return { ...state, onlineUsers: action.payload };

    case "ADD_TYPING": {
      const name = action.payload;
      return { ...state, typingUsers: { ...state.typingUsers, [name]: true } };
    }

    case "REMOVE_TYPING": {
      const { [action.payload]: _, ...rest } = state.typingUsers;
      return { ...state, typingUsers: rest };
    }

    default:
      return state;
  }
}

export function ChatProvider({ children }) {
  /* Provides reducer-driven chat state and dispatch to descendant components. */
  const [state, dispatch] = useReducer(reducer, undefined, getInitialState);
  return (
    <ChatContext.Provider value={{ state, dispatch }}>
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  /* Returns chat context and guards against usage outside the provider tree. */
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error("useChat must be inside ChatProvider");
  return ctx;
}
