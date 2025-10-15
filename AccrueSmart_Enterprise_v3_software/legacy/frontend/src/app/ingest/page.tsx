
'use client';
import { useState } from "react";
import { api } from "@/lib/api";
import { toast } from "sonner";
export default function Ingest(){
  const [text, setText] = useState(`Master Subscription Agreement
Customer receives SaaS and maintenance for 36 months.
Transaction Price: $120,000. Acceptance testing required. Right to return within 30 days. Sales commission: $6,000.`);
  const [res, setRes] = useState<any>(null);
  const run=async()=>{ try{ const out=await api('/ingest/text',{method:'POST',body:JSON.stringify({filename:'demo.txt', text})}); setRes(out); toast.success('Analyzed'); } catch { toast.error('Analyze failed'); } };
  return (<main className="max-w-6xl mx-auto p-6 space-y-4"><h2 className="text-xl font-semibold">Ingest</h2><textarea className="w-full h-48 p-2 border rounded bg-white" value={text} onChange={e=>setText(e.target.value)}/><button className="px-4 py-2 rounded border bg-white" onClick={run}>Analyze</button>{res && <pre className="text-xs bg-white p-3 rounded-xl border">{JSON.stringify(res,null,2)}</pre>}</main>);
}
