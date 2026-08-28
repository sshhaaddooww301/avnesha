"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Navbar } from "@/components/layout/Navbar";
import { api } from "@/lib/api";
import { ReportSummary } from "@/lib/types";
import {
  Download,
  Activity,
  Lock,
  RefreshCw,
  FileText,
} from "lucide-react";

export default function ReportsPage() {
  const [report, setReport] = useState<ReportSummary | null>(null);
  const [days, setDays] = useState<number>(30);
  const [loading, setLoading] = useState(true);

  const fetchReport = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.getReportSummary(days);
      setReport(data);
    } catch (err) {
      console.error("Failed to load report summary:", err);
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => {
    fetchReport();
  }, [fetchReport]);

  const handleExport = (type: "threats" | "events" | "ledger") => {
    const url = api.getExportUrl(type);
    window.open(url, "_blank");
  };

  const handlePdfExport = () => {
    const url = api.getPdfExportUrl(days);
    window.open(url, "_blank");
  };

  return (
    <div className="min-h-screen flex flex-col bg-background text-zinc-200">
      <Navbar />

      <main className="flex-1 max-w-[1720px] w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        {/* Page Header */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-lg font-bold text-white tracking-wide uppercase font-mono">
              Cybersecurity Reports & Forensics
            </h1>
            <p className="text-xs text-zinc-400 font-mono mt-0.5">
              Statistical summaries and immutable audit evidence exported directly from PostgreSQL
            </p>
          </div>

          {/* Time Window Selector & Refresh */}
          <div className="flex items-center gap-3">
            <select
              value={days}
              onChange={(e) => setDays(parseInt(e.target.value))}
              className="px-3 py-1.5 bg-zinc-950 rounded-lg border border-border text-xs text-zinc-200 font-mono focus:border-zinc-500 focus:outline-none"
            >
              <option value={7}>Last 7 Days</option>
              <option value={14}>Last 14 Days</option>
              <option value={30}>Last 30 Days</option>
              <option value={90}>Last 90 Days</option>
            </select>

            <button
              onClick={fetchReport}
              className="p-1.5 rounded-lg bg-card hover:bg-card-hover border border-border text-zinc-300"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-zinc-400" : ""}`} />
            </button>
          </div>
        </div>

        {/* Export Card Bar (PDF & CSV) */}
        <div className="p-5 rounded-xl bg-card border border-border shadow-card flex flex-wrap items-center justify-between gap-4">
          <div>
            <h3 className="text-xs font-bold text-white uppercase font-mono tracking-wider">Export Forensic & Compliance Reports</h3>
            <p className="text-xs text-zinc-400 font-mono mt-0.5">
              Export comprehensive PDF assessment report or raw database records for compliance audits, SOC reviews, and forensics
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={handlePdfExport}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white hover:bg-zinc-100 text-zinc-950 text-xs font-mono font-bold shadow-md transition-colors"
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Download PDF Assessment</span>
            </button>
            <button
              onClick={() => handleExport("threats")}
              className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-zinc-200 text-xs font-mono transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Threats CSV</span>
            </button>
            <button
              onClick={() => handleExport("events")}
              className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-zinc-200 text-xs font-mono transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Events CSV</span>
            </button>
            <button
              onClick={() => handleExport("ledger")}
              className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-zinc-200 text-xs font-mono transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Audit Ledger CSV</span>
            </button>
          </div>
        </div>

        {/* Report Key Metric Tiles */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-5 rounded-xl bg-card border border-border shadow-card">
            <span className="text-zinc-400 text-[11px] font-mono uppercase">Total Ingested Events</span>
            <div className="text-3xl font-bold text-white font-mono mt-2">
              {loading ? "..." : report?.total_events ?? 0}
            </div>
            <span className="text-[10px] text-zinc-500 font-mono mt-1 block">In selected {days}-day period</span>
          </div>

          <div className="p-5 rounded-xl bg-card border border-border shadow-card">
            <span className="text-zinc-400 text-[11px] font-mono uppercase">Total Flagged Threats</span>
            <div className="text-3xl font-bold text-red-400 font-mono mt-2">
              {loading ? "..." : report?.total_threats ?? 0}
            </div>
            <span className="text-[10px] text-zinc-500 font-mono mt-1 block">
              {report && report.total_events > 0
                ? `${((report.total_threats / report.total_events) * 100).toFixed(1)}% alert rate`
                : "0%"}
            </span>
          </div>

          <div className="p-5 rounded-xl bg-card border border-border shadow-card">
            <span className="text-zinc-400 text-[11px] font-mono uppercase">Verification Success Rate</span>
            <div className="text-3xl font-bold text-emerald-400 font-mono mt-2">
              {loading
                ? "..."
                : report?.verification_success_rate !== null && report?.verification_success_rate !== undefined
                ? `${report.verification_success_rate}%`
                : "--"}
            </div>
            <span className="text-[10px] text-zinc-500 font-mono mt-1 block">
              {report?.verification_success_count ?? 0} passed / {report?.verification_failure_count ?? 0} failed
            </span>
          </div>

          <div className="p-5 rounded-xl bg-card border border-border shadow-card">
            <span className="text-zinc-400 text-[11px] font-mono uppercase">Ledger Integrity</span>
            <div className="text-3xl font-bold text-emerald-400 font-mono mt-2 flex items-center gap-2">
              <Lock className="w-6 h-6 text-emerald-400" />
              <span>{loading ? "..." : report?.ledger_integrity || "EMPTY"}</span>
            </div>
            <span className="text-[10px] text-zinc-500 font-mono mt-1 block">
              {report?.ledger_total_blocks ?? 0} verified blocks
            </span>
          </div>
        </div>

        {/* Quantum Measurement Statistical Breakdown */}
        {report?.measurement_stats && (
          <div className="p-5 rounded-xl bg-card border border-border shadow-card space-y-4">
            <div className="flex items-center gap-2 pb-3 border-b border-border">
              <Activity className="w-5 h-5 text-zinc-400" />
              <h3 className="text-xs font-semibold text-white tracking-wider uppercase font-mono">
                Statistical Aggregations (PostgreSQL Dynamic Calculations)
              </h3>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 font-mono text-xs text-center">
              <div className="p-3 bg-zinc-950/80 rounded-lg border border-border">
                <span className="text-zinc-500 block text-[10px]">SAMPLES</span>
                <span className="text-base font-bold text-white">{report.measurement_stats.sample_count}</span>
              </div>
              <div className="p-3 bg-zinc-950/80 rounded-lg border border-border">
                <span className="text-zinc-500 block text-[10px]">MEAN DEVIATION</span>
                <span className="text-base font-bold text-zinc-200">
                  {report.measurement_stats.mean_deviation_pct}%
                </span>
              </div>
              <div className="p-3 bg-zinc-950/80 rounded-lg border border-border">
                <span className="text-zinc-500 block text-[10px]">STD DEV (σ)</span>
                <span className="text-base font-bold text-white">
                  {report.measurement_stats.std_deviation_pct}%
                </span>
              </div>
              <div className="p-3 bg-zinc-950/80 rounded-lg border border-border">
                <span className="text-zinc-500 block text-[10px]">VARIANCE</span>
                <span className="text-base font-bold text-white">{report.measurement_stats.variance}</span>
              </div>
              <div className="p-3 bg-zinc-950/80 rounded-lg border border-border">
                <span className="text-zinc-500 block text-[10px]">MAX DEVIATION</span>
                <span className="text-base font-bold text-red-400">
                  {report.measurement_stats.max_deviation_pct}%
                </span>
              </div>
              <div className="p-3 bg-zinc-950/80 rounded-lg border border-border">
                <span className="text-zinc-500 block text-[10px]">MIN DEVIATION</span>
                <span className="text-base font-bold text-emerald-400">
                  {report.measurement_stats.min_deviation_pct}%
                </span>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
