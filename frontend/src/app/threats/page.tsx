"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { Navbar } from "@/components/layout/Navbar";
import { SeverityBadge } from "@/components/common/SeverityBadge";
import { StatusBadge } from "@/components/common/StatusBadge";
import { EmptyState } from "@/components/common/EmptyState";
import { api } from "@/lib/api";
import { Threat } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";
import {
  Search,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
} from "lucide-react";

export default function ThreatsPage() {
  const [threats, setThreats] = useState<Threat[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState("");
  const [severity, setSeverity] = useState("");
  const [status, setStatus] = useState("");
  const [threatType, setThreatType] = useState("");

  const fetchThreats = useCallback(async () => {
    try {
      setLoading(true);
      const params: Record<string, any> = {
        page,
        page_size: 15,
        sort_by: "detected_at",
        sort_order: "desc",
      };
      if (search) params.search = search;
      if (severity) params.severity = severity;
      if (status) params.status = status;
      if (threatType) params.threat_type = threatType;

      const res = await api.getThreats(params);
      setThreats(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (err) {
      console.error("Failed to fetch threats:", err);
    } finally {
      setLoading(false);
    }
  }, [page, search, severity, status, threatType]);

  useEffect(() => {
    fetchThreats();
  }, [fetchThreats]);

  return (
    <div className="min-h-screen flex flex-col bg-background text-zinc-200">
      <Navbar />

      <main className="flex-1 max-w-[1720px] w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        {/* Page Header */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-lg font-bold text-white tracking-wide uppercase font-mono">
              Threats & Incident Management
            </h1>
            <p className="text-xs text-zinc-400 font-mono mt-0.5">
              Active security threats detected by deterministic quantum rules and multi-factor engines
            </p>
          </div>
          <button
            onClick={fetchThreats}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-card hover:bg-card-hover border border-border text-xs font-mono text-zinc-300"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-zinc-400" : ""}`} />
            <span>Refresh</span>
          </button>
        </div>

        {/* Filter Toolbar */}
        <div className="p-4 rounded-xl bg-card border border-border shadow-card grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-zinc-500 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search Threat ID, Rule..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="w-full pl-9 pr-3 py-2 bg-zinc-950 rounded-lg border border-border text-xs text-zinc-200 placeholder-zinc-500 font-mono focus:border-zinc-500 focus:outline-none"
            />
          </div>

          <div>
            <select
              value={severity}
              onChange={(e) => {
                setSeverity(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 bg-zinc-950 rounded-lg border border-border text-xs text-zinc-300 font-mono focus:border-zinc-500 focus:outline-none"
            >
              <option value="">All Severities</option>
              <option value="critical">Critical (Score 75-100)</option>
              <option value="high">High (Score 50-74)</option>
              <option value="medium">Medium (Score 25-49)</option>
              <option value="low">Low (Score 0-24)</option>
            </select>
          </div>

          <div>
            <select
              value={status}
              onChange={(e) => {
                setStatus(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 bg-zinc-950 rounded-lg border border-border text-xs text-zinc-300 font-mono focus:border-zinc-500 focus:outline-none"
            >
              <option value="">All Statuses</option>
              <option value="open">Open</option>
              <option value="investigating">Under Investigation</option>
              <option value="resolved">Resolved</option>
              <option value="false_positive">False Positive</option>
            </select>
          </div>

          <div>
            <select
              value={threatType}
              onChange={(e) => {
                setThreatType(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 bg-zinc-950 rounded-lg border border-border text-xs text-zinc-300 font-mono focus:border-zinc-500 focus:outline-none"
            >
              <option value="">All Threat Types</option>
              <option value="Replay Attack">Replay Attack</option>
              <option value="MITM Attack">MITM / Channel Attack</option>
              <option value="Forgery">Signature Forgery</option>
              <option value="Impersonation">Identity Impersonation</option>
              <option value="Quantum Measurement Anomaly">Quantum Measurement Anomaly</option>
            </select>
          </div>

          <div>
            <button
              onClick={() => {
                setSearch("");
                setSeverity("");
                setStatus("");
                setThreatType("");
                setPage(1);
              }}
              className="w-full py-2 bg-zinc-950 hover:bg-zinc-900 rounded-lg border border-border text-xs text-zinc-400 hover:text-zinc-200 font-mono transition-colors"
            >
              Reset Filters
            </button>
          </div>
        </div>

        {/* Threats Table */}
        <div className="bg-card rounded-xl border border-border p-5 shadow-card flex flex-col">
          <div className="overflow-x-auto">
            {loading ? (
              <div className="py-16 text-center text-xs font-mono text-zinc-500">
                Fetching active threat alerts from database...
              </div>
            ) : threats.length === 0 ? (
              <EmptyState
                icon="shield"
                title="No Threats Found"
                message="No threats match the specified severity and status criteria."
              />
            ) : (
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-border text-zinc-500 uppercase text-[10px]">
                    <th className="pb-3 font-medium">Detection Time</th>
                    <th className="pb-3 font-medium">Threat ID</th>
                    <th className="pb-3 font-medium">Classification</th>
                    <th className="pb-3 font-medium">Severity</th>
                    <th className="pb-3 font-medium">Risk Score</th>
                    <th className="pb-3 font-medium">Detection Rule</th>
                    <th className="pb-3 font-medium">Confidence</th>
                    <th className="pb-3 font-medium">Source</th>
                    <th className="pb-3 font-medium">Status</th>
                    <th className="pb-3 text-right font-medium">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {threats.map((t) => (
                    <tr key={t.threat_id} className="hover:bg-card-hover/90 transition-colors">
                      <td className="py-3 text-zinc-400 whitespace-nowrap text-[11px]">
                        {formatDateTime(t.detected_at)}
                      </td>
                      <td className="py-3 text-zinc-300 whitespace-nowrap">{t.threat_id.slice(0, 8)}...</td>
                      <td className="py-3 font-sans font-medium text-white whitespace-nowrap">{t.threat_type}</td>
                      <td className="py-3 whitespace-nowrap">
                        <SeverityBadge severity={t.severity} />
                      </td>
                      <td className="py-3 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <span
                            className={`font-bold ${
                              t.risk_score >= 75
                                ? "text-red-400"
                                : t.risk_score >= 50
                                ? "text-orange-400"
                                : "text-amber-300"
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
                                  : "bg-amber-400"
                              }`}
                              style={{ width: `${Math.min(t.risk_score, 100)}%` }}
                            />
                          </div>
                        </div>
                      </td>
                      <td className="py-3 text-zinc-300 whitespace-nowrap">{t.detection_rule}</td>
                      <td className="py-3 text-zinc-400 whitespace-nowrap">
                        {(t.confidence * 100).toFixed(0)}%
                      </td>
                      <td className="py-3 text-zinc-400 whitespace-nowrap text-[11px]">
                        {t.source_node || t.session_id || "--"}
                      </td>
                      <td className="py-3 whitespace-nowrap">
                        <StatusBadge status={t.status} />
                      </td>
                      <td className="py-3 text-right whitespace-nowrap">
                        <Link
                          href={`/threats/${t.threat_id}`}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-zinc-200 hover:text-white text-[11px] transition-colors"
                        >
                          <span>Investigate</span>
                          <ExternalLink className="w-3 h-3" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {/* Pagination Footer */}
          {total > 0 && (
            <div className="mt-4 pt-4 border-t border-border flex items-center justify-between text-xs font-mono text-zinc-400">
              <span>
                Page <strong className="text-white">{page}</strong> of{" "}
                <strong className="text-white">{totalPages}</strong> ({total} threats total)
              </span>
              <div className="flex items-center gap-2">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="px-2.5 py-1 rounded bg-zinc-900 border border-border disabled:opacity-40 hover:bg-zinc-850 text-zinc-200"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  className="px-2.5 py-1 rounded bg-zinc-900 border border-border disabled:opacity-40 hover:bg-zinc-850 text-zinc-200"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
