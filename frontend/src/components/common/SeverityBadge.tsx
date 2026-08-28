import React from "react";
import { Severity } from "@/lib/types";

interface SeverityBadgeProps {
  severity: Severity | string;
  className?: string;
  showDot?: boolean;
}

export function SeverityBadge({ severity, className = "", showDot = true }: SeverityBadgeProps) {
  const sev = (severity || "").toLowerCase();

  const configs: Record<string, { bg: string; text: string; border: string; dot: string }> = {
    critical: {
      bg: "bg-red-950/40",
      text: "text-red-300",
      border: "border-red-800/40",
      dot: "bg-red-500 shadow-[0_0_6px_rgba(239,68,68,0.8)]",
    },
    high: {
      bg: "bg-orange-950/40",
      text: "text-orange-300",
      border: "border-orange-800/40",
      dot: "bg-orange-400",
    },
    medium: {
      bg: "bg-amber-950/30",
      text: "text-amber-300",
      border: "border-amber-800/40",
      dot: "bg-amber-400",
    },
    low: {
      bg: "bg-zinc-800/50",
      text: "text-zinc-300",
      border: "border-zinc-700/60",
      dot: "bg-zinc-400",
    },
  };

  const config = configs[sev] || {
    bg: "bg-zinc-900/60",
    text: "text-zinc-400",
    border: "border-zinc-800",
    dot: "bg-zinc-500",
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono font-medium uppercase tracking-wider border ${config.bg} ${config.text} ${config.border} ${className}`}
    >
      {showDot && <span className={`w-1.5 h-1.5 rounded-full ${config.dot}`} />}
      {severity}
    </span>
  );
}
