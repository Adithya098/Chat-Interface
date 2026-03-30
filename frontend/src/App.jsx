import { useCallback } from "react";
import { ChatProvider, useChat } from "./context/ChatContext";
import LoginScreen from "./components/LoginScreen";
import Sidebar from "./components/Sidebar";
import ChatArea from "./components/ChatArea";
import KickedBanner from "./components/KickedBanner";
import ConfirmDialog from "./components/ConfirmDialog";
import "./App.css";

function AppInner() {
  const { state, dispatch } = useChat();

  const handleEnterRoom = useCallback(
    (room, role) => {
      dispatch({
        type: "SET_ACTIVE_ROOM",
        payload: { id: room.id, name: room.name, role },
      });
    },
    [dispatch]
  );

  if (!state.user) {
    return <LoginScreen />;
  }

  const layoutClass =
    state.activeRoom != null ? "app-layout chat-open" : "app-layout";

  return (
    <div className={layoutClass}>
      <KickedBanner />
      <ConfirmDialog />
      <Sidebar onEnterRoom={handleEnterRoom} />
      <ChatArea />
    </div>
  );
}

export default function App() {
  return (
    <ChatProvider>
      <AppInner />
    </ChatProvider>
  );
}
