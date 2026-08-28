"use client";

import React from "react";
import Link from "next/link";
import { Terminal, CheckCircle, XCircle, ChevronRight } from "lucide-react";
import { EmptyState } from "../common/EmptyState";
import { formatDateTime, formatPercent } from "@/lib/utils";

interface LogTimelineProps {
  logs: any[];
  loading?: boolean;
}

export function LogTimeline({ logs, loading = false }: LogTimelineProps) {
  return (
    <div className="bg-card rounded-xl border border-border p-5 shadow-card flex flex-col h-full">
      <div className="flex items-center justify-between pb-4 border-b border-border">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-zinc-400" />
          <h3 className="text-xs font-semibold text-white tracking-wider uppercase font-mono">
            QDS Verification Telemetry Stream
          </h3>
        </div>
        <Link
          href="/logs"
          className="text-xs text-zinc-400 hover:text-white font-mono flex items-center gap-1 transition-colors"
        >
          <span>All Telemetry</span>
          <ChevronRight className="w-3 h-3" />
        </Link>
      </div>

      <div className="mt-4 flex-1 overflow-y-auto max-h-[280px] font-mono text-xs divide-y divide-border/60">
        {loading ? (
          <div className="py-8 text-center text-zinc-500">Streaming telemetry from PostgreSQL...</div>
        ) : logs.length === 0 ? (
          <EmptyState
            icon="radio"
            title="No Security Events Available"
            message="No QDS measurement or verification events recorded yet."
          />
        ) : (
          logs.map((log) => (
            <div
              key={log.event_id}
              className="py-2.5 px-2 hover:bg-card-hover/90 rounded transition-colors flex items-center justify-between gap-3"
            >
              <div className="flex items-center gap-3 min-w-0">
                {log.verification_result === true ? (
                  <CheckCircle className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                ) : log.verification_result === false ? (
                  <XCircle className="w-3.5 h-3.5 text-red-400 shrink-0" />
                ) : (
                  <span className="w-1.5 h-1.5 rounded-full bg-zinc-500 shrink-0" />
                )}

                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-zinc-100 font-medium truncate">{log.event_type}</span>
                    <span className="text-[10px] text-zinc-500">[{log.source_node}]</span>
                  </div>
                  <div className="text-[10px] text-zinc-500 truncate">
                    Session: {log.session_id} | Deviation:{" "}
                    {log.measurement_deviation !== null
                      ? formatPercent(log.measurement_deviation * 100)
                      : "0.0%"}
                  </div>
                </div>
              </div>

              <div className="text-right shrink-0">
                <span className="text-[10px] text-zinc-500 block">
                  {formatDateTime(log.timestamp)}
                </span>
                {log.has_threats && (
                  <span className="text-[9px] uppercase px-1.5 py-0.2 rounded bg-red-950/70 border border-red-800/80 text-red-400 font-bold">
                    FLAGGED
                  </span>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
