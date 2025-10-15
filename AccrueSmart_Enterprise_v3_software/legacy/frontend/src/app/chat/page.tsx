
'use client';
import { useState } from "react";
import { api } from "@/lib/api";
import { toast } from "sonner";
export default function Chat(){
  const [msg, setMsg] = useState('Summarize a contract and generate a disclosure');
  const [out, setOut] = useState<any>(null);
  const run = async()=>{ try{ const r=await api('/chat',{method:'POST',body:JSON.stringify({prompt:msg})}); setOut(r); } catch { toast.error('Chat failed'); } };
  return (<main className="max-w-4xl mx-auto p-6 space-y-4"><h2 className="text-xl font-semibold">Chat Orchestrator</h2><input className="w-full p-2 border rounded" value={msg} onChange={e=>setMsg(e.target.value)}/><button className="px-4 py-2 rounded border bg-white" onClick={run}>Send</button>{out && <pre className="text-xs bg-white p-3 rounded-xl border">{JSON.stringify(out,null,2)}</pre>}</main>);
}
