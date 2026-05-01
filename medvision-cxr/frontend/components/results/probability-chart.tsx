"use client";

import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { LabelProbability } from "@/types";

export function ProbabilityChart({ items }: { items: LabelProbability[] }) {
  return (
    <div className="h-[320px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={items} layout="vertical" margin={{ top: 8, right: 20, left: 30, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#d7e1dc" />
          <XAxis type="number" domain={[0, 1]} tickFormatter={(value) => `${Math.round(value * 100)}%`} stroke="#55717b" />
          <YAxis type="category" dataKey="label" width={150} tick={{ fill: "#14303a", fontSize: 12 }} stroke="#55717b" />
          <Tooltip formatter={(value: number) => `${Math.round(value * 100)}%`} />
          <Bar dataKey="risk_probability" radius={[0, 10, 10, 0]}>
            {items.map((item) => (
              <Cell key={item.label} fill={item.risk_flag ? "#f28a58" : "#0d5c63"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
