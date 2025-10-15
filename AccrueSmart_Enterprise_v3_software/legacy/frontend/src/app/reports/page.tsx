
'use client';
import { useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer, BarChart, Bar, Legend, ComposedChart, Area } from "recharts";
export default function Reports(){
  const byEntity = { US: {"2025-01":10000,"2025-02":12000}, EU: {"2025-01":8000,"2025-02":8500} };
  const byProduct = { SaaS: {"2025-01":9000,"2025-02":10000}, Services: {"2025-01":5000,"2025-02":5500} };
  const byGeo = { NA: {"2025-01":14000,"2025-02":16000}, EU: {"2025-01":6000,"2025-02":6500} };
  const series = (m:any)=>{ const ps = Array.from(new Set(Object.values(m).flatMap((o:any)=>Object.keys(o)))).sort(); return ps.map(p=>({period:p, ...Object.fromEntries(Object.entries(m).map(([k,v]:any)=>[k, v[p]||0]))})); };
  return (<main className="max-w-7xl mx-auto p-6 space-y-8">
    <h2 className="text-xl font-semibold">Reports & Dashboards</h2>
    <section className="bg-white p-4 rounded-xl border"><div className="font-semibold mb-2">Revenue over time — by Entity</div><div style={{width:'100%',height:280}}><ResponsiveContainer><ComposedChart data={series(byEntity)}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="period"/><YAxis/><Tooltip/><Legend/>{Object.keys(byEntity).map(k=> <Line key={k} type="monotone" dataKey={k} />)}</ComposedChart></ResponsiveContainer></div></section>
    <section className="bg-white p-4 rounded-xl border"><div className="font-semibold mb-2">Revenue over time — by Product Line</div><div style={{width:'100%',height:280}}><ResponsiveContainer><ComposedChart data={series(byProduct)}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="period"/><YAxis/><Tooltip/><Legend/>{Object.keys(byProduct).map(k=> <Area key={k} type="monotone" dataKey={k} />)}</ComposedChart></ResponsiveContainer></div></section>
    <section className="bg-white p-4 rounded-xl border"><div className="font-semibold mb-2">Revenue over time — by Geography</div><div style={{width:'100%',height:280}}><ResponsiveContainer><BarChart data={series(byGeo)}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="period"/><YAxis/><Tooltip/><Legend/>{Object.keys(byGeo).map(k=> <Bar key={k} dataKey={k} />)}</BarChart></ResponsiveContainer></div></section>
    <section className="bg-white p-4 rounded-xl border"><div className="font-semibold mb-2">RPO Rollforward</div><pre className="text-xs bg-slate-50 p-3 rounded-lg border">{JSON.stringify({begin:50000, additions:20000, satisfied:18000, end:52000},null,2)}</pre></section>
    <section className="bg-white p-4 rounded-xl border"><div className="font-semibold mb-2">Contract Balances Rollforward</div><pre className="text-xs bg-slate-50 p-3 rounded-lg border">{JSON.stringify({contract_assets_end:9000, deferred_revenue_end:13000},null,2)}</pre></section>
    <section className="bg-white p-4 rounded-xl border"><div className="font-semibold mb-2">Commissions Rollforward</div><pre className="text-xs bg-slate-50 p-3 rounded-lg border">{JSON.stringify({capitalized_end:3500},null,2)}</pre></section>
    <section className="bg-white p-4 rounded-xl border"><div className="font-semibold mb-2">Variable Consideration Tracker</div><pre className="text-xs bg-slate-50 p-3 rounded-lg border">{JSON.stringify({returns_liability:{'2025-01':-500,'2025-02':200}, loyalty_liability:{'2025-01':100,'2025-02':150}, trueups:{'2025-02':50}},null,2)}</pre></section>
    <section className="bg-white p-4 rounded-xl border"><div className="font-semibold mb-2">Principal vs Agent Summary</div><pre className="text-xs bg-slate-50 p-3 rounded-lg border">{JSON.stringify([{contract_id:'C-100', role:'principal', indicators:{control_before_transfer:true}}, {contract_id:'C-101', role:'agent', indicators:{inventory_risk:false}}],null,2)}</pre></section>
    <section className="bg-white p-4 rounded-xl border"><div className="font-semibold mb-2">Disclosure Pack</div><p className="text-sm">Call <code>POST /reports/disclosure_pack</code> with bullets & sections; download via <code>GET /files/get</code>.</p></section>
  </main>);
}
