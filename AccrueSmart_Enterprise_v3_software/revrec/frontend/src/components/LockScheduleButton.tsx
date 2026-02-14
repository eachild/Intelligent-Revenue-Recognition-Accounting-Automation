"use client";
import { useState } from "react";
import { Button } from "@/src/components/ui/button";
import { toast } from "@/src/components/ui/toast";
import { api } from "@/src/lib/api";

type Props = {
  contractId: string;
  schedule: any;      // the exact JSON you want to lock (allocation/schedules)
  note?: string;
  className?: string;
};

export default function LockScheduleButton({ contractId, schedule, note, className }: Props) {
  const [loading, setLoading] = useState(false);
  const [locked, setLocked] = useState<any>(null);

  async function doLock() {
    setLoading(true);
    try {
      const res = await api("/locks/schedule", {
        method: "POST",
        body: JSON.stringify({ contract_id: contractId, schedule, note }),
      });
      setLocked(res.lock);
      toast({ title: "Schedule locked", description: `Hash: ${res.lock.hash.slice(0, 10)}…` });
    } catch (e: any) {
      toast({ title: "Lock failed", description: e?.message || "Unknown error" });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={className}>
      <Button onClick={doLock} disabled={loading}>
        {loading ? "Locking…" : "🔒 Lock Schedule"}
      </Button>
      {locked && (
        <div className="mt-2 text-xs text-gray-600">
          Locked by {locked.approver} at {new Date(locked.locked_at).toLocaleString()} <br />
          Hash: <span className="font-mono">{locked.hash}</span>
        </div>
      )}
    </div>
  );
}