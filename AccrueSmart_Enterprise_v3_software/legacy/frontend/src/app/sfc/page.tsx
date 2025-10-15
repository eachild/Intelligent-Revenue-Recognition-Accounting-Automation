
'use client';
import { useState } from "react";
import { api, API_BASE } from "@/lib/api";
import { toast } from "sonner";
export default function SFC(){
  const [initial, setInitial] = useState(10000);
  const [payments, setPayments] = useState<any>({"2025-02": 2500,"2025-03":2500,"2025-04":2500,"2025-05":2500});
  const [annualRate, setAnnualRate] = useState<number | null>(null);
  const [csvPath, setCsvPath] = useState<string | null>(null);
  const run = async()=>{ try{ await api('/sfc/schedule',{method:'POST',body:JSON.stringify({initial_carry:initial,payments,annual_rate:annualRate})}); toast.success('Computed'); } catch { toast.error('Failed'); } };
  const exportCsv = async()=>{ try{ const r=await api('/sfc/export_csv',{method:'POST',body:JSON.stringify({initial_carry:initial,payments,annual_rate:annualRate})}); setCsvPath(r.csv_path); toast.success('CSV ready'); } catch { toast.error('CSV failed'); } };
  const download=()=>{ if(!csvPath){ toast.error('No CSV'); return; } const a=document.createElement('a'); a.href=`${API_BASE}/files/get?path=${encodeURIComponent(csvPath)}`; a.download='sfc_amortization.csv'; a.click(); };
  return (<main className="max-w-6xl mx-auto p-6 space-y-4"><h2 className="text-xl font-semibold">SFC</h2><div className="flex gap-2"><button className="px-4 py-2 rounded border bg-white" onClick={run}>Compute</button><button className="px-4 py-2 rounded border bg-white" onClick={exportCsv}>Prepare CSV</button><button className="px-4 py-2 rounded border bg-white" onClick={download}>Download CSV</button></div></main>);
}
