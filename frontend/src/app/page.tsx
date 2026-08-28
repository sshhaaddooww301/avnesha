"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Navbar } from "@/components/layout/Navbar";
import { AlertCards } from "@/components/dashboard/AlertCards";
import { ActiveAlerts } from "@/components/dashboard/ActiveAlerts";
import { AlertsOverTime } from "@/components/dashboard/AlertsOverTime";
import { SeverityDistribution } from "@/components/dashboard/SeverityDistribution";
import { TopOffenses } from "@/components/dashboard/TopOffenses";
import { RecentIncidents } from "@/components/dashboard/RecentIncidents";
import { LogTimeline } from "@/components/dashboard/LogTimeline";
import { SimulatorModal } from "@/components/dashboard/SimulatorModal";
import { api } from "@/lib/api";
import { useWebSocket } from "@/hooks/useWebSocket";
import {
  DashboardSummary,
  TimelinePoint,
  SeverityDistribution as SevDistType,
  TopOffense,
} from "@/lib/types";
import { ShieldCheck, Atom } from "lucide-react";

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [timeline, setTimeline] = useState<TimelinePoint[]>([]);
  const [severityDist, setSeverityDist] = useState<SevDistType[]>([]);
  const [topOffenses, setTopOffenses] = useState<TopOffense[]>([]);
  const [recentIncidents, setRecentIncidents] = useState<any[]>([]);
  const [logTimeline, setLogTimeline] = useState<any[]>([]);
  const [threatsList, setThreatsList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [simModalOpen, setSimModalOpen] = useState(false);

  // Fetch all dashboard data from PostgreSQL
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [sum, tl, sev, top, inc, logs, thr] = await Promise.allSettled([
        api.getSummary(),
        api.getTimeline("24h"),
        api.getSeverityDistribution(),
        api.getTopOffenses(5),
        api.getRecentIncidents(8),
        api.getLogTimeline(15),
        api.getThreats({ page: 1, page_size: 10, status: "open" }),
      ]);

      if (sum.status === "fulfilled") setSummary(sum.value);
      if (tl.status === "fulfilled") setTimeline(tl.value);
      if (sev.status === "fulfilled") setSeverityDist(sev.value);
      if (top.status === "fulfilled") setTopOffenses(top.value);
      if (inc.status === "fulfilled") setRecentIncidents(inc.value);
      if (logs.status === "fulfilled") setLogTimeline(logs.value);
      if (thr.status === "fulfilled") setThreatsList(thr.value.items || []);
    } catch (err) {
      console.error("Failed to load dashboard data:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  // WebSocket for real-time detection events
  const { isConnected } = useWebSocket(
    useCallback(
      (msg: { type: string; data?: any }) => {
        if (msg.type === "new_event" || msg.type === "new_threat") {
          loadData();
        }
      },
      [loadData]
    )
  );

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleRangeChange = async (range: string) => {
    try {
      const data = await api.getTimeline(range);
      setTimeline(data);
    } catch (err) {
      console.error("Timeline range error:", err);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-background text-zinc-200">
      {/* Top SOC Navbar */}
      <Navbar
        wsConnected={isConnected}
        onRefresh={loadData}
        onRunSimulator={() => setSimModalOpen(true)}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-[1720px] w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        {/* SOC Sub-header / System Status Ribbon */}
        <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-card border border-border shadow-card">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2.5">
              <span className="w-2 h-2 rounded-full bg-zinc-400" />
              <span className="text-xs font-mono text-zinc-200 font-semibold tracking-wider uppercase">
                SOC THREAT POSTURE : ACTIVE
              </span>
            </div>
            <div className="hidden sm:flex items-center gap-5 text-xs font-mono text-zinc-400 border-l border-border pl-5">
              <span>
                Total Events:{" "}
                <strong className="text-white font-bold">{summary?.total_events ?? 0}</strong>
              </span>
              <span>
                Flagged Threats:{" "}
                <strong className="text-red-400 font-bold">{summary?.total_threats ?? 0}</strong>
              </span>
              <span>
                Verification Rate:{" "}
                <strong className="text-emerald-400 font-bold">
                  {summary?.verification_success_rate !== null && summary?.verification_success_rate !== undefined
                    ? `${summary.verification_success_rate}%`
                    : "--"}
                </strong>
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-zinc-950 border border-zinc-800 text-xs font-mono">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-zinc-500">Hash Ledger:</span>
              <span
                className={`font-bold ${
                  summary?.ledger_integrity === "VALID"
                    ? "text-emerald-400"
                    : summary?.ledger_integrity === "COMPROMISED"
                    ? "text-red-400"
                    : "text-zinc-400"
                }`}
              >
                {summary?.ledger_integrity || "CHECKING"}
              </span>
            </div>

            <button
              onClick={() => setSimModalOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-zinc-200 text-xs font-mono transition-colors"
            >
              <Atom className="w-3.5 h-3.5 text-zinc-400 animate-spin-slow" />
              <span>Simulate Attack</span>
            </button>
          </div>
        </div>

        {/* Row 1: Alert Summary Cards */}
        <AlertCards summary={summary} loading={loading} />

        {/* Row 2: Active Alerts Table (Left 7 cols) & Alerts Over Time Chart (Right 5 cols) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-7">
            <ActiveAlerts threats={threatsList} loading={loading} />
          </div>
          <div className="lg:col-span-5">
            <AlertsOverTime
              data={timeline}
              loading={loading}
              onRangeChange={handleRangeChange}
            />
          </div>
        </div>

        {/* Row 3: Severity Distribution (4 cols) & Top Offenses (4 cols) & Recent Incidents (4 cols) */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-4">
            <SeverityDistribution data={severityDist} loading={loading} />
          </div>
          <div className="lg:col-span-4">
            <TopOffenses data={topOffenses} loading={loading} />
          </div>
          <div className="lg:col-span-4">
            <RecentIncidents incidents={recentIncidents} loading={loading} />
          </div>
        </div>

        {/* Row 4: Log Timeline Stream (Full Width) */}
        <div className="w-full">
          <LogTimeline logs={logTimeline} loading={loading} />
        </div>
      </main>

      {/* Quantum Simulator Trigger Modal */}
      <SimulatorModal
        isOpen={simModalOpen}
        onClose={() => setSimModalOpen(false)}
        onRunSuccess={loadData}
      />
    </div>
  );
}
