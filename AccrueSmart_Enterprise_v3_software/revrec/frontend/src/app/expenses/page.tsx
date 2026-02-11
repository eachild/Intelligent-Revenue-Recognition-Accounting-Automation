"use client";
import { useState } from "react";
import { Input } from "@/src/components/ui/input";
import { Textarea } from "@/src/components/ui/textarea";
import { Button } from "@/src/components/ui/button";
import { Card } from "@/src/components/ui/card";
import { api } from "@/src/lib/api";

export default function ExpensesPage(){
  const [text,setText]=useState("");
  const [amount,setAmount]=useState<number>(0);
  const [cls,setCls]=useState<any>(null);

  const [preAmt,setPreAmt]=useState<number>(1200);
  const [months,setMonths]=useState<number>(12);
  const [start,setStart]=useState<string>("2025-01-01");
  const [sched,setSched]=useState<any>(null);

  async function classify(){
    setCls(await api("/expenses/classify",{method:"POST", body:JSON.stringify({text, amount})}));
  }
  async function buildPrepaid(){
    setSched(await api("/expenses/prepaid/schedule",{method:"POST", body:JSON.stringify({amount:preAmt, months, start})}));
  }

  return (
    <div className="mx-auto max-w-5xl space-y-4">
      <h1 className="text-xl font-semibold">Expenses (AI + Prepaid)</h1>
      <Card className="p-3 space-y-2">
        <Textarea rows={4} placeholder="Paste invoice or description..." value={text} onChange={e=>setText(e.target.value)} />
        <div className="flex gap-2">
          <Input type="number" placeholder="Amount" value={amount} onChange={e=>setAmount(parseFloat(e.target.value||"0"))}/>
          <Button onClick={classify}>AI Classify</Button>
        </div>
        {cls && <pre className="text-sm">{JSON.stringify(cls,null,2)}</pre>}
      </Card>

      <Card className="p-3 space-y-2">
        <div className="grid md:grid-cols-3 gap-2">
          <Input type="number" placeholder="Prepaid Amount" value={preAmt} onChange={e=>setPreAmt(parseFloat(e.target.value||"0"))}/>
          <Input type="number" placeholder="Months" value={months} onChange={e=>setMonths(parseInt(e.target.value||"0"))}/>
          <Input type="text" placeholder="Start (YYYY-MM-DD)" value={start} onChange={e=>setStart(e.target.value)}/>
        </div>
        <Button onClick={buildPrepaid}>Build Schedule</Button>
        {sched && <pre className="text-sm">{JSON.stringify(sched,null,2)}</pre>}
      </Card>
    </div>
  );
}
