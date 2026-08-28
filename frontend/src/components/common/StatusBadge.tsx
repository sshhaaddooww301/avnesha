import React from "react";
import { ThreatStatus } from "@/lib/types";

interface StatusBadgeProps {
  status: ThreatStatus | string;
  className?: string;
}

export function StatusBadge({ status, className = "" }: StatusBadgeProps) {
  const st = (status || "").toLowerCase();

  const configs: Record<string, { bg: string; text: string; border: string }> = {
    open: {
      bg: "bg-zinc-900",
      text: "text-zinc-200",
      border: "border-zinc-700/70",
    },
    investigating: {
      bg: "bg-zinc-900",
      text: "text-amber-300",
      border: "border-zinc-700/70",
    },
    resolved: {
      bg: "bg-zinc-900",
      text: "text-emerald-400",
      border: "border-zinc-700/70",
    },
    false_positive: {
      bg: "bg-zinc-950",
      text: "text-zinc-500",
      border: "border-zinc-800",
    },
  };

  const config = configs[st] || {
    bg: "bg-zinc-900",
    text: "text-zinc-400",
    border: "border-zinc-800",
  };

  const label = st.replace("_", " ");

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-wider border ${config.bg} ${config.text} ${config.border} ${className}`}
    >
      {label}
    </span>
  );
}
