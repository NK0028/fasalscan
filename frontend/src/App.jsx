import { useEffect, useState } from "react";
import { api, tokenStore } from "./api.js";
import Login from "./components/Login.jsx";
import Scan from "./components/Scan.jsx";
import History from "./components/History.jsx";
import Ask from "./components/Ask.jsx";
import { t, RTL_LANGS } from "./i18n.js";

const LANGS = [
  { code: "en", label: "English" },
  { code: "ur", label: "اردو" },
  { code: "ps", label: "پښتو" },
];

const TABS = ["scan", "history", "ask"];

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

  const s = t(lang);
  const rtl = RTL_LANGS.has(lang);
  const dir = rtl ? "rtl" : "ltr";

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
            aria-label={s.langSelect}
          >
            {LANGS.map((l) => (
              <option key={l.code} value={l.code}>{l.label}</option>
            ))}
          </select>
          <button className="link-btn" onClick={logout} dir={dir}>{s.logout}</button>
        </div>
      </header>

      <nav className="tabs" role="tablist" dir={dir}>
        {TABS.map((id) => (
          <button
            key={id}
            role="tab"
            aria-selected={tab === id}
            className={tab === id ? "tab active" : "tab"}
            onClick={() => setTab(id)}
          >
            {s.tabs[id]}
          </button>
        ))}
      </nav>

      <main className="content" dir={dir}>
        {tab === "scan" && <Scan lang={lang} onScanned={setLastScan} lastScan={lastScan} user={user} />}
        {tab === "history" && <History lang={lang} />}
        {tab === "ask" && <Ask lang={lang} lastScan={lastScan} />}
      </main>

      <footer className={`foot ${rtl ? "rtl" : ""}`} dir={dir} lang={lang}>
        {s.footer}
      </footer>
    </div>
  );
}
