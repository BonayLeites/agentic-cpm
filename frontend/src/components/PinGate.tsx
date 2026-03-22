import { useState, useEffect, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { API_BASE } from "../api/client";

const TOKEN_KEY = "demoToken";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

async function verifyToken(token: string): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/api/data/stats`, {
      headers: { "X-Demo-Token": token },
    });
    return res.ok;
  } catch {
    return false;
  }
}

export default function PinGate({ children }: { children: ReactNode }) {
  const { t } = useTranslation();
  const [authenticated, setAuthenticated] = useState(false);
  const [checking, setChecking] = useState(true);
  const [pin, setPin] = useState("");
  const [error, setError] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const saved = getToken();
    if (saved) {
      verifyToken(saved).then((ok) => {
        if (ok) setAuthenticated(true);
        else localStorage.removeItem(TOKEN_KEY);
        setChecking(false);
      });
    } else {
      setChecking(false);
    }
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!pin.trim()) return;
    setSubmitting(true);
    setError(false);
    const ok = await verifyToken(pin.trim());
    if (ok) {
      localStorage.setItem(TOKEN_KEY, pin.trim());
      setAuthenticated(true);
    } else {
      setError(true);
    }
    setSubmitting(false);
  }

  if (checking) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  if (authenticated) {
    return <>{children}</>;
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-sm rounded-xl bg-white p-8 shadow-lg">
        <div className="mb-6 text-center">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-blue-100">
            <svg className="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h1 className="text-lg font-semibold text-gray-900">{t("pin.title")}</h1>
          <p className="mt-1 text-sm text-gray-500">CPM Agent Accelerator</p>
        </div>

        <form onSubmit={handleSubmit}>
          <input
            type="text"
            value={pin}
            onChange={(e) => { setPin(e.target.value); setError(false); }}
            placeholder={t("pin.placeholder")}
            autoFocus
            className={`w-full rounded-lg border px-4 py-2.5 text-center text-sm tracking-widest outline-none transition-colors ${
              error
                ? "border-red-300 bg-red-50 text-red-900 focus:border-red-500"
                : "border-gray-200 bg-gray-50 text-gray-900 focus:border-blue-500"
            }`}
          />

          {error && (
            <p className="mt-2 text-center text-xs text-red-600">{t("pin.error")}</p>
          )}

          <button
            type="submit"
            disabled={submitting || !pin.trim()}
            className="mt-4 w-full rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
          >
            {submitting ? "..." : t("pin.submit")}
          </button>
        </form>
      </div>
    </div>
  );
}
