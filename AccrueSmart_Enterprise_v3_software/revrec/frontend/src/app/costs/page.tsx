"use client";
import { useState } from "react";
import { api } from "@/src/lib/api";
import { Input } from "@/src/components/ui/input";
import { Button } from "@/src/components/ui/button";
import { Card } from "@/src/components/ui/card";

type Row = { period:number; date:string; opening:number; amortization:number; closing:number };

export default function CostsPage() {
  const [total, setTotal] = useState(2400);
  const [months, setMonths] = useState(24);
  const [start, setStart] = useState("2025-01-01");
  const [method, setMethod] = useState("straight_line");
  const [weights, setWeights] = useState("");
  const [rows, setRows] = useState<Row[]>([]);
  const [error, setError] = useState("");

  async function run() {
    setError("");
    try {
      const body: any = { total, months, start, method };

      if (method !== "straight_line") {
        const parsed = weights.split(",").map((x) => parseFloat(x.trim())).filter((x) => !isNaN(x));
        if (parsed.length !== months) {
          setError(`You must enter exactly ${months} comma-separated weights (got ${parsed.length}).`);
          return;
        }
        if (method === "percent_complete") body.percent_complete = parsed;
        else body.curve = parsed;
      }

      const res = await api("/costs/amortize", { method:"POST", body:JSON.stringify(body) });
      setRows(res.rows);
    } catch (e:any) {
      setError(e?.message || "Failed to compute");
    }
  }

  const needsWeights = method !== "straight_line";

  return (
    <div className="max-w-5xl mx-auto space-y-4">
      <h1 className="text-xl font-semibold">ASC 340-40 Costs Amortization</h1>

      <Card className="p-4 space-y-3">
        <div className="grid grid-cols-5 gap-2 items-center">
          <Input type="number" value={total} onChange={e=>setTotal(parseFloat(e.target.value||"0"))} placeholder="Total cost" />
          <Input type="number" value={months} onChange={e=>setMonths(parseInt(e.target.value||"0"))} placeholder="Months" />
          <Input type="date" value={start} onChange={e=>setStart(e.target.value)} />
          <select className="border rounded px-2 py-1" value={method} onChange={e=>{ setMethod(e.target.value); setWeights(""); }}>
            <option value="straight_line">straight_line</option>
            <option value="percent_complete">percent_complete</option>
            <option value="custom_curve">custom_curve</option>
          </select>
          <Button onClick={run}>Run</Button>
        </div>

        {needsWeights && (
          <div className="space-y-1">
            <label className="text-xs text-gray-500">
              {method === "percent_complete"
                ? `Completion weights — enter exactly ${months} comma-separated values (e.g. 0.1,0.2,...)`
                : `Custom curve — enter exactly ${months} comma-separated weights (e.g. 0.5,0.3,0.2,...)`}
            </label>
            <Input
              value={weights}
              onChange={e => setWeights(e.target.value)}
              placeholder={`${months} values, e.g. ${Array(Math.min(months, 3)).fill("0.1").join(",")},…`}
            />
          </div>
        )}
      </Card>

      {error && <div className="text-red-600 text-sm">{error}</div>}

      {rows.length > 0 && (
        <Card className="p-0 overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="p-2 text-left">Period</th>
                <th className="p-2 text-left">Month</th>
                <th className="p-2 text-right">Opening</th>
                <th className="p-2 text-right">Amortization</th>
                <th className="p-2 text-right">Closing</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r)=>(
                <tr key={r.period} className="border-t">
                  <td className="p-2">{r.period}</td>
                  <td className="p-2">{r.date}</td>
                  <td className="p-2 text-right">{r.opening.toFixed(2)}</td>
                  <td className="p-2 text-right text-blue-600">{r.amortization.toFixed(2)}</td>
                  <td className="p-2 text-right">{r.closing.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
      {rows.length > 0 && (
        <div className="text-xs text-gray-500">
          Total Amortization: {rows.reduce((s, r)=>s+r.amortization, 0).toFixed(2)}
        </div>
      )}
    </div>
  );
}
