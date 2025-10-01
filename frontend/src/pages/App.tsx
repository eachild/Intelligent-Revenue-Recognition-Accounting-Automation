
import React, { useState } from 'react';
import axios from 'axios';
type PO={po_id:string;description:string;ssp:number;method:'point_in_time'|'straight_line'|'milestone'|'percent_complete';start_date?:string;end_date?:string;params?:any;};
type AllocationResp={allocated:{po_id:string,ssp:number,allocated_price:number}[];schedules:Record<string,Record<string,number>>;commission_schedule?:Record<string,number>|null;};
const API=(import.meta as any).env.VITE_API_BASE||'http://localhost:8011';
export default function App(){
  const [contractId,setContractId]=useState('C-EX-001');
  const [customer,setCustomer]=useState('SampleCo');
  const [price,setPrice]=useState(1200);
  const [pos,setPos]=useState<PO[]>([
    {po_id:'PO-1',description:'Device',ssp:933.33,method:'point_in_time',start_date:'2025-01-01'},
    {po_id:'PO-2',description:'Maintenance 36mo',ssp:266.67,method:'straight_line',start_date:'2025-01-01',end_date:'2027-12-01'}
  ]);
  const [commission,setCommission]=useState({total_commission:120,benefit_months:36,practical_expedient_1yr:false});
  const [resp,setResp]=useState<AllocationResp|null>(null);
  const addPO=()=>setPos(p=>[...p,{po_id:`PO-${p.length+1}`,description:'',ssp:0,method:'point_in_time'}]);
  const submit=async()=>{const payload={contract_id:contractId,customer,transaction_price:price,pos,commission};const r=await axios.post(`${API}/contracts/allocate`,payload);setResp(r.data);};
  return (<div className='max-w-6xl mx-auto p-6 space-y-6'>
    <header className='flex items-center justify-between'><h1 className='text-2xl font-bold'>AccrueSmart — Revenue Recognition</h1><button className='btn' onClick={submit}>Allocate & Generate</button></header>
    <section className='card'><h2 className='font-semibold mb-2'>Contract</h2><div className='grid grid-cols-3 gap-4'>
      <div><label className='text-sm'>Contract ID</label><input className='input' value={contractId} onChange={e=>setContractId(e.target.value)}/></div>
      <div><label className='text-sm'>Customer</label><input className='input' value={customer} onChange={e=>setCustomer(e.target.value)}/></div>
      <div><label className='text-sm'>Transaction Price</label><input type='number' className='input' value={price} onChange={e=>setPrice(+e.target.value)}/></div>
    </div></section>
    <section className='card'><div className='flex items-center justify-between'><h2 className='font-semibold mb-2'>Performance Obligations</h2><button className='btn' onClick={addPO}>Add PO</button></div>
      <table className='table'><thead><tr><th>PO</th><th>Description</th><th>SSP</th><th>Method</th><th>Start</th><th>End</th></tr></thead><tbody>
        {pos.map((p,i)=>(<tr key={i}>
          <td><input className='input' value={p.po_id} onChange={e=>{const n=[...pos];n[i]={...p,po_id:e.target.value};setPos(n);}}/></td>
          <td><input className='input' value={p.description} onChange={e=>{const n=[...pos];n[i]={...p,description:e.target.value};setPos(n);}}/></td>
          <td><input type='number' className='input' value={p.ssp} onChange={e=>{const n=[...pos];n[i]={...p,ssp:+e.target.value};setPos(n);}}/></td>
          <td><select className='input' value={p.method} onChange={e=>{const n=[...pos];n[i]={...p,method:e.target.value as any};setPos(n);}}>
            <option value='point_in_time'>Point in Time</option><option value='straight_line'>Straight Line</option>
            <option value='milestone'>Milestone</option><option value='percent_complete'>Percent Complete</option>
          </select></td>
          <td><input className='input' value={p.start_date||''} onChange={e=>{const n=[...pos];n[i]={...p,start_date:e.target.value};setPos(n);}}/></td>
          <td><input className='input' value={p.end_date||''} onChange={e=>{const n=[...pos];n[i]={...p,end_date:e.target.value};setPos(n);}}/></td>
        </tr>))}
      </tbody></table>
    </section>
    <section className='card'><h2 className='font-semibold mb-2'>Commissions</h2><div className='grid grid-cols-3 gap-4'>
      <div><label className='text-sm'>Total Commission</label><input type='number' className='input' value={commission.total_commission} onChange={e=>setCommission({...commission,total_commission:+e.target.value})}/></div>
      <div><label className='text-sm'>Benefit Months</label><input type='number' className='input' value={commission.benefit_months} onChange={e=>setCommission({...commission,benefit_months:+e.target.value})}/></div>
      <div className='flex items-center gap-2'><input type='checkbox' checked={commission.practical_expedient_1yr} onChange={e=>setCommission({...commission,practical_expedient_1yr:e.target.checked})}/><span>Practical Expedient ≤ 1yr</span></div>
    </div></section>
    {resp && (<section className='card'><h2 className='font-semibold mb-2'>Results</h2>
      <div className='grid grid-cols-2 gap-6'><div><h3 className='font-semibold mb-2'>Allocations</h3>
        <table className='table'><thead><tr><th>PO</th><th>SSP</th><th>Allocated</th></tr></thead><tbody>
          {resp.allocated.map((a,i)=>(<tr key={i}><td>{a.po_id}</td><td>{a.ssp.toFixed(2)}</td><td>{a.allocated_price.toFixed(2)}</td></tr>))}
        </tbody></table></div>
        <div><h3 className='font-semibold mb-2'>Commission Schedule</h3>
          {!resp.commission_schedule ? <p>No commission</p> : <table className='table'><thead><tr><th>Period</th><th>Amount</th></tr></thead><tbody>
            {Object.entries(resp.commission_schedule).map(([k,v])=>(<tr key={k}><td>{k}</td><td>{v.toFixed(2)}</td></tr>))}
          </tbody></table>}
        </div></div>
      <div className='mt-6'><h3 className='font-semibold mb-2'>Revenue Schedules</h3>
        {Object.entries(resp.schedules).map(([poid,sched])=> (<div key={poid} className='mb-4'><h4 className='font-medium'>{poid}</h4>
          <table className='table'><thead><tr><th>Period</th><th>Amount</th></tr></thead><tbody>
            {Object.entries(sched).map(([k,v])=>(<tr key={k}><td>{k}</td><td>{v.toFixed(2)}</td></tr>))}
          </tbody></table></div>))}
      </div></section>)}
  </div>);
}
