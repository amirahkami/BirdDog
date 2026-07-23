"use client";

import { signIn } from "next-auth/react";
import { useEffect, useState } from "react";

export default function LoginPage() {
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    void signIn("keycloak", { callbackUrl: "/" }).catch(() => setFailed(true));
  }, []);

  return (
    <main className="login-shell">
      <section className="login-card" aria-live="polite">
        <p className="eyebrow">BirdDog secure access</p>
        <h1>Opening login…</h1>
        <p>{failed ? "Login is temporarily unavailable." : "Redirecting to Keycloak."}</p>
        {failed ? <button onClick={() => signIn("keycloak", { callbackUrl: "/" })}>Retry</button> : null}
      </section>
    </main>
  );
}
