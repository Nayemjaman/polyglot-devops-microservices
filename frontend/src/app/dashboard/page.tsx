"use client";

import { SessionGate } from "@/components/auth/session-gate";
import { FinanceWorkspace } from "@/components/dashboard/finance-workspace";

export default function DashboardPage() {
  return (
    <SessionGate>
      {(user) => <FinanceWorkspace user={user} />}
    </SessionGate>
  );
}
