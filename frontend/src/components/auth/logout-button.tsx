"use client";

import { useRouter } from "next/navigation";
import { LogOut } from "lucide-react";
import { logout } from "@/lib/auth-api";
import { clearSession, getRefreshToken } from "@/lib/auth";
import { Button } from "@/components/ui/button";

export function LogoutButton() {
  const router = useRouter();

  async function handleLogout() {
    const refresh = getRefreshToken();
    try {
      if (refresh) {
        await logout(refresh);
      }
    } finally {
      clearSession();
      router.push("/login");
    }
  }

  return (
    <Button type="button" variant="secondary" onClick={handleLogout}>
      <LogOut size={17} />
      Sign out
    </Button>
  );
}
