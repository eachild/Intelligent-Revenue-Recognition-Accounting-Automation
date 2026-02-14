
'use client';
import { useState } from "react";
import { api } from "../../lib/api";
import { Button, Card, Textarea } from "../../components/ui";
export default function Ingest(){
  const [text, setText] = useState('Customer receives SaaS and hardware. Price $10,000. Right to return.');
  const [res, setRes] = useState<any>(null);
  const runText=async()=>{ const out=await api('/ingest/text',{method:'POST',body:JSON.stringify({filename:'demo.txt', text})}); setRes(out); };
  return <main className="max-w-6xl mx-auto p-6 space-y-3">
    <h2 className="text-xl font-semibold">Ingest</h2>
    <Card><Textarea className="w-full h-40" value={text} onChange={e=>setText(e.target.value)}/><Button onClick={runText}>Analyze</Button></Card>
    {res && <Card><pre className="text-xs">{JSON.stringify(res, null, 2)}</pre></Card>}
  </main>;
}
