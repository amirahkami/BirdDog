"use client";

import { signOut } from "next-auth/react";

export function SignOutButton() {
  async function handleSignOut() {
    const response = await fetch("/api/logout", { cache: "no-store" });
    const payload = (await response.json()) as { logoutUrl?: string };
    await signOut({ redirect: false });
    window.location.assign(payload.logoutUrl ?? "/login");
  }

  return (
    <button className="link-button" onClick={handleSignOut} type="button">
      Sign out
    </button>
  );
}
