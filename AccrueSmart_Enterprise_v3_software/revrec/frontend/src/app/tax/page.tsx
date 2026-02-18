"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { Button, Card, Textarea } from "@/components/ui";
type TempDiff = { period: string; amount: number; reversal_year: number };

export default function TaxPage() {
  const [company, setCompany] = useState("Acme Inc");
  const [rate, setRate] = useState(0.21);
  const [va, setVA] = useState(0.1);

  const [diffs] = useState<TempDiff[]>([
    { period: "2025-12", amount: 10000, reversal_year: 2026 },
    { period: "2026-12", amount: -5000, reversal_year: 2027 },
  ]);

  const [result, setResult] = useState<any>(null);

  async function calc() {
    const res = await api("/tax/asc740/calc", {
      method: "POST",
      body: JSON.stringify({
        company,
        statutory_rate: rate,
        valuation_allowance_pct: va,
        differences: diffs,
      }),
    });
    setResult(res);
  }

  async function memo() {
    const res = await api("/tax/asc740/memo", {
      method: "POST",
      body: JSON.stringify({
        company,
        statutory_rate: rate,
        valuation_allowance_pct: va,
        differences: diffs,
      }),
    });

    const blob = new Blob([res.memo], { type: "text/plain" });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = `${company}_ASC740.txt`;
    a.click();

    URL.revokeObjectURL(url);
  }

  return (
    <div className="max-w-5xl mx-auto space-y-4">
      <h1 className="text-xl font-semibold">ASC 740 Deferred Tax Calculator</h1>

      <Card className="space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
          <Input
            value={company}
            onChange={(e: any) => setCompany(e.target.value)}
            placeholder="Company"
          />
          <Input
            type="number"
            value={String(rate)}
            onChange={(e: any) => setRate(Number(e.target.value))}
            placeholder="Tax Rate"
          />
          <Input
            type="number"
            value={String(va)}
            onChange={(e: any) => setVA(Number(e.target.value))}
            placeholder="Valuation Allowance %"
          />
        </div>

        <div className="flex gap-2">
          <Button onClick={calc}>Compute</Button>
          <Button onClick={memo}>Download Memo</Button>
        </div>
      </Card>

      {result && (
        <Card className="space-y-2 text-sm">
          <div>Gross DTL: ${result.gross?.DTL}</div>
          <div>Gross DTA: ${result.gross?.DTA}</div>
          <div>Valuation Allowance: ${result.valuation_allowance}</div>
          <div>Net Deferred Tax: ${result.net_deferred_tax}</div>
        </Card>
      )}
    </div>
  );
}
