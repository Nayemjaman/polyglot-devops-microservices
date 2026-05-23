"use client";

import { useEffect, useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { fetchMe, refreshSession } from "@/lib/auth-api";
import { clearSession, getRefreshToken, persistTokens, persistUser, type AuthUser } from "@/lib/auth";

type SessionGateProps = {
  children: (user: AuthUser) => ReactNode;
};

export function SessionGate({ children }: SessionGateProps) {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    async function loadSession() {
      try {
        const me = await fetchMe();
        if (!isMounted) {
          return;
        }
        persistUser(me.user);
        setUser(me.user);
      } catch {
        try {
          const refresh = getRefreshToken();
          const refreshed = await refreshSession(refresh);
          persistTokens(refreshed.tokens);
          const me = await fetchMe();
          if (!isMounted) {
            return;
          }
          persistUser(me.user);
          setUser(me.user);
        } catch {
          clearSession();
          router.replace("/login");
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadSession();

    return () => {
      isMounted = false;
    };
  }, [router]);

  if (isLoading) {
    return (
      <main className="grid min-h-screen place-items-center px-5">
        <div className="rounded-lg border bg-white px-5 py-4 text-sm font-semibold shadow-sm">
          Loading your workspace...
        </div>
      </main>
    );
  }

  if (!user) {
    return null;
  }

  return children(user);
}
