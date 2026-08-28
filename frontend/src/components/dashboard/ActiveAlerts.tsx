"use client";

import React from "react";
import Link from "next/link";
import { ExternalLink, AlertTriangle } from "lucide-react";
import { SeverityBadge } from "../common/SeverityBadge";
import { StatusBadge } from "../common/StatusBadge";
import { EmptyState } from "../common/EmptyState";
import { formatDateTime } from "@/lib/utils";

interface ActiveAlertsProps {
  threats: any[];
  loading?: boolean;
}

export function ActiveAlerts({ threats, loading = false }: ActiveAlertsProps) {
  return (
    <div className="bg-card rounded-xl border border-border p-5 shadow-card flex flex-col h-full">
      <div className="flex items-center justify-between pb-4 border-b border-border">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-zinc-400" />
          <h3 className="text-xs font-semibold text-white tracking-wider uppercase font-mono">
            Active Security Incidents
          </h3>
        </div>
        <Link
          href="/threats"
          className="text-xs text-zinc-400 hover:text-white flex items-center gap-1 font-mono transition-colors"
        >
          <span>View All ({threats.length})</span>
          <ExternalLink className="w-3 h-3" />
        </Link>
      </div>

      <div className="mt-4 flex-1 overflow-x-auto">
        {loading ? (
          <div className="py-12 text-center text-xs text-zinc-500 font-mono">
            Querying PostgreSQL threats table...
          </div>
        ) : threats.length === 0 ? (
          <EmptyState
            icon="shield"
            title="No Active Threats"
            message="No security alerts currently recorded in database."
          />
        ) : (
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-border text-zinc-500 font-mono uppercase text-[10px]">
                <th className="pb-2.5 font-medium">Time</th>
                <th className="pb-2.5 font-medium">Alert Type</th>
                <th className="pb-2.5 font-medium">Severity</th>
                <th className="pb-2.5 font-medium">Source Node</th>
                <th className="pb-2.5 font-medium">Risk Score</th>
                <th className="pb-2.5 font-medium">Rule</th>
                <th className="pb-2.5 font-medium">Status</th>
                <th className="pb-2.5 text-right font-medium">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60 font-mono">
              {threats.slice(0, 7).map((t) => (
                <tr key={t.threat_id} className="hover:bg-card-hover/90 transition-colors">
                  <td className="py-3 text-zinc-400 text-[11px] whitespace-nowrap">
                    {formatDateTime(t.detected_at)}
                  </td>
                  <td className="py-3 font-sans font-medium text-white whitespace-nowrap">
                    {t.threat_type}
                  </td>
                  <td className="py-3 whitespace-nowrap">
                    <SeverityBadge severity={t.severity} />
                  </td>
                  <td className="py-3 text-zinc-400 text-[11px] whitespace-nowrap">
                    {t.source_node || t.session_id || "--"}
                  </td>
                  <td className="py-3 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <span
                        className={`font-bold ${
                          t.risk_score >= 75
                            ? "text-red-400"
                            : t.risk_score >= 50
                            ? "text-orange-400"
                            : t.risk_score >= 25
                            ? "text-amber-300"
                            : "text-zinc-300"
                        }`}
                      >
                        {t.risk_score}
                      </span>
                      <div className="w-12 h-1 bg-zinc-800 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${
                            t.risk_score >= 75
                              ? "bg-red-500"
                              : t.risk_score >= 50
                              ? "bg-orange-500"
                              : t.risk_score >= 25
                              ? "bg-amber-400"
                              : "bg-zinc-400"
                          }`}
                          style={{ width: `${Math.min(t.risk_score, 100)}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="py-3 text-zinc-400 text-[11px] whitespace-nowrap">
                    {t.detection_rule}
                  </td>
                  <td className="py-3 whitespace-nowrap">
                    <StatusBadge status={t.status} />
                  </td>
                  <td className="py-3 text-right whitespace-nowrap">
                    <Link
                      href={`/threats/${t.threat_id}`}
                      className="px-2.5 py-1 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-zinc-200 hover:text-white text-[11px] transition-colors"
                    >
                      Investigate
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
