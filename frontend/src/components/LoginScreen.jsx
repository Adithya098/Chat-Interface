import { useState } from "react";
import { useChat } from "../context/ChatContext";
import { api } from "../hooks/useApi";
import "../styles/Login.css";

function isDuplicateEmailError(message) {
  const m = String(message || "").toLowerCase();
  return m.includes("already registered") || m.includes("email already");
}

export default function LoginScreen() {
  const { dispatch } = useChat();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (!name.trim() || !email.trim()) {
      setError("Name and email are required");
      return;
    }

    setLoading(true);
    try {
      let user;
      try {
        user = await api("/users/", {
          method: "POST",
          body: JSON.stringify({ name: name.trim(), email: email.trim() }),
        });
      } catch (e) {
        if (!isDuplicateEmailError(e.message)) throw e;
        const users = await api("/users/");
        user = users.find((u) => u.email === email.trim());
        if (!user) throw new Error("Could not find or create user");
      }
      dispatch({ type: "SET_USER", payload: user });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-screen">
      <form className="login-card" onSubmit={handleSubmit}>
        <h1>Chat Rooms</h1>
        <p className="subtitle">Sign in or create an account</p>
        <input
          type="text"
          placeholder="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <button type="submit" disabled={loading}>
          {loading ? "Loading..." : "Continue"}
        </button>
        {error && <p className="error">{error}</p>}
      </form>
    </div>
  );
}
