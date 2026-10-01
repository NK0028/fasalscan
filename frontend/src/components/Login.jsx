import { useEffect, useState } from "react";
import { api } from "../api.js";

const DEMO = { email: "demo@fasalscan.app", password: "demo1234" };

export default function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [server, setServer] = useState("checking"); // checking | ready | waking | down

  // Free hosting sleeps when idle; ping early so it's awake by the time they log in.
  useEffect(() => {
    let cancelled = false;
    const slow = setTimeout(() => !cancelled && setServer((s) => (s === "checking" ? "waking" : s)), 2500);
    api("/api/health", { timeoutMs: 90000 })
      .then(() => !cancelled && setServer("ready"))
      .catch(() => !cancelled && setServer("down"));
    return () => {
      cancelled = true;
      clearTimeout(slow);
    };
  }, []);

  async function submit(creds) {
    setBusy(true);
    setError("");
    try {
      const res = await api("/api/auth/login", { method: "POST", json: creds, timeoutMs: 90000 });
      onLogin(res.user, res.access_token);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-wrap">
      <div className="login-card">
        <div className="login-head">
          <img src="/icon.svg" alt="" width="44" height="44" />
          <h1>FasalScan</h1>
          <p>One photo of a crate. Grade, damage and how many days it has left.</p>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            submit({ email, password });
          }}
        >
          <label>
            Email
            <input type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </label>
          <label>
            Password
            <input type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </label>
          {error && <p className="error">{error}</p>}
          <button className="btn primary" type="submit" disabled={busy}>
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <div className="demo-box">
          <div>
            <strong>Demo account</strong>
            <span>{DEMO.email} · {DEMO.password}</span>
          </div>
          <button
            className="btn ghost"
            type="button"
            disabled={busy}
            onClick={() => {
              setEmail(DEMO.email);
              setPassword(DEMO.password);
              submit(DEMO);
            }}
          >
            Use demo
          </button>
        </div>

        <p className={`server-status ${server}`}>
          {server === "checking" && "Connecting to server…"}
          {server === "waking" && "Server is waking up (free hosting), this can take up to a minute…"}
          {server === "ready" && "Server ready"}
          {server === "down" && "Server not responding. Refresh in a moment."}
        </p>
      </div>
    </div>
  );
}
