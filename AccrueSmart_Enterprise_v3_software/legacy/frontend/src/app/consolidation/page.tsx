
'use client';
import { useState } from "react";
import { api } from "@/lib/api";
import { toast } from "sonner";
export default function Consolidation(){
  const [rateType, setRateType] = useState<'average' | 'month_end'>('month_end');
  const [payload, setPayload] = useState<any>({
    parent_currency:"USD",
    entities:[{entity:"US", currency:"USD", schedules:{"2025-01":1000,"2025-02":1200}, commissions:{"2025-01":100}},
              {entity:"EU", currency:"EUR", schedules:{"2025-01":800,"2025-02":900}, commissions:{}}],
    fx_rates:[{period:"2025-01",currency:"EUR",rate_to_parent:1.12,rate_type:"average"},{period:"2025-01",currency:"EUR",rate_to_parent:1.10,rate_type:"month_end"},{period:"2025-02",currency:"EUR",rate_to_parent:1.11,rate_type:"average"},{period:"2025-02",currency:"EUR",rate_to_parent:1.08,rate_type:"month_end"}],
    eliminations:[{period:"2025-01", amount_parent_ccy: 100}], rate_type:"month_end", intercompany:[{"doc_id":"IC-001","counterparty":"EU","period":"2025-02","amount_parent_ccy":150}]
  });
  const [res, setRes] = useState<any>(null);
  const toggle = (t:'average'|'month_end')=>{ setRateType(t); setPayload((p:any)=>({...p, rate_type:t})); };
  const run = async()=>{ try{ const r=await api('/consolidation/multientity',{method:'POST',body:JSON.stringify({...payload, rate_type:rateType})}); setRes(r); toast.success('Consolidated'); } catch { toast.error('Failed'); } };
  return (<main className="max-w-6xl mx-auto p-6 space-y-4"><h2 className="text-xl font-semibold">Consolidation</h2><div className="flex items-center gap-2"><span className="text-sm">Rate Type:</span><button className={`px-3 py-1 rounded border ${rateType==='average'?'bg-slate-900 text-white':''}`} onClick={()=>toggle('average')}>Average</button><button className={`px-3 py-1 rounded border ${rateType==='month_end'?'bg-slate-900 text-white':''}`} onClick={()=>toggle('month_end')}>Month-end</button></div><button className="px-4 py-2 rounded border bg-white" onClick={run}>Consolidate</button>{res && <pre className="text-xs bg-white p-3 rounded-xl border">{JSON.stringify(res,null,2)}</pre>}</main>);
}
