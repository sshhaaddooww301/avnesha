"use client";

import React from "react";
import { ShieldAlert, AlertTriangle, AlertCircle, CheckCircle2 } from "lucide-react";
import { DashboardSummary } from "@/lib/types";

interface AlertCardsProps {
  summary: DashboardSummary | null;
  loading?: boolean;
}

export function AlertCards({ summary, loading = false }: AlertCardsProps) {
  const cards = [
    {
      title: "Critical Threats",
      count: summary?.critical_count ?? 0,
      icon: ShieldAlert,
      textColor: "text-red-400",
      accentBorder: "hover:border-red-900/80",
      badge: "Tier 1 Priority",
      badgeColor: "bg-red-950/50 text-red-400 border-red-900/60",
      iconBg: "bg-zinc-900 text-red-400 border border-zinc-800",
    },
    {
      title: "High Severity",
      count: summary?.high_count ?? 0,
      icon: AlertTriangle,
      textColor: "text-orange-400",
      accentBorder: "hover:border-orange-900/80",
      badge: "High Risk",
      badgeColor: "bg-orange-950/50 text-orange-400 border-orange-900/60",
      iconBg: "bg-zinc-900 text-orange-400 border border-zinc-800",
    },
    {
      title: "Medium Severity",
      count: summary?.medium_count ?? 0,
      icon: AlertCircle,
      textColor: "text-amber-300",
      accentBorder: "hover:border-amber-900/80",
      badge: "Under Review",
      badgeColor: "bg-amber-950/40 text-amber-300 border-amber-900/60",
      iconBg: "bg-zinc-900 text-amber-400 border border-zinc-800",
    },
    {
      title: "Low / Monitored",
      count: summary?.low_count ?? 0,
      icon: CheckCircle2,
      textColor: "text-zinc-300",
      accentBorder: "hover:border-zinc-700",
      badge: "Standard",
      badgeColor: "bg-zinc-900 text-zinc-400 border-zinc-800",
      iconBg: "bg-zinc-900 text-zinc-300 border border-zinc-800",
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, i) => {
        const Icon = card.icon;
        return (
          <div
            key={i}
            className={`relative overflow-hidden p-5 rounded-xl bg-card border border-border ${card.accentBorder} shadow-card transition-all duration-300 hover:bg-card-hover group`}
          >
            <div className="flex items-start justify-between">
              <div>
                <span className={`text-[10px] uppercase font-mono tracking-wider px-2 py-0.5 rounded border ${card.badgeColor}`}>
                  {card.badge}
                </span>
                <h4 className="text-xs font-medium text-zinc-400 mt-2.5">{card.title}</h4>
              </div>
              <div className={`p-2.5 rounded-lg ${card.iconBg} shadow-inner`}>
                <Icon className="w-4 h-4" />
              </div>
            </div>

            <div className="mt-4 flex items-baseline justify-between">
              <span className={`text-3xl font-bold tracking-tight font-mono ${card.textColor}`}>
                {loading ? "..." : card.count}
              </span>
              <span className="text-[11px] font-mono text-zinc-500">
                {summary && summary.total_threats > 0
                  ? `${((card.count / summary.total_threats) * 100).toFixed(0)}% of total`
                  : "0%"}
              </span>
            </div>

            <div className="mt-3 pt-2.5 border-t border-border/70 flex items-center justify-between text-[10px] text-zinc-500 font-mono">
              <span>PostgreSQL Count</span>
              <span className="text-zinc-400 font-bold group-hover:text-white transition-colors">
                {card.count > 0 ? "RECORDED" : "CLEAR"}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
