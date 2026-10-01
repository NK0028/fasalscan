import { useEffect, useState } from "react";
import { api, tokenStore } from "./api.js";
import Login from "./components/Login.jsx";
import Scan from "./components/Scan.jsx";
import History from "./components/History.jsx";
import Ask from "./components/Ask.jsx";

const LANGS = [
  { code: "en", label: "English" },
  { code: "ur", label: "اردو" },
  { code: "ps", label: "پښتو" },
];

const TABS = [
  { id: "scan", label: "Scan" },
  { id: "history", label: "History" },
  { id: "ask", label: "Ask" },
];

export default function App() {
  const [user, setUser] = useState(null);
  const [booting, setBooting] = useState(Boolean(tokenStore.get()));
  const [tab, setTab] = useState("scan");
  const [lang, setLang] = useState("en");
  const [lastScan, setLastScan] = useState(null);

  useEffect(() => {
    if (!tokenStore.get()) return;
    api("/api/auth/me")
      .then(setUser)
      .catch(() => tokenStore.clear())
      .finally(() => setBooting(false));
  }, []);

  function logout() {
    tokenStore.clear();
    setUser(null);
    setLastScan(null);
    setTab("scan");
  }

  if (booting) {
    return <div className="boot">Loading FasalScan…</div>;
  }

  if (!user) {
    return (
      <Login
        onLogin={(u, token) => {
          tokenStore.set(token);
          setUser(u);
        }}
      />
    );
  }

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          <img src="/icon.svg" alt="" width="28" height="28" />
          <span>FasalScan</span>
        </div>
        <div className="topbar-right">
          <select
            className="lang-select"
            value={lang}
            onChange={(e) => setLang(e.target.value)}
            aria-label="Answer language"
          >
            {LANGS.map((l) => (
              <option key={l.code} value={l.code}>{l.label}</option>
            ))}
          </select>
          <button className="link-btn" onClick={logout}>Log out</button>
        </div>
      </header>

      <nav className="tabs" role="tablist">
        {TABS.map((t) => (
          <button
            key={t.id}
            role="tab"
            aria-selected={tab === t.id}
            className={tab === t.id ? "tab active" : "tab"}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <main className="content">
        {tab === "scan" && <Scan lang={lang} onScanned={setLastScan} lastScan={lastScan} user={user} />}
        {tab === "history" && <History />}
        {tab === "ask" && <Ask lang={lang} lastScan={lastScan} />}
      </main>

      <footer className="foot">
        Estimates only. Built with YOLOv8, Whisper and Llama 3.3. MVP by Naeem Khan.
      </footer>
    </div>
  );
}
