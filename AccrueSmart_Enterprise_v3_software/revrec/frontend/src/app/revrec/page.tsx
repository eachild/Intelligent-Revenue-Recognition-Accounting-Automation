'use client';
import { useState } from "react";
import { api } from "../../lib/api";
import { toast } from "sonner";
export default function Revrec(){
    //dummy contract for allocation
  const [payload, setPayload] = useState<any>({ 
    contract_id:"UX-DEMO", 
    customer:"DemoCo", 
    transaction_price:50000, 
    pos:[{
        po_id:"PO-1", 
        description:"SaaS 12m", 
        ssp:20000, 
        method:"straight_line", 
        start_date:"2025-01-01", 
        end_date:"2025-12-01"},

        {
        po_id:"PO-2", 
        description:"Implementation", 
        ssp:30000, 
        method:"milestone", 
        params:{
            milestones:[{
                id:"M1",
                percent_of_price:0.5,
                met_date:"2025-03-01"},

                {
                id:"M2",
                percent_of_price:0.5,
                met_date:"2025-06-01"
            }]
        }
    }]
});

//sends JSON to backend at endpoint "/contracts/allocate"
//the toast package will show success or failure
//result will be stored in the res state
  const [res, setRes] = useState<any>(null);
  const run=async()=>{ 
    try{ 
        setRes(await api('/contracts/allocate',
            {method:'POST',
            body:JSON.stringify(payload)})); 
        toast.success('Allocated'); 
    } 
        catch { 
            toast.error('Allocation failed'); 
        } 
    };
    //styling 
  return (
  <main className="max-w-6xl mx-auto p-6 space-y-4">
    <h2 className="text-xl font-semibold">RevRec Page</h2>
    <p>Allows user to send a dummy JSON object to backend API</p>
    <button className="px-4 py-2 rounded border bg-white" onClick={run}>Allocate</button>
    {res && <pre className="text-xs bg-white p-3 rounded-xl border">{JSON.stringify(res,null,2)}</pre>}
    </main>);
}