"use client";

import { useEffect, useState } from "react";

import type { AuthSession } from "@/lib/api";
import { getMe, login } from "@/lib/api";

const STORAGE_KEY = "investpro.auth";

export function AuthButtons() {
  const [session, setSession] = useState<AuthSession | null>(null);
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    const stored = JSON.parse(raw) as AuthSession;
    getMe(stored.token)
      .then((user) => setSession({ ...user, token: stored.token }))
      .catch(() => window.localStorage.removeItem(STORAGE_KEY));
  }, []);

  async function handleLogin() {
    setError(null);
    try {
      const next = await login(email, name || "Investor");
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      setSession(next);
      setEmail("");
      setName("");
    } catch (loginError) {
      setError(loginError instanceof Error ? loginError.message : "Sign in failed.");
    }
  }

  function handleLogout() {
    window.localStorage.removeItem(STORAGE_KEY);
    setSession(null);
  }

  if (session) {
    return (
      <div className="auth-box signed-in">
        <span>{session.name}</span>
        <button type="button" onClick={handleLogout}>Sign out</button>
      </div>
    );
  }

  return (
    <div className="auth-box">
      <input aria-label="Name" placeholder="Name" value={name} onChange={(event) => setName(event.target.value)} />
      <input aria-label="Email" placeholder="Email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} />
      <button type="button" onClick={handleLogin}>Sign in</button>
      {error ? <span>{error}</span> : null}
    </div>
  );
}
