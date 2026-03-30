/*
 * Authentication screen that handles login and account creation workflows.
 *
 * This component toggles between login and signup forms, validates required
 * fields, calls backend auth endpoints, surfaces errors, and stores the
 * authenticated user in global chat context on success.
 */
import { useState } from "react";
import { useChat } from "../context/ChatContext";
import { api } from "../hooks/useApi";
import "../styles/Login.css";

export default function LoginScreen() {
  /* Renders login/signup forms and coordinates authentication actions. */
  const { dispatch } = useChat();
  const [mode, setMode] = useState("login"); // "login" | "signup"

  // Shared
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Signup only
  const [name, setName] = useState("");
  const [mobile, setMobile] = useState("");

  const switchMode = () => {
    /* Toggles between login and signup mode while clearing stale errors. */
    setMode(mode === "login" ? "signup" : "login");
    setError("");
  };

  const handleLogin = async (e) => {
    /* Submits login credentials and stores the returned user on success. */
    e.preventDefault();
    setError("");
    if (!email.trim() || !password) {
      setError("Email and password are required");
      return;
    }

    setLoading(true);
    try {
      const user = await api("/users/login", {
        method: "POST",
        body: JSON.stringify({ email: email.trim(), password }),
      });
      dispatch({ type: "SET_USER", payload: user });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async (e) => {
    /* Submits account registration data and signs in the new user. */
    e.preventDefault();
    setError("");
    if (!name.trim() || !email.trim() || !password || !mobile.trim()) {
      setError("All fields are required");
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }

    setLoading(true);
    try {
      const user = await api("/users/signup", {
        method: "POST",
        body: JSON.stringify({
          name: name.trim(),
          email: email.trim(),
          password,
          mobile: mobile.trim(),
        }),
      });
      dispatch({ type: "SET_USER", payload: user });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (mode === "signup") {
    return (
      <div className="login-screen">
        <form className="login-card" onSubmit={handleSignup}>
          <h1>Chat Rooms</h1>
          <p className="subtitle">Create a new account</p>
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
          <input
            type="tel"
            placeholder="Mobile number"
            value={mobile}
            onChange={(e) => setMobile(e.target.value)}
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <button type="submit" disabled={loading}>
            {loading ? "Creating account..." : "Sign Up"}
          </button>
          {error && <p className="error">{error}</p>}
          <p className="switch-mode">
            Already have an account?{" "}
            <button type="button" className="link-btn" onClick={switchMode}>
              Log in
            </button>
          </p>
        </form>
      </div>
    );
  }

  return (
    <div className="login-screen">
      <form className="login-card" onSubmit={handleLogin}>
        <h1>Chat Rooms</h1>
        <p className="subtitle">Log in to your account</p>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <button type="submit" disabled={loading}>
          {loading ? "Logging in..." : "Log In"}
        </button>
        {error && <p className="error">{error}</p>}
        <p className="switch-mode">
          Don't have an account?{" "}
          <button type="button" className="link-btn" onClick={switchMode}>
            Sign up
          </button>
        </p>
      </form>
    </div>
  );
}
