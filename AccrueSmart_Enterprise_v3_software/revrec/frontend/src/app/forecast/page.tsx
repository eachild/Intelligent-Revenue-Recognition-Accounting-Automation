"use client";

import { useState } from "react";
import { api } from "../../lib/api";
import { Button, Card, Input } from "../../components/ui";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

export default function ForecastPage() {
  const [history] = useState<Record<string, number>>({
    "2024-01": 10000,
    "2024-02": 12000,
    "2024-03": 9000,
    "2024-04": 11000,
    "2024-05": 11500,
  });

  const [horizon, setHorizon] = useState(6);
  const [method, setMethod] = useState("exp_smooth");
  const [result, setResult] = useState<any>(null);

  async function run() {
    const res = await api("/forecast/revenue", {
      method: "POST",
      body: JSON.stringify({ history, horizon, method }),
    });
    setResult(res);
  }

  const data = result
    ? [
        ...Object.entries(result.fitted || {}).map(([k, v]) => ({
          month: k,
          recognized: v,
          forecast: null,
        })),
        ...Object.entries(result.forecast || {}).map(([k, v]) => ({
          month: k,
          recognized: null,
          forecast: v,
        })),
      ]
    : [];

  return (
    <div className="max-w-6xl mx-auto space-y-4">
      <h1 className="text-xl font-semibold">Revenue Forecast AI</h1>

      <Card className="grid grid-cols-1 md:grid-cols-4 gap-2">
        <Input
          type="number"
          value={String(horizon)}
          onChange={(e: any) => setHorizon(Number(e.target.value))}
          placeholder="Horizon (months)"
        />

        <select
          className="border rounded px-2 py-1"
          value={method}
          onChange={(e: any) => setMethod(e.target.value)}
        >
          <option value="exp_smooth">Exponential Smoothing</option>
          <option value="seasonal_ma">Seasonal MA</option>
        </select>

        <Button onClick={run}>Run Forecast</Button>
      </Card>

      {result && (
        <Card>
          <div style={{ width: "100%", height: 320 }}>
            <ResponsiveContainer>
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="recognized" name="Historical" />
                <Line
                  type="monotone"
                  dataKey="forecast"
                  name="Forecast"
                  strokeDasharray="5 5"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>
      )}
    </div>
  );
}
