"use client";

import Link from "next/link";
import { useSession, signOut } from "next-auth/react";
import { BookOpenText, LogOut } from "lucide-react";

export default function Navbar() {
  const { data: session } = useSession();

  return (
    <header className="border-b border-surface-border bg-paper/80 backdrop-blur sticky top-0 z-10">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <BookOpenText size={20} className="text-accent-deep" />
          <span className="font-display text-lg font-semibold tracking-tight">Archive</span>
        </Link>

        {session ? (
          <div className="flex items-center gap-4">
            <span className="text-sm text-ink/60">{session.user?.email}</span>
            <button
              onClick={() => signOut({ callbackUrl: "/" })}
              className="flex items-center gap-1.5 text-sm font-medium text-ink/70 hover:text-ink transition-colors"
            >
              <LogOut size={15} />
              Sign out
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-3">
            <Link href="/login" className="text-sm font-medium text-ink/70 hover:text-ink transition-colors">
              Sign in
            </Link>
            <Link
              href="/register"
              className="text-sm font-medium bg-ink text-paper px-4 py-2 rounded-full hover:bg-ink/85 transition-colors"
            >
              Get started
            </Link>
          </div>
        )}
      </div>
    </header>
  );
}
