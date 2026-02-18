"use client";
import { useState } from "react";
import dynamic from "next/dynamic";
import { api } from "@/src/lib/api";
import { Input } from "@/src/components/ui/input";
import { Button } from "@/src/components/ui/button";
import { Card } from "@/src/components/ui/card";
import { toast } from "sonner";

const LockScheduleButton = dynamic(() => import("@/src/components/LockScheduleButton"), { ssr: false });

export default function ReportsPage() {
  const [contractId, setContractId] = useState("C-TEST");
  const [schedules, setSchedules] = useState<Record<string, any> | null>(null);
  const [allocResult, setAllocResult] = useState<any>(null);

  async function loadFromGrid() {
    try {
      const rows = await api(`/schedules/grid/${encodeURIComponent(contractId)}`);
      if (!rows.length) {
        toast.error("No schedule rows found for this contract");
        return;
      }
      // Convert grid rows into a schedule object { period: amount }
      const sched: Record<string, number> = {};
      for (const r of rows) {
        sched[r.period] = (sched[r.period] || 0) + r.amount;
      }
      setSchedules(sched);
      setAllocResult(null);
      toast.success(`Loaded ${rows.length} schedule rows`);
    } catch (e: any) {
      toast.error(e?.message || "Failed to load schedule");
    }
  }

  async function runAllocation() {
    try {
      const res = await api("/contracts/allocate", {
        method: "POST",
        body: JSON.stringify({
          contract_id: contractId,
          customer: "Demo",
          transaction_price: 50000,
          pos: [
            { po_id: "PO-1", description: "SaaS 12m", ssp: 20000, method: "straight_line", start_date: "2025-01-01", end_date: "2025-12-01" },
            { po_id: "PO-2", description: "Implementation", ssp: 30000, method: "point_in_time", start_date: "2025-01-01" },
          ],
        }),
      });
      setAllocResult(res);
      setSchedules(res.schedules);
      toast.success("Allocation complete");
    } catch (e: any) {
      toast.error(e?.message || "Allocation failed");
    }
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <h1 className="text-xl font-semibold">Reports & Schedule Lock</h1>

      <Card className="p-4 space-y-3">
        <h2 className="font-medium text-sm text-gray-700">Load Schedule Data</h2>
        <div className="flex gap-2 items-center">
          <Input className="max-w-xs" placeholder="Contract ID" value={contractId} onChange={(e: any) => setContractId(e.target.value)} />
          <Button onClick={loadFromGrid}>Load from Grid</Button>
          <Button onClick={runAllocation}>Run Demo Allocation</Button>
        </div>
      </Card>

      {schedules && (
        <>
          <Card className="p-0 overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="p-2 text-left">Period</th>
                  <th className="p-2 text-right">Amount</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(schedules).sort().map(([period, value]) => {
                  // value could be a number or nested object (from allocation)
                  const isNested = typeof value === "object";
                  if (isNested) {
                    return Object.entries(value as Record<string, number>).sort().map(([p, amt]) => (
                      <tr key={`${period}-${p}`} className="border-t">
                        <td className="p-2">{period} / {p}</td>
                        <td className="p-2 text-right">{Number(amt).toFixed(2)}</td>
                      </tr>
                    ));
                  }
                  return (
                    <tr key={period} className="border-t">
                      <td className="p-2">{period}</td>
                      <td className="p-2 text-right">{Number(value).toFixed(2)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Card>

          <Card className="p-4 space-y-3">
            <h2 className="font-medium text-sm text-gray-700">Lock This Schedule</h2>
            <p className="text-xs text-gray-500">
              Locking creates a tamper-proof hash of the schedule JSON. Once locked, any changes will produce a different hash.
            </p>
            <LockScheduleButton
              contractId={contractId || "C-TEST"}
              schedule={schedules}
              note="Month-end close"
            />
          </Card>
        </>
      )}

      {allocResult && (
        <Card className="p-4">
          <h2 className="font-medium text-sm text-gray-700 mb-2">Full Allocation Result</h2>
          <pre className="text-xs bg-slate-50 p-3 rounded border overflow-x-auto">{JSON.stringify(allocResult, null, 2)}</pre>
        </Card>
      )}
    </div>
  );
}
