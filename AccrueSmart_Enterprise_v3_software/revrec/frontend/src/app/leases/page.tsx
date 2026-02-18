"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { Button, Card, Textarea } from "@/components/ui";

type LeaseState = {
  lease_id: string;
  start_date: string;
  end_date: string;
  payment: number;
  frequency: string;
  discount_rate_annual: number;
  initial_direct_costs: number;
  incentives: number;
  cpi_escalation_pct: number;
  cpi_escalation_month: number;
};

export default function LeasePage() {
  const [lease, setLease] = useState<LeaseState>({
    lease_id: "L-1001",
    start_date: "2025-01-01",
    end_date: "2027-12-31",
    payment: 5000,
    frequency: "monthly",
    discount_rate_annual: 0.06,
    initial_direct_costs: 0,
    incentives: 0,
    cpi_escalation_pct: 0.03,
    cpi_escalation_month: 12,
  });

  const [schedule, setSchedule] = useState<any>(null);
  const [downloading, setDownloading] = useState(false);

  async function run() {
    const res = await api("/leases/schedule", {
      method: "POST",
      body: JSON.stringify(lease),
    });
    setSchedule(res);
  }

  async function downloadCSV() {
    setDownloading(true);
    try {
      const res = await api("/leases/export/journals", {
        method: "POST",
        body: JSON.stringify(lease),
      });

      const blob = new Blob([res.content], { type: "text/csv" });
      const url = URL.createObjectURL(blob);

      const a = document.createElement("a");
      a.href = url;
      a.download = res.filename || "lease_journals.csv";
      a.click();

      URL.revokeObjectURL(url);
    } finally {
      setDownloading(false);
    }
  }

  function setField(key: keyof LeaseState, raw: string) {
    const current = lease[key];
    const next =
      typeof current === "number" ? (raw === "" ? 0 : Number(raw)) : raw;

    setLease({ ...lease, [key]: next } as LeaseState);
  }

  return (
    <div className="max-w-6xl mx-auto space-y-4">
      <h1 className="text-xl font-semibold">Lease Schedule (ASC 842)</h1>

      <Card className="grid grid-cols-2 md:grid-cols-4 gap-2">
        {(Object.keys(lease) as Array<keyof LeaseState>).map((k) => (
          <Input
            key={String(k)}
            value={String(lease[k])}
            onChange={(e: any) => setField(k, e.target.value)}
            placeholder={String(k)}
            type={typeof lease[k] === "number" ? "number" : "text"}
          />
        ))}

        <Button onClick={run}>Generate Schedule</Button>
        <Button onClick={downloadCSV} disabled={downloading}>
          {downloading ? "Downloading..." : "Download CSV"}
        </Button>
      </Card>

      {schedule?.rows?.length > 0 && (
        <Card className="p-0 overflow-x-auto text-sm">
          <table className="min-w-full">
            <thead className="bg-gray-50">
              <tr>
                {Object.keys(schedule.rows[0] || {}).map((h) => (
                  <th key={h} className="p-2 text-left">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {schedule.rows.map((r: any, idx: number) => (
                <tr key={r.period ?? idx} className="border-t">
                  {Object.values(r).map((v: any, i: number) => (
                    <td key={i} className="p-2">
                      {String(v)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
