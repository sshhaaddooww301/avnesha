"use client";

import React, { useState } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { Activity } from "lucide-react";
import { TimelinePoint } from "@/lib/types";
import { EmptyState } from "../common/EmptyState";

interface AlertsOverTimeProps {
  data: TimelinePoint[];
  loading?: boolean;
  onRangeChange?: (range: string) => void;
}

export function AlertsOverTime({ data, loading = false, onRangeChange }: AlertsOverTimeProps) {
  const [activeRange, setActiveRange] = useState<string>("24h");

  const ranges = ["1h", "6h", "24h", "7d", "30d"];

  const handleSelect = (r: string) => {
    setActiveRange(r);
    if (onRangeChange) onRangeChange(r);
  };

  const hasData = data && data.length > 0 && data.some((d) => d.count > 0);

  return (
    <div className="bg-card rounded-xl border border-border p-5 shadow-card flex flex-col h-full">
      <div className="flex flex-wrap items-center justify-between gap-2 pb-4 border-b border-border">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-zinc-400" />
          <h3 className="text-xs font-semibold text-white tracking-wider uppercase font-mono">
            Alerts Over Time
          </h3>
        </div>

        {/* Range Selector */}
        <div className="flex items-center bg-zinc-900 rounded-lg p-0.5 border border-zinc-800">
          {ranges.map((r) => (
            <button
              key={r}
              onClick={() => handleSelect(r)}
              className={`px-2.5 py-1 rounded text-[10px] font-mono transition-colors ${
                activeRange === r
                  ? "bg-zinc-800 text-white font-bold border border-zinc-700 shadow-sm"
                  : "text-zinc-500 hover:text-zinc-300"
              }`}
            >
              {r}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-4 flex-1 min-h-[240px]">
        {loading ? (
          <div className="h-full flex items-center justify-center text-xs font-mono text-zinc-500">
            Calculating time series from PostgreSQL...
          </div>
        ) : !hasData ? (
          <EmptyState
            icon="database"
            title="No Time-Series Events"
            message={`No alerts recorded in the selected ${activeRange} window.`}
          />
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="colorCritical" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.7} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="colorHigh" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f97316" stopOpacity={0.6} />
                  <stop offset="95%" stopColor="#f97316" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="colorMedium" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#d4d4d8" stopOpacity={0.5} />
                  <stop offset="95%" stopColor="#d4d4d8" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="colorLow" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#71717a" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#71717a" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="2 2" stroke="#1f1f24" />
              <XAxis dataKey="timestamp" stroke="#52525b" tick={{ fontSize: 10 }} />
              <YAxis stroke="#52525b" tick={{ fontSize: 10 }} allowDecimals={false} />
              <Tooltip
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
              <Legend wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }} />
              <Area
                type="monotone"
                dataKey="critical"
                name="Critical"
                stroke="#ef4444"
                strokeWidth={1.5}
                fillOpacity={1}
                fill="url(#colorCritical)"
                stackId="1"
              />
              <Area
                type="monotone"
                dataKey="high"
                name="High"
                stroke="#f97316"
                strokeWidth={1.5}
                fillOpacity={1}
                fill="url(#colorHigh)"
                stackId="1"
              />
              <Area
                type="monotone"
                dataKey="medium"
                name="Medium"
                stroke="#d4d4d8"
                strokeWidth={1.5}
                fillOpacity={1}
                fill="url(#colorMedium)"
                stackId="1"
              />
              <Area
                type="monotone"
                dataKey="low"
                name="Low"
                stroke="#71717a"
                strokeWidth={1.5}
                fillOpacity={1}
                fill="url(#colorLow)"
                stackId="1"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
