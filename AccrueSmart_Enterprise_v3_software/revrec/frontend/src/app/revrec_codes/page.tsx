"use client";
import { useEffect, useState } from "react";
import { api } from "@/src/lib/api";
import { Input } from "@/src/components/ui/input";
import { Button } from "@/src/components/ui/button";
import { Card } from "@/src/components/ui/card";

type Rrc = { id:string; code:string; rule_type:"straight_line"|"point_in_time"|"milestone"|"percent_complete"|"usage"; params:any };
type Product = { id:string; code:string; name:string };

export default function RevRecCodesPage(){
  const [list,setList]=useState<Rrc[]>([]);
  const [code,setCode]=useState(""); const [rule,setRule]=useState<Rrc["rule_type"]>("straight_line");
  const [params,setParams]=useState('{"months":12}');
  const [products,setProducts]=useState<Product[]>([]);
  const [mapSku,setMapSku]=useState(""); const [mapRrc,setMapRrc]=useState("");

  async function load(){
    setList(await api("/codes/revrec"));
    const prods = await api("/codes/products");
    setProducts(prods.map((p:any)=>({id:p.id, code:p.code, name:p.name})));
  }
  async function add(){
    await api(`/codes/revrec?code=${encodeURIComponent(code)}&rule_type=${rule}`,{
      method:"POST", body: JSON.stringify(JSON.parse(params||"{}"))
    });
    setCode(""); setParams("{}"); await load();
  }
  async function map(){
    if(!mapSku || !mapRrc) return;
    await api(`/codes/map?product_code=${encodeURIComponent(mapSku)}&revrec_code=${encodeURIComponent(mapRrc)}`,{method:"POST"});
    await load();
  }

  useEffect(()=>{ load(); },[]);

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <h1 className="text-xl font-semibold">RevRec Codes</h1>

      <Card className="p-4 space-y-2">
        <div className="grid grid-cols-3 gap-2">
          <Input placeholder="Code (e.g., 606_SL_12)" value={code} onChange={e=>setCode(e.target.value)} />
          <select className="border rounded px-2" value={rule} onChange={e=>setRule(e.target.value as any)}>
            <option value="straight_line">straight_line</option>
            <option value="point_in_time">point_in_time</option>
            <option value="milestone">milestone</option>
            <option value="percent_complete">percent_complete</option>
            <option value="usage">usage</option>
          </select>
          <Input placeholder='Params JSON ({"months":12})' value={params} onChange={e=>setParams(e.target.value)} />
        </div>
        <Button onClick={add}>Add RevRec Code</Button>
      </Card>

      <Card className="p-4 space-y-2">
        <div className="grid grid-cols-3 gap-2">
          <Input placeholder="Product Code (SKU-001)" value={mapSku} onChange={e=>setMapSku(e.target.value)} />
          <Input placeholder="RevRec Code (606_SL_12)" value={mapRrc} onChange={e=>setMapRrc(e.target.value)} />
          <Button onClick={map}>Map Product → RevRec</Button>
        </div>
      </Card>

      <Card className="p-0 overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50">
            <tr><th className="p-2 text-left">Code</th><th className="p-2">Rule</th><th className="p-2 text-left">Params</th></tr>
          </thead>
        <tbody>
          {list.map(rr=>(
            <tr key={rr.id} className="border-t">
              <td className="p-2">{rr.code}</td>
              <td className="p-2 text-center">{rr.rule_type}</td>
              <td className="p-2 font-mono text-xs">{JSON.stringify(rr.params)}</td>
            </tr>
          ))}
        </tbody></table>
      </Card>
    </div>
  );
}