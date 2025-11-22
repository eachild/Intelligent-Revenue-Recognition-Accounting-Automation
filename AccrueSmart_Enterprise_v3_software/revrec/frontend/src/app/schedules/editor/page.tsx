"use client";
import { useEffect, useMemo, useState } from "react";
import { api } from "@/src/lib/api";
import { Input } from "@/src/components/ui/input";
import { Button } from "@/src/components/ui/button";
import { Card } from "@/src/components/ui/card";

type GridRow = { line_no:number; period:string; amount:number; product_code?:string; revrec_code?:string };

export default function ScheduleEditorPage(){
  const [cid,setCid]=useState("C-TEST");
  const [rows,setRows]=useState<GridRow[]>([]);
  const [file,setFile]=useState<File|null>(null);

  async function load(){ setRows(await api(`/schedules/grid/${encodeURIComponent(cid)}`)); }
  async function save(){ await api(`/schedules/grid/${encodeURIComponent(cid)}`,{method:"POST", body:JSON.stringify({rows})}); await load(); }
  async function exportCsv(){
    const url = `${process.env.NEXT_PUBLIC_API_URL}/schedules/grid/${encodeURIComponent(cid)}/export/csv`;
    window.open(url, "_blank");
  }
  async function importCsv(){
    if(!file) return;
    const fd = new FormData(); fd.append("file", file);
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/schedules/grid/${encodeURIComponent(cid)}/import/csv`, { method:"POST", body:fd });
    if(!res.ok) alert("Import failed");
    await load();
  }

  useEffect(()=>{ load(); },[]);

  function addRow(){
    const nextLine = (rows.at(-1)?.line_no ?? 0) + 1;
    setRows([...rows, { line_no: nextLine, period: "2025-01", amount: 0 }]);
  }

  return (
    <div className="max-w-6xl mx-auto space-y-4">
      <h1 className="text-xl font-semibold">Schedule Editor</h1>
      <Card className="p-4 flex gap-2 items-center">
        <Input className="max-w-xs" value={cid} onChange={e=>setCid(e.target.value)} />
        <Button onClick={load}>Load</Button>
        <Button onClick={save} variant="secondary">Save</Button>
        <input type="file" accept=".csv" onChange={e=>setFile(e.target.files?.[0]||null)} />
        <Button onClick={importCsv}>Import CSV</Button>
        <Button onClick={exportCsv}>Export CSV</Button>
      </Card>

      <Card className="p-0 overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="p-2">Line</th><th className="p-2">Period (YYYY-MM)</th><th className="p-2">Amount</th>
              <th className="p-2">Product Code</th><th className="p-2">RevRec Code</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r,idx)=>(
              <tr key={`${r.line_no}:${r.period}`} className="border-t">
                <td className="p-1 w-16">
                  <Input value={r.line_no} type="number"
                    onChange={e=>{
                      const v = parseInt(e.target.value||"0"); const copy=[...rows]; copy[idx].line_no = v; setRows(copy);
                    }}/>
                </td>
                <td className="p-1 w-40">
                  <Input value={r.period}
                    onChange={e=>{ const copy=[...rows]; copy[idx].period = e.target.value; setRows(copy); }}/>
                </td>
                <td className="p-1 w-32">
                  <Input type="number" step="0.01" value={r.amount}
                    onChange={e=>{ const copy=[...rows]; copy[idx].amount = parseFloat(e.target.value||"0"); setRows(copy); }}/>
                </td>
                <td className="p-1 w-40">
                  <Input value={r.product_code||""}
                    onChange={e=>{ const copy=[...rows]; copy[idx].product_code = e.target.value; setRows(copy); }}/>
                </td>
                <td className="p-1 w-40">
                  <Input value={r.revrec_code||""}
                    onChange={e=>{ const copy=[...rows]; copy[idx].revrec_code = e.target.value; setRows(copy); }}/>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
      <div className="text-xs text-gray-600">Tip: Import a CSV with columns: line_no, period, amount, product_code, revrec_code</div>
    </div>
  );
}