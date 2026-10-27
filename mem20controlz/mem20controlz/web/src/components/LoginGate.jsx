import React, { useRef, useState } from "react";
import { login as apiLogin } from "../auth.js";
import FocusTrap from "./FocusTrap.jsx";

// Shown whenever the API answers 401. Explains the two ways in, because a user
// behind Cloudflare Access will never see a password prompt work - Access has
// already admitted them, or it has not admitted anyone.
export default function LoginGate({ status, onAuthenticated }) {
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const inputRef = useRef(null);

  const viaAccess = status && status.trust_cf_access;
  const passwordAvailable = !status || status.password_configured;

  async function submit(event) {
    event.preventDefault();
    if (!password) return;
    setBusy(true);
    setError(null);
    try {
      await apiLogin(password);
      setPassword("");
      onAuthenticated();
    } catch (err) {
      setError(err && err.message ? err.message : "login failed");
    } finally {
      setBusy(false);
    }
  }

  // The gate is the only thing on screen, so it is a real modal dialog rather than a
  // region: focus goes to the password field on mount (not to <body>), Tab stays
  // inside the card, and the error paragraph is announced by role="alert" below.
  return (
    <FocusTrap
      className="login-gate"
      role="dialog"
      labelledBy="login-title"
      describedBy="login-sub"
      initialFocus={inputRef.current}
    >
      <form className="login-card" onSubmit={submit}>
        <h1 className="login-title" id="login-title">mem20 control plane</h1>
        <p className="login-sub" id="login-sub">
          This panel is restricted. Sign in to continue.
        </p>

        {status && !passwordAvailable && !viaAccess ? (
          <p className="login-error">
            No admin password is configured on the server, so password sign-in is
            disabled. Set <code>MEM20_CONTROL_PASSWORD</code> in the estate secrets
            file, or reach this through Cloudflare Access.
          </p>
        ) : null}

        {status && status.secret_configured === false ? (
          <p className="login-error">
            No session secret is configured, so a session cannot be signed. Set{" "}
            <code>MEM20_CONTROL_SECRET</code> in the estate secrets file.
          </p>
        ) : null}

        <label className="login-label" htmlFor="login-password">
          Admin password
        </label>
        <input
          id="login-password"
          ref={inputRef}
          className="login-input"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={busy || !passwordAvailable}
          aria-invalid={error ? "true" : undefined}
          aria-describedby={error ? "login-error" : undefined}
        />

        {error ? (
          <p className="login-error" id="login-error" role="alert">
            {error}
          </p>
        ) : null}

        <button
          className="login-submit"
          type="submit"
          disabled={busy || !password || !passwordAvailable}
        >
          {busy ? "signing in…" : "Sign in"}
        </button>

        {viaAccess ? (
          <p className="login-hint">
            This control plane trusts Cloudflare Access. If you reached it through
            Access you should already be admitted — reload after signing in to your
            Access account.
          </p>
        ) : null}
      </form>
    </FocusTrap>
  );
}
