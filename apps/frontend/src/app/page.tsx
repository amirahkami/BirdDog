import Link from "next/link";
import { getServerSession } from "next-auth";
import { redirect } from "next/navigation";

import { authOptions } from "@/lib/auth";

import { SignOutButton } from "./sign-out-button";

export const dynamic = "force-dynamic";

export default async function Home() {
  const session = await getServerSession(authOptions);
  if (!session) {
    redirect("/login");
  }

  const isAdmin = session.user.roles.includes("admin");

  return (
    <main>
      <nav className="topbar" aria-label="Account navigation">
        <strong>BirdDog</strong>
        <div>
          {isAdmin ? <Link href="/admin">Admin dashboard</Link> : null}
          <SignOutButton />
        </div>
      </nav>

      <section className="hero" aria-labelledby="page-title">
        <p className="eyebrow">Private workspace</p>
        <h1 id="page-title">The job search that reads before you apply.</h1>
        <p className="intro">
          Signed in as <strong>{session.user.username}</strong>. BirdDog will collect focused
          roles, remove the noise, and explain which opportunities fit your CV.
        </p>
      </section>
    </main>
  );
}
