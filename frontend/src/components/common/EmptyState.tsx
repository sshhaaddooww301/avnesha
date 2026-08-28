import React from "react";
import { ShieldAlert, Database, Radio, CheckCircle2 } from "lucide-react";

interface EmptyStateProps {
  icon?: "shield" | "database" | "radio" | "check";
  title?: string;
  message?: string;
  action?: React.ReactNode;
}

export function EmptyState({
  icon = "shield",
  title = "No Data Available",
  message = "No security events or alerts match the current query.",
  action,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center bg-card/40 rounded-lg border border-border/50 min-h-[160px]">
      <div className="p-3 bg-cyber-dark rounded-full border border-border/60 text-gray-400 mb-3">
        {icon === "shield" && <ShieldAlert className="w-6 h-6 text-gray-500" />}
        {icon === "database" && <Database className="w-6 h-6 text-gray-500" />}
        {icon === "radio" && <Radio className="w-6 h-6 text-cyan-500 animate-pulse" />}
        {icon === "check" && <CheckCircle2 className="w-6 h-6 text-emerald-500" />}
      </div>
      <h3 className="text-sm font-semibold text-gray-300">{title}</h3>
      <p className="text-xs text-gray-500 mt-1 max-w-sm">{message}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
