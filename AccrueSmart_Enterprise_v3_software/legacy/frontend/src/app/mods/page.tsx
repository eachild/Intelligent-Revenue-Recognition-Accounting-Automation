
'use client';
import { useState } from "react";
import { api } from "@/lib/api";
import { toast } from "sonner";
export default function Mods(){
  const [base, setBase] = useState<any>({ contract_id:"C-MOD", customer:"X", transaction_price:10000, pos:[{po_id:"A",description:"Service 10m",ssp:10000,method:"straight_line",start_date:"2025-01-01",end_date:"2025-10-01"}]});
  const [mod, setMod] = useState<any>({ effective_date:"2025-06-01", transaction_price_delta:2000, add_pos:[{po_id:"B",description:"Addon",ssp:2000,method:"point_in_time",start_date:"2025-06-01"}] });
  const [res, setRes] = useState<any>(null);
  const run = async()=>{ try{ const r=await api('/contracts/modify/catchup',{method:'POST',body:JSON.stringify({base, modification:mod})}); setRes(r); toast.success('Catch-up posted'); } catch { toast.error('Failed'); } };
  return (<main className="max-w-6xl mx-auto p-6 space-y-4"><h2 className="text-xl font-semibold">Modifications</h2><button className="px-4 py-2 rounded border bg-white" onClick={run}>Simulate</button>{res && <pre className="text-xs bg-white p-3 rounded-xl border">{JSON.stringify(res,null,2)}</pre>}</main>);
}
