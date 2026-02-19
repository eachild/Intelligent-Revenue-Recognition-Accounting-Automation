"use client";

import { useState } from "react";
import { api } from "@/src/lib/api";
import { Button, Card } from "@/src/components/ui";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

export default function AuditorPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runAudit() {
    setLoading(true);
    setError(null);

    try {
      const [revrec, leases, tax, forecast] = await Promise.allSettled([
        api("/revrec/schedule", { method: "GET" }),
        api("/leases/schedule", {
          method: "POST",
          body: JSON.stringify({
            lease_id: "AUTO-AUDIT",
            start_date: "2025-01-01",
            end_date: "2026-12-31",
            payment: 4500,
            frequency: "monthly",
            discount_rate_annual: 0.06,
          }),
        }),
        api("/tax/asc740/calc", {
          method: "POST",
          body: JSON.stringify({
            company: "AuditTestCo",
            statutory_rate: 0.21,
            valuation_allowance_pct: 0.05,
            differences: [
              { period: "2025-12", amount: 8000, reversal_year: 2026 },
              { period: "2026-12", amount: -4000, reversal_year: 2027 },
            ],
          }),
        }),
        api("/forecast/revenue", {
          method: "POST",
          body: JSON.stringify({
            history: {
              "2024-09": 10000,
              "2024-10": 12000,
              "2024-11": 11000,
              "2024-12": 11500,
            },
            horizon: 6,
            method: "exp_smooth",
          }),
        }),
      ]);

      const findings: Record<string, any> = {};
      if (revrec.status === "fulfilled") findings.revrec = revrec.value;
      if (leases.status === "fulfilled") findings.leases = leases.value;
      if (tax.status === "fulfilled") findings.tax = tax.value;
      if (forecast.status === "fulfilled") findings.forecast = forecast.value;

      const audit = await api("/auditor/summary", {
        method: "POST",
        body: JSON.stringify(findings),
      });

      setData(audit);
    } catch (e) {
      console.error(e);
      setError("Audit failed. Check backend endpoints + permissions.");
    } finally {
      setLoading(false);
    }
  }

  const chartData = data
    ? Object.entries(data.scores || {}).map(([k, v]) => ({ module: k, score: v }))
    : [];

  return (
    <div className="max-w-6xl mx-auto space-y-4">
      <h1 className="text-xl font-semibold">AI Auditor Dashboard</h1>

      <Button onClick={runAudit} disabled={loading}>
        {loading ? "Analyzing..." : "Run Full Audit"}
      </Button>

      {error && <div className="text-red-600 text-sm">{error}</div>}

      {data && (
        <>
          <Card>
            <div className="font-medium">Overall Score: {data.avg_score}</div>
            <ul className="list-disc ml-6 text-sm mt-2">
              {(data.notes || []).map((n: string, i: number) => (
                <li key={i}>{n}</li>
              ))}
            </ul>
          </Card>

          <Card>
            <div style={{ width: "100%", height: 320 }}>
              <ResponsiveContainer>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="module" />
                  <YAxis domain={[0, 100]} />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="score" name="Score" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card className="whitespace-pre-wrap text-sm bg-gray-50">
            {data.summary_memo}
          </Card>
        </>
      )}
    </div>
  );
}
