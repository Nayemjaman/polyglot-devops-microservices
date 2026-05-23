"use client";

import Link from "next/link";
import { ArrowLeft, CreditCard, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { SessionGate } from "@/components/auth/session-gate";
import { Button } from "@/components/ui/button";
import { Notice, Panel } from "@/components/ui/panel";
import { financeApi, type PaymentMethod } from "@/lib/finance-api";

export function PaymentMethodDetailsScreen({ id }: { id: string }) {
  return (
    <SessionGate>
      {() => <PaymentMethodDetails id={id} />}
    </SessionGate>
  );
}

function PaymentMethodDetails({ id }: { id: string }) {
  const [method, setMethod] = useState<PaymentMethod | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await financeApi.paymentMethods.get(id);
      setMethod(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load payment method");
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <main className="aurora-surface min-h-screen px-4 py-6 sm:px-6">
      <div className="mx-auto grid max-w-4xl gap-5">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <Link href="/dashboard">
            <Button type="button" variant="secondary">
              <ArrowLeft size={17} />
              Back
            </Button>
          </Link>
          <Button type="button" variant="secondary" onClick={load} disabled={isLoading}>
            <RefreshCw size={17} />
            Refresh
          </Button>
        </div>

        {error ? <Notice tone="error">{error}</Notice> : null}

        <Panel title="Payment method details" description="Review this payment method record and its current status.">
          {isLoading ? (
            <div className="rounded-md border border-dashed bg-slate-50 p-8 text-center text-sm text-muted-foreground">Loading payment method...</div>
          ) : method ? (
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-lg border bg-slate-950 p-5 text-white sm:col-span-2">
                <div className="flex items-center gap-3">
                  <div className="grid h-12 w-12 place-items-center rounded-md bg-white text-slate-950">
                    <CreditCard size={24} />
                  </div>
                  <div>
                    <h1 className="text-2xl font-black">{method.name}</h1>
                    <p className="text-sm text-white/62">{method.type}</p>
                  </div>
                </div>
              </div>
              <Detail label="ID" value={method.id} />
              <Detail label="Status" value={method.is_active ? "Active" : "Inactive"} />
              <Detail label="Name" value={method.name} />
              <Detail label="Type" value={method.type} />
            </div>
          ) : (
            <div className="rounded-md border border-dashed bg-slate-50 p-8 text-center text-sm text-muted-foreground">Payment method not found.</div>
          )}
        </Panel>
      </div>
    </main>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border bg-white p-4">
      <p className="text-xs font-bold uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-2 break-all text-sm font-semibold">{value}</p>
    </div>
  );
}
