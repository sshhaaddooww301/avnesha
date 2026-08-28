"use client";

import React from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from "recharts";
import { PieChart as PieIcon } from "lucide-react";
import { SeverityDistribution as SevDistType } from "@/lib/types";
import { EmptyState } from "../common/EmptyState";

interface SeverityDistributionProps {
  data: SevDistType[];
  loading?: boolean;
}

const COLORS: Record<string, string> = {
  critical: "#ef4444",
  high: "#f97316",
  medium: "#d4d4d8",
  low: "#52525b",
};

export function SeverityDistribution({ data, loading = false }: SeverityDistributionProps) {
  const hasData = data && data.length > 0 && data.some((d) => d.count > 0);

  return (
    <div className="bg-card rounded-xl border border-border p-5 shadow-card flex flex-col h-full">
      <div className="flex items-center justify-between pb-4 border-b border-border">
        <div className="flex items-center gap-2">
          <PieIcon className="w-4 h-4 text-zinc-400" />
          <h3 className="text-xs font-semibold text-white tracking-wider uppercase font-mono">
            Severity Ratios
          </h3>
        </div>
        <span className="text-[10px] font-mono text-zinc-500 uppercase">Exact DB %</span>
      </div>

      <div className="mt-4 flex-1 min-h-[220px]">
        {loading ? (
          <div className="h-full flex items-center justify-center text-xs font-mono text-zinc-500">
            Calculating severity breakdown...
          </div>
        ) : !hasData ? (
          <EmptyState
            icon="database"
            title="No Threat Distribution"
            message="No alerts in the database to calculate severity ratios."
          />
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={55}
                outerRadius={80}
                paddingAngle={3}
                dataKey="count"
                nameKey="severity"
                stroke="#09090b"
                strokeWidth={2}
              >
                {data.map((entry) => (
                  <Cell
                    key={`cell-${entry.severity}`}
                    fill={COLORS[entry.severity.toLowerCase()] || "#71717a"}
                  />
                ))}
              </Pie>
              <Tooltip
                formatter={(value: any, name: any, props: any) => [
                  `${value} alerts (${props.payload.percentage}%)`,
                  String(name).toUpperCase(),
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
              <Legend
                formatter={(val) => <span className="text-xs text-zinc-300 font-mono capitalize">{val}</span>}
                wrapperStyle={{ fontSize: "11px", paddingTop: "6px" }}
              />
            </PieChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
