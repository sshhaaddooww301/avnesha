"use client";

import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { Zap } from "lucide-react";
import { TopOffense } from "@/lib/types";
import { EmptyState } from "../common/EmptyState";

interface TopOffensesProps {
  data: TopOffense[];
  loading?: boolean;
}

const BAR_COLORS = ["#ef4444", "#f97316", "#e4e4e7", "#a1a1aa", "#71717a"];

export function TopOffenses({ data, loading = false }: TopOffensesProps) {
  const hasData = data && data.length > 0;

  return (
    <div className="bg-card rounded-xl border border-border p-5 shadow-card flex flex-col h-full">
      <div className="flex items-center justify-between pb-4 border-b border-border">
        <div className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-zinc-400" />
          <h3 className="text-xs font-semibold text-white tracking-wider uppercase font-mono">
            Top Offense Signatures
          </h3>
        </div>
        <span className="text-[10px] font-mono text-zinc-500 uppercase">Ranked</span>
      </div>

      <div className="mt-4 flex-1 min-h-[220px]">
        {loading ? (
          <div className="h-full flex items-center justify-center text-xs font-mono text-zinc-500">
            Querying offensive patterns from database...
          </div>
        ) : !hasData ? (
          <EmptyState
            icon="shield"
            title="No Threat Offenses"
            message="No threat classifications recorded in database."
          />
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={data}
              layout="vertical"
              margin={{ top: 5, right: 30, left: 40, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="2 2" stroke="#1f1f24" horizontal={false} />
              <XAxis type="number" stroke="#52525b" tick={{ fontSize: 10 }} allowDecimals={false} />
              <YAxis
                dataKey="threat_type"
                type="category"
                stroke="#a1a1aa"
                tick={{ fontSize: 10, width: 120 }}
                width={120}
              />
              <Tooltip
                formatter={(val: any, name: any, props: any) => [
                  `${val} incidents (${props.payload.percentage}%)`,
                  "Count",
                ]}
                contentStyle={{
                  backgroundColor: "#121216",
                  borderColor: "#27272a",
                  borderRadius: "8px",
                  fontSize: "12px",
                  fontFamily: "monospace",
                  color: "#f4f4f5",
                  boxShadow: "0 8px 30px rgba(0,0,0,0.5)",
                }}
              />
              <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                {data.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={BAR_COLORS[index % BAR_COLORS.length]}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
