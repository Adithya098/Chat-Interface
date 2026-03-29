import { createContext, useContext, useReducer, useCallback } from "react";

const ChatContext = createContext(null);

const initialState = {
  user: JSON.parse(localStorage.getItem("chat_user") || "null"),
  rooms: [],          // all rooms with membership info
  activeRoom: null,   // { id, name, role, status }
  messages: [],
  onlineUsers: [],
  typingUsers: {},    // { userName: timeoutId }
};

function reducer(state, action) {
  switch (action.type) {
    case "SET_USER":
      localStorage.setItem("chat_user", JSON.stringify(action.payload));
      return { ...state, user: action.payload };

    case "LOGOUT":
      localStorage.removeItem("chat_user");
      return { ...initialState, user: null };

    case "SET_ROOMS":
      return { ...state, rooms: action.payload };

    case "SET_ACTIVE_ROOM":
      return { ...state, activeRoom: action.payload, messages: [], onlineUsers: [], typingUsers: {} };

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
  const [state, dispatch] = useReducer(reducer, initialState);
  return (
    <ChatContext.Provider value={{ state, dispatch }}>
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error("useChat must be inside ChatProvider");
  return ctx;
}
