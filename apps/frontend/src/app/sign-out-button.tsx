"use client";

import { signOut } from "next-auth/react";

import { Button } from "@/components/ui/button";

export function SignOutButton() {
  async function handleSignOut() {
    const response = await fetch("/api/logout", { cache: "no-store" });
    const payload = (await response.json()) as { logoutUrl?: string };
    await signOut({ redirect: false });
    window.location.assign(payload.logoutUrl ?? "/login");
  }

  return (
    <Button variant="ghost" size="sm" onClick={handleSignOut} type="button">
      Sign out
    </Button>
  );
}
