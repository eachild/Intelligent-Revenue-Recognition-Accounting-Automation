"use client";
import { useEffect, useState } from "react";
import { api } from "@/src/lib/api";
import { Input } from "@/src/components/ui/input";
import { Button } from "@/src/components/ui/button";
import { Card } from "@/src/components/ui/card";

type Row = { id:string; code:string; name:string; revrec_code?:string; rule_type?:string; params?:any };

export default function CatalogPage() {
  const [rows,setRows] = useState<Row[]>([]);
  const [code,setCode] = useState(""); const [name,setName]=useState(""); const [desc,setDesc]=useState("");

  async function load(){ setRows(await api("/codes/products")); }
  async function add(){
    if(!code || !name) return;
    await api("/codes/products",{method:"POST", body:JSON.stringify({code,name,description:desc})});
    setCode(""); setName(""); setDesc(""); await load();
  }

  useEffect(()=>{ load(); },[]);

  return (
    <div className="max-w-5xl mx-auto space-y-4">
      <h1 className="text-xl font-semibold">Product Catalog</h1>
      <Card className="p-4 space-y-2">
        <div className="grid grid-cols-3 gap-2">
          <Input placeholder="Code (SKU-001)" value={code} onChange={e=>setCode(e.target.value)} />
          <Input placeholder="Name" value={name} onChange={e=>setName(e.target.value)} />
          <Input placeholder="Description" value={desc} onChange={e=>setDesc(e.target.value)} />
        </div>
        <Button onClick={add}>Add Product</Button>
      </Card>

      <Card className="p-0 overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50">
            <tr><th className="p-2 text-left">Code</th><th className="p-2 text-left">Name</th><th className="p-2">RevRec Code</th><th className="p-2">Rule</th></tr>
          </thead>
          <tbody>
            {rows.map(r=>(
              <tr key={r.id} className="border-t">
                <td className="p-2">{r.code}</td>
                <td className="p-2">{r.name}</td>
                <td className="p-2">{r.revrec_code || <span className="text-gray-400">–</span>}</td>
                <td className="p-2">{r.rule_type || <span className="text-gray-400">–</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}