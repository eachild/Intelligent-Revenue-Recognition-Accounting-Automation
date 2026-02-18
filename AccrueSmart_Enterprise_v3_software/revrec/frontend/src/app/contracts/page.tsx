"use client";
import { useState } from "react";
import { api } from "@/src/lib/api";
import { Input } from "@/src/components/ui/input";
import { Button } from "@/src/components/ui/button";
import { Card } from "@/src/components/ui/card";
import { toast } from "sonner";

type LineItem = { product_code: string; amount: number };

export default function ContractsPage() {
  const [contract_id, setContractId] = useState("C-TEST");
  const [customer, setCustomer] = useState("DemoCo");
  const [transaction_price, setTxnPrice] = useState(50000);
  const [default_start, setDefaultStart] = useState("2025-01-01");
  const [contractText, setContractText] = useState("");
  const [items, setItems] = useState<LineItem[]>([
    { product_code: "SKU-001", amount: 20000 },
    { product_code: "SKU-002", amount: 30000 },
  ]);

  const [payload, setPayload] = useState<any>({
    contract_id: "C-TEST",
    customer: "DemoCo",
    transaction_price: 50000,
    pos: [
      { po_id: "PO-1", description: "SaaS 12m", ssp: 20000, method: "straight_line", start_date: "2025-01-01", end_date: "2025-12-01" },
      { po_id: "PO-2", description: "Implementation", ssp: 30000, method: "milestone", params: { milestones: [{ id: "M1", percent_of_price: 0.5, met_date: "2025-03-01" }, { id: "M2", percent_of_price: 0.5, met_date: "2025-06-01" }] } },
    ],
  });

  const [allocResult, setAllocResult] = useState<any>(null);

  async function allocate() {
    try {
      const res = await api("/contracts/allocate", { method: "POST", body: JSON.stringify(payload) });
      setAllocResult(res);
      toast.success("Allocated");
    } catch {
      toast.error("Allocation failed");
    }
  }

  async function aiGenerate() {
    try {
      const text = contractText;
      const line_hints = items.map((i) => ({ product_code: i.product_code, amount: i.amount }));
      const res = await api("/schedules/ai-generate", {
        method: "POST",
        body: JSON.stringify({ contract_id, text, default_start, line_hints }),
      });
      const rows = Object.entries(res.schedule).map(([period, amount], ix) => ({
        line_no: ix + 1,
        period,
        amount,
        product_code: "",
        revrec_code: "",
        source: "ai",
      }));
      await api(`/schedules/grid/${encodeURIComponent(contract_id)}`, {
        method: "POST",
        body: JSON.stringify({ rows }),
      });
      toast.success("AI schedule saved to grid.");
    } catch {
      toast.error("AI generation failed");
    }
  }

  function updateItem(idx: number, field: keyof LineItem, value: string) {
    const copy = [...items];
    copy[idx] = { ...copy[idx], [field]: field === "amount" ? parseFloat(value || "0") : value };
    setItems(copy);
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <h1 className="text-xl font-semibold">Contracts</h1>

      <Card className="p-4 space-y-3">
        <h2 className="font-medium text-sm text-gray-700">Contract Details</h2>
        <div className="grid grid-cols-4 gap-2">
          <Input placeholder="Contract ID" value={contract_id} onChange={(e: any) => setContractId(e.target.value)} />
          <Input placeholder="Customer" value={customer} onChange={(e: any) => setCustomer(e.target.value)} />
          <Input placeholder="Transaction Price" type="number" value={transaction_price} onChange={(e: any) => setTxnPrice(parseFloat(e.target.value || "0"))} />
          <Input placeholder="Default Start (YYYY-MM-DD)" value={default_start} onChange={(e: any) => setDefaultStart(e.target.value)} />
        </div>
      </Card>

      <Card className="p-4 space-y-3">
        <h2 className="font-medium text-sm text-gray-700">Line Items</h2>
        {items.map((item, idx) => (
          <div key={idx} className="grid grid-cols-3 gap-2">
            <Input placeholder="Product Code" value={item.product_code} onChange={(e: any) => updateItem(idx, "product_code", e.target.value)} />
            <Input placeholder="Amount" type="number" value={item.amount} onChange={(e: any) => updateItem(idx, "amount", e.target.value)} />
            <Button onClick={() => setItems(items.filter((_, i) => i !== idx))}>Remove</Button>
          </div>
        ))}
        <Button onClick={() => setItems([...items, { product_code: "", amount: 0 }])}>+ Add Line</Button>
      </Card>

      <Card className="p-4 space-y-3">
        <h2 className="font-medium text-sm text-gray-700">Contract Text (for AI)</h2>
        <textarea
          className="border rounded p-2 w-full h-32 text-sm"
          placeholder="Paste OCR / parsed contract text here..."
          value={contractText}
          onChange={(e) => setContractText(e.target.value)}
        />
      </Card>

      <div className="flex gap-2">
        <Button onClick={allocate}>Allocate</Button>
        <Button onClick={aiGenerate}>AI Generate Schedule</Button>
      </div>

      {allocResult && (
        <Card className="p-4">
          <h2 className="font-medium text-sm text-gray-700 mb-2">Allocation Result</h2>
          <pre className="text-xs bg-slate-50 p-3 rounded border overflow-x-auto">{JSON.stringify(allocResult, null, 2)}</pre>
        </Card>
      )}
    </div>
  );
}
