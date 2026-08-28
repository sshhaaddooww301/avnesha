"use client";

import React from "react";
import Link from "next/link";
import { ShieldAlert, ChevronRight, Clock } from "lucide-react";
import { SeverityBadge } from "../common/SeverityBadge";
import { EmptyState } from "../common/EmptyState";
import { formatDateTime } from "@/lib/utils";

interface RecentIncidentsProps {
  incidents: any[];
  loading?: boolean;
}

export function RecentIncidents({ incidents, loading = false }: RecentIncidentsProps) {
  return (
    <div className="bg-card rounded-xl border border-border p-5 shadow-card flex flex-col h-full">
      <div className="flex items-center justify-between pb-4 border-b border-border">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-zinc-400" />
          <h3 className="text-xs font-semibold text-white tracking-wider uppercase font-mono">
            Incident Queue
          </h3>
        </div>
        <span className="text-[10px] font-mono text-zinc-500 uppercase">Live Buffer</span>
      </div>

      <div className="mt-4 flex-1 overflow-y-auto max-h-[280px] pr-1 space-y-2">
        {loading ? (
          <div className="py-8 text-center text-xs font-mono text-zinc-500">Loading incident feed...</div>
        ) : incidents.length === 0 ? (
          <EmptyState
            icon="check"
            title="No Recent Incidents"
            message="No security incidents currently flagged in database."
          />
        ) : (
          incidents.map((inc) => (
            <Link
              key={inc.threat_id}
              href={`/threats/${inc.threat_id}`}
              className="group block p-3 rounded-lg bg-zinc-950/70 hover:bg-zinc-900 border border-border hover:border-zinc-700 transition-all"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-white group-hover:text-zinc-200 transition-colors">
                  {inc.threat_type}
                </span>
                <SeverityBadge severity={inc.severity} />
              </div>

              <div className="mt-2 flex items-center justify-between text-[11px] font-mono text-zinc-400">
                <div className="flex items-center gap-1.5 text-zinc-500">
                  <Clock className="w-3 h-3" />
                  <span>{formatDateTime(inc.detected_at)}</span>
                </div>
                <div className="flex items-center gap-1">
                  <span className="text-zinc-500">Risk:</span>
                  <span
                    className={`font-bold ${
                      inc.risk_score >= 75
                        ? "text-red-400"
                        : inc.risk_score >= 50
                        ? "text-orange-400"
                        : "text-amber-300"
                    }`}
                  >
                    {inc.risk_score}
                  </span>
                </div>
              </div>

              <div className="mt-1.5 flex items-center justify-between text-[10px] text-zinc-500 font-mono">
                <span className="truncate max-w-[180px]">{inc.source_node || inc.session_id}</span>
                <span className="text-zinc-400 group-hover:translate-x-0.5 transition-transform flex items-center gap-0.5">
                  Inspect <ChevronRight className="w-3 h-3" />
                </span>
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}
